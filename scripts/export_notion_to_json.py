# export_notion_to_json.py
import os, json, requests, datetime

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DB_ID")
NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

def get_database_rows(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    results = []
    cursor = None
    while True:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return results

def prop_text(p):
    if "title" in p:
        return "".join([x.get("plain_text","") for x in p["title"]]).strip()
    if "rich_text" in p:
        return "".join([x.get("plain_text","") for x in p["rich_text"]]).strip()
    return ""

def prop_select(p):
    v = p.get("select") or {}
    return v.get("name")

def prop_multi(p):
    return [x.get("name") for x in p.get("multi_select", [])]

def prop_date(p):
    d = p.get("date") or {}
    return (d.get("start") or "").split("T")[0]  # YYYY-MM-DD

def prop_url(p):
    return p.get("url")

def map_row(row):
    props = row.get("properties", {})
    return {
        "doc_id": prop_text(props.get("DocId", {})) or row.get("id"),
        "title": prop_text(props.get("Title", {})) or "Sin título",
        "version": prop_text(props.get("Version", {})) or "v1.0",
        "area": prop_select(props.get("Area", {})) or "Sin área",
        "type": prop_select(props.get("Type", {})) or "Documento",
        "owner": prop_text(props.get("Owner", {})) or "",
        "tags": prop_multi(props.get("Tags", {})),
        "confidentiality": prop_select(props.get("Confidentiality", {})) or "Interno",
        "last_updated": prop_date(props.get("LastUpdated", {})) or "",
        "drive_link": prop_url(props.get("DriveLink", {})) or "",
        "notion_page_url": row.get("url"),
        "summary": prop_text(props.get("Summary", {})) or ""
    }

def main():
    rows = get_database_rows(DATABASE_ID)
    docs = [map_row(r) for r in rows if r.get("object") == "page"]
    out = {
        "schema_version": "1.0",
        "exported_at": datetime.datetime.now().astimezone().isoformat(),
        "source": f"Notion DB {DATABASE_ID}",
        "documents": docs
    }
    fname = f"Notion_TechDocs_Index_{datetime.date.today().isoformat()}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Exported {len(docs)} docs -> {fname}")

if __name__ == "__main__":
    main()
