import sqlite3
import os
from datetime import datetime

DB_PATH = "data/scraper.db"

def get_conn():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword     TEXT NOT NULL,
            pages       INTEGER DEFAULT 1,
            total_found INTEGER DEFAULT 0,
            started_at  TEXT,
            finished_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id       INTEGER NOT NULL,
            keyword          TEXT,
            page             INTEGER,
            listing_type     TEXT,
            asin             TEXT,
            title            TEXT,
            category         TEXT,
            price            TEXT,
            rating           TEXT,
            reviews          TEXT,
            image_url        TEXT,
            product_url      TEXT,
            seller_name      TEXT,
            seller_email     TEXT,
            seller_phone     TEXT,
            seller_country   TEXT,
            seller_type      TEXT,
            total_products   TEXT,
            suggested_service TEXT,
            seller_page_url  TEXT,
            scraped_at       TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    conn.commit()
    conn.close()
    # Run migration on every startup -- safe to re-run, skips clean sessions
    migrate_combined_sessions()


def migrate_combined_sessions():
    """
    Finds any session whose keyword contains a comma and splits it into
    individual sessions, one per unique keyword found in that session's
    results. Safe to re-run -- skips sessions that are already clean.
    """
    conn = get_conn()
    c    = conn.cursor()

    combined = c.execute(
        "SELECT * FROM sessions WHERE keyword LIKE '%,%'"
    ).fetchall()

    if not combined:
        conn.close()
        return

    print(f"[DB MIGRATION] Found {len(combined)} combined session(s) to split...")

    for session in combined:
        old_id   = session["id"]
        pages    = session["pages"]
        started  = session["started_at"]
        finished = session["finished_at"]

        # Get all results belonging to this combined session
        results = c.execute(
            "SELECT * FROM results WHERE session_id=?", (old_id,)
        ).fetchall()

        # Group results by their own keyword column
        grouped = {}
        for row in results:
            kw = (row["keyword"] or "").strip()
            if not kw:
                # Fallback: try to match to one of the sub-keywords
                kw = "__unknown__"
            if kw not in grouped:
                grouped[kw] = []
            grouped[kw].append(row)

        print(f"[DB MIGRATION] Session {old_id} '{session['keyword']}' has {len(grouped)} keyword group(s): {list(grouped.keys())}")

        if len(grouped) == 1:
            # Only one unique keyword -- just rename the session
            only_kw = list(grouped.keys())[0]
            if only_kw != "__unknown__":
                c.execute(
                    "UPDATE sessions SET keyword=? WHERE id=?",
                    (only_kw, old_id)
                )
                print(f"[DB MIGRATION] Session {old_id} renamed to '{only_kw}'")
            conn.commit()
            continue

        # Multiple keywords -- create one new session per keyword group
        for kw, kw_results in grouped.items():
            if kw == "__unknown__":
                kw = session["keyword"].split(",")[0].strip()

            c.execute(
                "INSERT INTO sessions (keyword, pages, total_found, started_at, finished_at) VALUES (?,?,?,?,?)",
                (kw, pages, len(kw_results), started, finished)
            )
            new_sid = c.lastrowid

            for row in kw_results:
                c.execute(
                    "UPDATE results SET session_id=? WHERE id=?",
                    (new_sid, row["id"])
                )

            print(f"[DB MIGRATION] Created session {new_sid} for '{kw}' with {len(kw_results)} results")

        # Remove the old combined session (results already moved)
        c.execute("DELETE FROM sessions WHERE id=?", (old_id,))
        print(f"[DB MIGRATION] Deleted combined session {old_id}")

    conn.commit()
    conn.close()
    print("[DB MIGRATION] Complete.")


def create_session(keyword, pages):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO sessions (keyword, pages, started_at) VALUES (?, ?, ?)",
        (keyword, pages, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

def finish_session(session_id, total_found):
    conn = get_conn()
    conn.execute(
        "UPDATE sessions SET total_found=?, finished_at=? WHERE id=?",
        (total_found, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), session_id)
    )
    conn.commit()
    conn.close()

def save_result(session_id, row):
    conn = get_conn()
    conn.execute("""
        INSERT INTO results (
            session_id, keyword, page, listing_type, asin, title, category,
            price, rating, reviews, image_url, product_url, seller_name,
            seller_email, seller_phone, seller_country, seller_type,
            total_products, suggested_service, seller_page_url, scraped_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        session_id,
        row.get("keyword",""), row.get("page",0), row.get("listing_type",""),
        row.get("asin",""), row.get("title",""), row.get("category",""),
        row.get("price",""), row.get("rating",""), row.get("reviews",""),
        row.get("image_url",""), row.get("product_url",""), row.get("seller_name",""),
        row.get("seller_email",""), row.get("seller_phone",""), row.get("seller_country",""),
        row.get("seller_type",""), row.get("total_products",""), row.get("suggested_service",""),
        row.get("seller_page_url",""), row.get("scraped_at","")
    ))
    conn.commit()
    conn.close()

def get_all_sessions():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM sessions ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_session_results(session_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM results WHERE session_id=? ORDER BY id ASC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_session(session_id):
    conn = get_conn()
    conn.execute("DELETE FROM results WHERE session_id=?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
