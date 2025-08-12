from __future__ import annotations
import csv
import json
import os
from typing import List, Any

import gspread
from google.oauth2.service_account import Credentials


def write_reports(results: list, out_dir: str) -> None:
    # CSV
    csv_path = os.path.join(out_dir, "results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["student_id", "gist_url", "total", "q1", "q2", "q3", "q4", "q5", "notes"])
        for r in results:
            w.writerow([
                r.get("student_id"), r.get("gist_url"), r.get("total", 0),
                r.get("q1", 0), r.get("q2", 0), r.get("q3", 0), r.get("q4", 0), r.get("q5", 0),
                r.get("notes", "")
            ])

    # JSON
    json_path = os.path.join(out_dir, "results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def push_results_to_google_sheets(rows: List[List[Any]]) -> bool:
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not (sa_json and sheet_id):
        return False

    info = json.loads(sa_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    ws = sh.sheet1
    ws.append_rows(rows, value_input_option="USER_ENTERED")
    return True
