import asyncio
import json
import threading
import queue
import os
import csv
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, send_file
from scraper import run_scraper, save_csv, save_bulk_mailer_csv
from database import init_db, create_session, finish_session, save_result, \
                     get_all_sessions, get_session_results, delete_session

app = Flask(__name__)
init_db()

scrape_results  = []
current_session_id = None
scrape_status   = {"running": False, "keyword": "", "pages": 1}
progress_queue_sync = queue.Queue()

service_rules = {
    "reviews_lt": 50,         "reviews_lt_service": "Listing Images",
    "rating_lt": 4.0,         "rating_lt_service": "Amazon SEO",
    "products_gt": 50,        "products_gt_service": "PPC",
    "good_service": "A+ Content", "default_service": "Amazon SEO"
}


def run_async_scraper(keywords_raw, pages):
    global scrape_results, current_session_id
    scrape_results = []

    # One DB session per keyword — tracked here
    keyword_sessions = {}   # keyword -> session_id
    keyword_counts   = {}   # keyword -> result count

    async def _run():
        async_q = asyncio.Queue()
        task    = asyncio.create_task(run_scraper(keywords_raw, pages, async_q))

        while True:
            try:
                msg = await asyncio.wait_for(async_q.get(), timeout=0.1)
                progress_queue_sync.put(msg)

                if msg["type"] == "keyword":
                    # New keyword starting — create its own session
                    kw = msg["keyword"]
                    sid = create_session(kw, pages)
                    keyword_sessions[kw] = sid
                    keyword_counts[kw]   = 0
                    current_session_id   = sid

                elif msg["type"] == "result":
                    row = msg["row"]
                    kw  = row.get("keyword", "")
                    sid = keyword_sessions.get(kw, current_session_id)
                    scrape_results.append(row)
                    save_result(sid, row)
                    keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

                elif msg["type"] == "keyword_done":
                    kw  = msg["keyword"]
                    sid = keyword_sessions.get(kw)
                    if sid:
                        finish_session(sid, keyword_counts.get(kw, 0))

                elif msg["type"] == "done":
                    break

            except asyncio.TimeoutError:
                if task.done():
                    break

        await task

    asyncio.run(_run())
    scrape_status["running"] = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/save_rules", methods=["POST"])
def save_rules():
    global service_rules
    data = request.json
    if data:
        service_rules.update(data)
        import scraper as sc
        sc.RULES = service_rules
    return jsonify({"success": True})


@app.route("/start", methods=["POST"])
def start_scrape():
    global scrape_results
    if scrape_status["running"]:
        return jsonify({"error": "Scraper is already running"}), 400

    data    = request.json
    keyword = data.get("keyword", "").strip()
    pages   = int(data.get("pages", 1))

    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400

    scrape_results = []
    scrape_status["running"] = True
    scrape_status["keyword"] = keyword
    scrape_status["pages"]   = pages

    while not progress_queue_sync.empty():
        try: progress_queue_sync.get_nowait()
        except: break

    thread = threading.Thread(
        target=run_async_scraper,
        args=(keyword, pages),
        daemon=True
    )
    thread.start()
    return jsonify({"success": True, "message": f"Started: {keyword}"})


@app.route("/stream")
def stream():
    def generate():
        while True:
            try:
                msg = progress_queue_sync.get(timeout=60)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg["type"] == "done":
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/results")
def get_results():
    return jsonify(scrape_results)


@app.route("/export")
def export_csv():
    keyword  = scrape_status.get("keyword", "results")
    filename = save_csv(scrape_results, keyword)
    if not filename:
        return jsonify({"error": "No results to export"}), 400
    return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))


@app.route("/export_bulkmailer")
def export_bulk_mailer():
    keyword  = scrape_status.get("keyword", "results")
    filename = save_bulk_mailer_csv(scrape_results, keyword)
    if not filename:
        return jsonify({"error": "No results with emails to export"}), 400
    return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))


# ── HISTORY ENDPOINTS ──

@app.route("/history/sessions")
def history_sessions():
    return jsonify(get_all_sessions())


@app.route("/history/results/<int:session_id>")
def history_results(session_id):
    return jsonify(get_session_results(session_id))


@app.route("/history/export/<int:session_id>")
def history_export(session_id):
    rows = get_session_results(session_id)
    if not rows:
        return jsonify({"error": "No data"}), 400
    keyword  = rows[0].get("keyword", "session")
    safe_kw  = re.sub(r'[^a-zA-Z0-9_]', '_', keyword)
    os.makedirs("exports", exist_ok=True)
    filename = f"exports/history_{safe_kw}_{session_id}.csv"
    fields   = [
        "keyword","page","listing_type","asin","title","price","rating",
        "reviews","product_url","seller_name","seller_email","seller_phone",
        "seller_country","seller_type","total_products","suggested_service",
        "seller_page_url","scraped_at"
    ]
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))


@app.route("/history/export_mailer/<int:session_id>")
def history_export_mailer(session_id):
    rows     = get_session_results(session_id)
    keyword  = rows[0].get("keyword", "session") if rows else "session"
    safe_kw  = re.sub(r'[^a-zA-Z0-9_]', '_', keyword)
    os.makedirs("exports", exist_ok=True)
    filename = f"exports/history_{safe_kw}_{session_id}_BulkMailer.csv"
    seen     = set()
    mailer_rows = []
    for r in rows:
        email = (r.get("seller_email") or "").strip()
        if not email or email in seen:
            continue
        seen.add(email)
        mailer_rows.append({
            "Seller Name": r.get("seller_name",""),
            "Email":       email,
            "Store Name":  r.get("seller_name",""),
            "Service":     r.get("suggested_service","Amazon SEO"),
            "Country":     r.get("seller_country",""),
        })
    if not mailer_rows:
        return jsonify({"error": "No emails found"}), 400
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["Seller Name","Email","Store Name","Service","Country"])
        w.writeheader()
        w.writerows(mailer_rows)
    return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))


@app.route("/history/delete/<int:session_id>", methods=["DELETE"])
def history_delete(session_id):
    delete_session(session_id)
    return jsonify({"success": True})


@app.route("/status")
def status():
    return jsonify({
        "running":      scrape_status["running"],
        "keyword":      scrape_status["keyword"],
        "result_count": len(scrape_results)
    })


if __name__ == "__main__":
    os.makedirs("exports", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    print("\n" + "="*50)
    print("  Advertpreneur - Amazon.de Scraper")
    print("  Open your browser: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=False, port=5000, threaded=True)
