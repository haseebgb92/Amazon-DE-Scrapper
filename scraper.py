import asyncio
import re
import csv
import os
from datetime import datetime
from playwright.async_api import async_playwright

ZIP_CODE = "10115"
BASE_URL  = "https://www.amazon.de"

def clean(text):
    return re.sub(r'\s+', ' ', text or "").strip()

# ------------------------------------------------------------------
# ZIP CODE
# Handles three Amazon ZIP dialogs:
#   1. Standard GLUXZip popover (Apply button)
#   2. "You are now shopping for delivery to" confirmation modal (Continue button)
#   3. "Dispatch to Pakistan" tooltip (Change Address button)
# ------------------------------------------------------------------
async def set_zip_code(page, progress_queue):
    await progress_queue.put({"type": "status", "message": "Setting delivery ZIP to 10115 (Berlin)..."})
    try:
        # Step 0: Dismiss "Dispatch to Pakistan" tooltip if present
        for dismiss_sel in [
            "input[data-action='GLUXDismissAction']",
            "button:has-text('Change Address')",
            "a:has-text('Change Address')",
        ]:
            try:
                el = await page.query_selector(dismiss_sel)
                if el:
                    await el.click()
                    await asyncio.sleep(1.5)
                    break
            except:
                continue

        # Step 1: Click the location widget to open ZIP popover
        loc_btn = await page.wait_for_selector(
            "#nav-global-location-popover-link, #glow-ingress-line2, #glow-ingress-block",
            timeout=10000
        )
        await loc_btn.click()
        await asyncio.sleep(2)

        # Step 2: Find ZIP input
        zip_input = None
        for sel in [
            "input#GLUXZipUpdateInput",
            "input[data-glowid='GLUXZipUpdateInput']",
            "input[placeholder*='ZIP']",
            "input[placeholder*='Postleitzahl']",
        ]:
            try:
                el = await page.wait_for_selector(sel, timeout=3000)
                if el:
                    zip_input = el
                    break
            except:
                continue

        if not zip_input:
            await progress_queue.put({"type": "status", "message": "ZIP input not found — skipping"})
            return False

        # Step 3: Clear and type ZIP
        await zip_input.click()
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Delete")
        await zip_input.type(ZIP_CODE, delay=100)
        await asyncio.sleep(0.5)

        # Step 4: Click Apply/Update button
        applied = False
        for btn_sel in [
            "input#GLUXZipUpdate",
            "[aria-labelledby='GLUXZipUpdate-announce']",
            "span#GLUXZipUpdate input",
            "input.a-button-input[type='submit']",
        ]:
            try:
                btn = await page.query_selector(btn_sel)
                if btn:
                    await btn.click()
                    applied = True
                    break
            except:
                continue

        if not applied:
            await page.keyboard.press("Enter")

        await asyncio.sleep(2.5)

        # Step 5: Handle "You are now shopping for delivery to: 10115" modal
        # This is the Continue button in the confirmation popup shown in the screenshot
        for continue_sel in [
            "input[data-action='GLUXConfirmAction']",
            "button[data-action='GLUXConfirmAction']",
            "#GLUXConfirmClose",
            "input[aria-labelledby='GLUXConfirmClose-announce']",
            "button.a-button-text:has-text('Continue')",
            "input[value='Continue']",
            "a:has-text('Continue')",
        ]:
            try:
                btn = await page.query_selector(continue_sel)
                if btn:
                    await btn.click()
                    await asyncio.sleep(1.5)
                    break
            except:
                continue

        # Step 6: Handle any remaining modal with a Continue/Done button
        # Catches the exact modal in the screenshot: "You're now shopping for delivery to: 10115"
        try:
            modal_continue = await page.query_selector(
                ".a-popover-wrapper button, "
                ".a-modal-scroller button, "
                "[data-action*='Confirm'] input, "
                ".a-button-primary input.a-button-input"
            )
            if modal_continue:
                await modal_continue.click()
                await asyncio.sleep(1.5)
        except:
            pass

        await asyncio.sleep(2)
        await progress_queue.put({"type": "status", "message": "ZIP 10115 set successfully"})
        return True

    except Exception as e:
        await progress_queue.put({"type": "status", "message": f"ZIP skipped: {str(e)[:80]}"})
        return False


# ------------------------------------------------------------------
# SEARCH
# ZIP is set once at the start. Subsequent keyword searches reuse
# the same browser session so ZIP stays set.
# ------------------------------------------------------------------
async def do_search(page, keyword, progress_queue, set_zip=False):
    if set_zip:
        await progress_queue.put({"type": "status", "message": "Opening Amazon.de..."})
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        await set_zip_code(page, progress_queue)

    url = f"{BASE_URL}/s?k={keyword.replace(' ', '+')}&language=en_GB"
    await progress_queue.put({"type": "status", "message": f"Searching: {keyword}"})
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(4)
    return url


# ------------------------------------------------------------------
# COLLECT PRODUCTS FROM SEARCH PAGE
# ------------------------------------------------------------------
async def collect_products(page, pages_count, start_url, progress_queue):
    all_products = []
    current_url  = start_url

    for page_num in range(1, pages_count + 1):
        await progress_queue.put({"type": "status", "message": f"Collecting products — page {page_num}/{pages_count}..."})

        if page_num > 1:
            await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(4)

        # Scroll to load all lazy items
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await asyncio.sleep(1)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        # Try multiple known Amazon search result selectors
        items = []
        for container_sel in [
            "[data-component-type='s-search-result']",
            "div[data-asin]:not([data-asin=''])",
            ".s-result-item[data-asin]",
            ".sg-col-inner .s-widget-container",
        ]:
            items = await page.query_selector_all(container_sel)
            if items:
                break

        await progress_queue.put({"type": "status", "message": f"Found {len(items)} raw items on page {page_num}"})

        page_count = 0
        for item in items:
            try:
                asin = await item.get_attribute("data-asin")
                if not asin or len(asin) < 5:
                    continue

                # Sponsored detection
                is_sponsored = False
                item_html = await item.inner_html()
                if any(kw in item_html for kw in [
                    "puis-sponsored", "s-sponsored-label",
                    "Gesponsert", "Sponsored", "sp-atf"
                ]):
                    is_sponsored = True

                # Title — try several selectors
                title = ""
                for t_sel in [
                    "h2 a span",
                    "h2 span.a-text-normal",
                    "h2 span",
                    ".a-size-base-plus.a-color-base.a-text-normal",
                    ".a-size-medium.a-color-base.a-text-normal",
                ]:
                    t_el = await item.query_selector(t_sel)
                    if t_el:
                        title = clean(await t_el.inner_text())
                        if title:
                            break

                # Product URL
                href = ""
                for link_sel in ["h2 a", "a.a-link-normal[href*='/dp/']", "a[href*='/dp/']"]:
                    link_el = await item.query_selector(link_sel)
                    if link_el:
                        href = await link_el.get_attribute("href") or ""
                        if "/dp/" in href:
                            break

                if not href or not asin:
                    continue

                product_url = (BASE_URL + href) if href.startswith("/") else href
                # Clean URL — remove query params except dp part
                dp_match = re.search(r'(/dp/[A-Z0-9]+)', product_url)
                if dp_match:
                    product_url = BASE_URL + dp_match.group(1)

                # Price
                price = ""
                for p_sel in [
                    ".a-price .a-offscreen",
                    ".a-price-whole",
                    "span.a-color-price",
                ]:
                    p_el = await item.query_selector(p_sel)
                    if p_el:
                        price = clean(await p_el.inner_text())
                        if price:
                            break

                # Rating
                rating = ""
                r_el = await item.query_selector("span.a-icon-alt, i.a-icon-star span")
                if r_el:
                    rt = clean(await r_el.inner_text())
                    m_r = re.search(r"[\d,.]+", rt)
                    if m_r:
                        rating = m_r.group(0).replace(",", ".")

                # Review count
                reviews = ""
                for rv_sel in [
                    "span[aria-label*='stars'] + span",
                    "a .a-size-base.s-underline-text",
                    ".a-row .a-link-normal .a-size-base",
                ]:
                    rv_el = await item.query_selector(rv_sel)
                    if rv_el:
                        rv_t = clean(await rv_el.inner_text())
                        rv_t = rv_t.replace(".", "").replace(",", "")
                        m_rv = re.search(r"\d+", rv_t)
                        if m_rv:
                            reviews = m_rv.group(0)
                            break

                # Main image URL
                image_url = ""
                img_el = await item.query_selector("img.s-image, .s-product-image-container img")
                if img_el:
                    image_url = await img_el.get_attribute("src") or ""

                all_products.append({
                    "asin": asin,
                    "title": title,
                    "url": product_url,
                    "sponsored": is_sponsored,
                    "page": page_num,
                    "price": price,
                    "rating": rating,
                    "reviews": reviews,
                    "image_url": image_url,
                })
                page_count += 1

            except Exception as e:
                continue

        await progress_queue.put({"type": "status", "message": f"Page {page_num}: {page_count} valid products collected"})

        # Next page button
        try:
            next_el = await page.query_selector(
                "a.s-pagination-next:not(.s-pagination-disabled), "
                "li.a-last a"
            )
            if next_el:
                href = await next_el.get_attribute("href") or ""
                if href:
                    current_url = (BASE_URL + href) if href.startswith("/") else href
                else:
                    break
            else:
                break
        except:
            break

    return all_products


# ------------------------------------------------------------------
# GET SELLER DETAILS
# ------------------------------------------------------------------
async def get_seller_details(page, product_url, progress_queue):
    result = {
        "seller_name": "", "seller_email": "", "seller_phone": "",
        "seller_country": "", "seller_type": "",
        "total_products": "", "sold_by_amazon": False, "seller_page_url": ""
    }

    try:
        await page.goto(product_url, wait_until="domcontentloaded", timeout=35000)
        await asyncio.sleep(3)

        # Category breadcrumb
        category = ""
        for bc_sel in [
            "#wayfinding-breadcrumbs_feature_div ul li:last-child span",
            "#wayfinding-breadcrumbs_feature_div .a-link-normal",
            ".a-breadcrumb li:last-child span",
            "#nav-subnav .nav-a-content",
        ]:
            bc_el = await page.query_selector(bc_sel)
            if bc_el:
                category = clean(await bc_el.inner_text())
                if category and len(category) < 80:
                    break
        result["category"] = category

        # Find seller link
        seller_href = ""
        seller_name_from_link = ""
        for sel in [
            "#sellerProfileTriggerId",
            "#merchant-info a",
            "a[href*='/sp?seller=']",
            "a[href*='seller=']",
            "#tabular-buybox a[href*='seller=']",
            ".tabular-buybox-text a",
            ".offer-display-feature-text a",
        ]:
            el = await page.query_selector(sel)
            if el:
                href = await el.get_attribute("href") or ""
                if "seller=" in href:
                    seller_href = href
                    seller_name_from_link = clean(await el.inner_text())
                    break

        # Check if Amazon is the seller
        if seller_name_from_link.lower() in ["amazon", "amazon.de", "amazon.com"]:
            result["sold_by_amazon"] = True
            result["seller_name"] = seller_name_from_link
            return result

        if not seller_href:
            # Try to grab name from page at minimum
            for sel in ["#sellerProfileTriggerId", "#merchant-info", "#bylineInfo"]:
                el = await page.query_selector(sel)
                if el:
                    result["seller_name"] = clean(await el.inner_text())
                    break
            return result

        seller_page_url = (BASE_URL + seller_href) if seller_href.startswith("/") else seller_href
        result["seller_page_url"] = seller_page_url

        # Go to seller profile
        await page.goto(seller_page_url, wait_until="domcontentloaded", timeout=35000)
        await asyncio.sleep(3)

        html = await page.content()

        # --- Parse seller info from HTML ---
        def extract(patterns, source):
            for pat in patterns:
                m = re.search(pat, source, re.IGNORECASE | re.DOTALL)
                if m:
                    val = clean(re.sub(r'<[^>]+>', '', m.group(1)))
                    if val:
                        return val
            return ""

        # Seller name: always use the "Sold by" text from the product page.
        # That is the exact name Amazon shows to buyers.
        # Only fall back to the profile page Business Name if the link had no text.
        result["seller_name"] = seller_name_from_link or extract([
            r'Business Name[:\s]*</span>\s*<span[^>]*>([^<]+)<',
            r'Business Name[:\s]*</b>\s*([^<\n]+)',
            r'Firmenname[:\s]*</span>\s*<span[^>]*>([^<]+)<',
        ], html)

        # Last resort: h1 on the storefront page
        if not result["seller_name"]:
            for sel in [".a-size-large.a-text-bold", "h1.a-size-large", "h1"]:
                el = await page.query_selector(sel)
                if el:
                    t = clean(await el.inner_text())
                    if t and len(t) < 120:
                        result["seller_name"] = t
                        break

        # Email — first try structured, then regex scan
        email_val = extract([
            r'E-?mail[:\s]*</span>\s*<span[^>]*>([^<]+)<',
            r'E-?mail[:\s]*</b>\s*([^<\n]+)',
        ], html)
        if not email_val:
            emails_found = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', html)
            for e in emails_found:
                if "amazon" not in e.lower() and "example" not in e.lower():
                    email_val = e
                    break
        result["seller_email"] = email_val

        result["seller_phone"] = extract([
            r'Phone number[:\s]*</span>\s*<span[^>]*>([^<]+)<',
            r'Phone number[:\s]*</b>\s*([^<\n]+)',
            r'Telefon[:\s]*</span>\s*<span[^>]*>([^<]+)<',
        ], html)

        result["seller_type"] = extract([
            r'Business Type[:\s]*</span>\s*<span[^>]*>([^<]+)<',
            r'Business Type[:\s]*</b>\s*([^<\n]+)',
            r'Unternehmensart[:\s]*</span>\s*<span[^>]*>([^<]+)<',
        ], html)

        # Country — multiple strategies to extract 2-letter country code
        country = ""

        # Strategy 1: look for country code in address block
        for pat in [
            r'Business Address[^<]*</span>(.*?)</li>',
            r'Business Address[^<]*</b>(.*?)</p>',
            r'Gesch.ftsadresse[^<]*</span>(.*?)</li>',
            r'Business Address(.*?)</ul>',
        ]:
            m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
            if m:
                addr_raw = clean(re.sub(r'<[^>]+>', ' ', m.group(1)))
                # Last word that is exactly 2 uppercase letters
                cm = re.search(r'\b([A-Z]{2})\b\s*$', addr_raw.strip())
                if cm:
                    country = cm.group(1)
                    break
                # Also try finding any 2-letter code in the block
                codes = re.findall(r'\b([A-Z]{2})\b', addr_raw)
                known = {"DE","CN","US","GB","UK","FR","IT","ES","NL","PL","CZ",
                         "AT","CH","HK","JP","KR","VN","TH","IN","CA","AU","TR",
                         "BE","SE","DK","NO","FI","PT","HU","RO","SG","TW","MY"}
                for code in reversed(codes):
                    if code in known:
                        country = code
                        break
                if country:
                    break

        # Strategy 2: scan full seller page text for country patterns
        if not country:
            # Look for lines like "CN" or "DE" standing alone near address section
            snippets = re.findall(
                r'(?:country|land|Country)[^<]{0,30}<[^>]+>\s*([A-Z]{2})\s*<',
                html, re.IGNORECASE
            )
            if snippets:
                country = snippets[0]

        # Strategy 3: scan plain text of page for known country codes near address
        if not country:
            known = {"DE","CN","US","GB","FR","IT","ES","NL","PL","CZ",
                     "AT","CH","HK","JP","KR","VN","TH","IN","CA","AU","TR",
                     "BE","SE","DK","NO","FI","PT","HU","RO","SG","TW","MY"}
            # Get visible text around address section
            addr_section = re.search(
                r'Business Address.{0,500}',
                re.sub(r'<[^>]+>', ' ', html), re.DOTALL | re.IGNORECASE
            )
            if addr_section:
                words = addr_section.group(0).split()
                for w in reversed(words):
                    w = w.strip(".,;:()")
                    if w in known:
                        country = w
                        break

        result["seller_country"] = country

        # --- See all products -> total count ---
        see_all_url = None
        # Try link with marketplaceID or me= param
        for sel in ["a[href*='marketplaceID']", "a[href*='me=']"]:
            el = await page.query_selector(sel)
            if el:
                h = await el.get_attribute("href") or ""
                if h:
                    see_all_url = (BASE_URL + h) if h.startswith("/") else h
                    break

        # Try by link text
        if not see_all_url:
            links = await page.query_selector_all("a")
            for lnk in links:
                try:
                    txt = clean(await lnk.inner_text())
                    if "all product" in txt.lower() or "alle produkte" in txt.lower():
                        h = await lnk.get_attribute("href") or ""
                        if h:
                            see_all_url = (BASE_URL + h) if h.startswith("/") else h
                            break
                except:
                    continue

        if see_all_url:
            await page.goto(see_all_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            for count_sel in [
                "[data-component-type='s-result-count']",
                "span.a-color-base.a-text-bold",
                "h1.a-size-base",
                ".a-section .a-color-base",
            ]:
                el = await page.query_selector(count_sel)
                if el:
                    t = clean(await el.inner_text())
                    nums = re.findall(r'\d+', t.replace(",", "").replace(".", ""))
                    if nums:
                        result["total_products"] = nums[-1]
                        break

    except Exception as e:
        await progress_queue.put({"type": "status", "message": f"Seller error: {str(e)[:100]}"})

    return result


# ------------------------------------------------------------------
# SERVICE SUGGESTION LOGIC
# Rules dict -- updated live from the UI Settings tab via /save_rules
# ------------------------------------------------------------------
RULES = {
    "reviews_lt": 50,
    "reviews_lt_service": "Listing Images",
    "rating_lt": 4.0,
    "rating_lt_service": "Amazon SEO",
    "products_gt": 50,
    "products_gt_service": "PPC",
    "good_service": "A+ Content",
    "default_service": "Amazon SEO"
}

def suggest_service(reviews, total_products, rating):
    try:
        rv = int(str(reviews).replace(",", "").replace(".", "")) if reviews else 0
        tp = int(str(total_products).replace(",", "").replace(".", "")) if total_products else 0
        rt = float(str(rating).replace(",", ".")) if rating else 0.0
    except:
        return RULES.get("default_service", "Amazon SEO")

    if rv > 0 and rv < RULES.get("reviews_lt", 50):
        return RULES.get("reviews_lt_service", "Listing Images")
    if rt > 0 and rt < RULES.get("rating_lt", 4.0):
        return RULES.get("rating_lt_service", "Amazon SEO")
    if tp > 0 and tp > RULES.get("products_gt", 50):
        return RULES.get("products_gt_service", "PPC")
    if rv >= RULES.get("reviews_lt", 50) and rt >= RULES.get("rating_lt", 4.0):
        return RULES.get("good_service", "A+ Content")
    return RULES.get("default_service", "Amazon SEO")


# ------------------------------------------------------------------
# MAIN
# Accepts comma-separated keywords. Scrapes each fully before moving
# to the next. ZIP is set once at the start and reused for all.
# ------------------------------------------------------------------
async def run_scraper(keywords_raw, pages, progress_queue):
    # Split comma-separated keywords and clean each
    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
    if not keywords:
        keywords = [keywords_raw.strip()]

    total_keywords = len(keywords)
    all_results    = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        context = await browser.new_context(
            locale="en-GB",
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            "window.chrome = {runtime: {}};"
        )

        page = await context.new_page()

        for kw_idx, keyword in enumerate(keywords):
            await progress_queue.put({
                "type": "keyword",
                "current": kw_idx + 1,
                "total":   total_keywords,
                "keyword": keyword
            })
            await progress_queue.put({
                "type": "status",
                "message": f"Keyword {kw_idx+1}/{total_keywords}: {keyword}"
            })

            # Set ZIP only on first keyword — browser session keeps it for subsequent ones
            search_url   = await do_search(page, keyword, progress_queue, set_zip=(kw_idx == 0))
            all_products = await collect_products(page, pages, search_url, progress_queue)

            await progress_queue.put({
                "type": "status",
                "message": f"[{keyword}] Collected {len(all_products)} products. Opening each product page..."
            })

            for idx, product in enumerate(all_products):
                short = (product["title"][:55] + "...") if len(product["title"]) > 55 else product["title"]
                await progress_queue.put({
                    "type": "progress",
                    "current": idx + 1,
                    "total":   len(all_products),
                    "message": f"[{keyword}] {idx+1}/{len(all_products)}: {short}"
                })

                seller = await get_seller_details(page, product["url"], progress_queue)

                if seller["sold_by_amazon"]:
                    await progress_queue.put({"type": "status", "message": f"Skipped (Amazon): {short}"})
                    continue

                service = suggest_service(
                    product.get("reviews", ""),
                    seller["total_products"],
                    product.get("rating", "")
                )

                row = {
                    "keyword":           keyword,
                    "page":              product["page"],
                    "listing_type":      "Sponsored" if product["sponsored"] else "Organic",
                    "asin":              product["asin"],
                    "title":             product["title"],
                    "category":          seller["category"],
                    "price":             product.get("price", ""),
                    "rating":            product.get("rating", ""),
                    "reviews":           product.get("reviews", ""),
                    "image_url":         product.get("image_url", ""),
                    "product_url":       product["url"],
                    "seller_name":       seller["seller_name"],
                    "seller_email":      seller["seller_email"],
                    "seller_phone":      seller["seller_phone"],
                    "seller_country":    seller["seller_country"],
                    "seller_type":       seller["seller_type"],
                    "total_products":    seller["total_products"],
                    "suggested_service": service,
                    "seller_page_url":   seller["seller_page_url"],
                    "scraped_at":        datetime.now().strftime("%Y-%m-%d %H:%M")
                }

                all_results.append(row)
                await progress_queue.put({"type": "result", "row": row})
                await progress_queue.put({
                    "type": "status",
                    "message": f"Captured: {seller['seller_name'] or 'Unknown'} | {seller['seller_email'] or 'no email'}"
                })
                await asyncio.sleep(2)

            await progress_queue.put({
                "type": "keyword_done",
                "keyword": keyword,
                "count":   len([r for r in all_results if r["keyword"] == keyword])
            })

        await browser.close()

    await progress_queue.put({"type": "done", "total": len(all_results)})
    return all_results


# ------------------------------------------------------------------
# CSV
# ------------------------------------------------------------------
def save_csv(results, keyword):
    """Full data export with all fields."""
    if not results:
        return None
    os.makedirs("exports", exist_ok=True)
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_kw = re.sub(r'[^a-zA-Z0-9_]', '_', keyword)
    fname   = f"exports/{safe_kw}_{ts}.csv"
    fields  = [
        "keyword", "page", "listing_type", "asin", "title", "category",
        "price", "rating", "reviews", "image_url", "product_url",
        "seller_name", "seller_email", "seller_phone",
        "seller_country", "seller_type", "total_products",
        "suggested_service", "seller_page_url", "scraped_at"
    ]
    with open(fname, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    return fname


def save_bulk_mailer_csv(results, keyword):
    """
    Export formatted for the Advertpreneur Gmail Bulk Mailer Google Sheet.
    Columns: Seller Name | Email | Store Name | Service | Country
    Only rows with an email address are included. Deduped by email.
    Country column is used by the GS script to pick the right language template.
    """
    if not results:
        return None
    os.makedirs("exports", exist_ok=True)
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_kw = re.sub(r'[^a-zA-Z0-9_]', '_', keyword)
    fname   = f"exports/{safe_kw}_{ts}_BulkMailer.csv"

    seen_emails = set()
    rows = []
    for r in results:
        email = (r.get("seller_email") or "").strip()
        if not email or email in seen_emails:
            continue
        seen_emails.add(email)
        rows.append({
            "Seller Name": r.get("seller_name", ""),
            "Email":       email,
            "Store Name":  r.get("seller_name", ""),
            "Service":     r.get("suggested_service", "Amazon SEO"),
            "Country":     r.get("seller_country", ""),
        })

    if not rows:
        return None

    fields = ["Seller Name", "Email", "Store Name", "Service", "Country"]
    with open(fname, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return fname
