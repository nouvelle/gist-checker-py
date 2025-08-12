from __future__ import annotations
import csv
import json
import os
from typing import List, Any, Optional

import gspread
from google.oauth2.service_account import Credentials


def write_reports(results: list, out_dir: str) -> None:
    """結果を CSV / JSON に書き出す。CSV はシンプルに『何問中いくつパスか』中心。"""
    # CSV
    csv_path = os.path.join(out_dir, "results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "student_id", "gist_url",
            "passed", "total_tests", "failed", "errors", "skipped", "pass_rate",
            "notes",
        ])
        for r in results:
            total = r.get("total_tests", 0)
            passed = r.get("passed", 0)
            failed = r.get("failed", 0)
            errors = r.get("errors", 0)
            skipped = r.get("skipped", 0)
            rate = f"{(passed/total*100):.0f}%" if total else "0%"
            w.writerow([
                r.get("student_id"), r.get("gist_url"),
                passed, total, failed, errors, skipped, rate,
                r.get("notes", ""),
            ])

    # JSON（各テストの詳細も入れる）
    json_path = os.path.join(out_dir, "results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def _get_gspread_client():
    """Secrets からクライアントと書き込み先シートIDを取得。未設定なら (None, None)。"""
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sa_json or not sheet_id:
        return None, None

    info = json.loads(sa_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc, sheet_id


def push_results_to_google_sheets(rows: List[List[Any]], worksheet_name: Optional[str] = None) -> bool:
    """採点結果を Google Sheets に追記。書き込み先タブは 引数 > 環境変数 RESULT_TAB > 1枚目。"""
    gc, sheet_id = _get_gspread_client()
    if not (gc and sheet_id):
        return False

    sh = gc.open_by_key(sheet_id)

    # 書き込みタブの決定
    target_tab = worksheet_name or os.environ.get("RESULT_TAB")
    try:
        ws = sh.worksheet(target_tab) if target_tab else sh.sheet1
    except Exception:
        ws = sh.sheet1

    ws.append_rows(rows, value_input_option="USER_ENTERED")
    return True
