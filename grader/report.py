from __future__ import annotations
import csv
import json
import os
from typing import List, Any, Optional

import gspread
from google.oauth2.service_account import Credentials

def write_reports(results: list, out_dir: str) -> None:
    """結果を CSV / JSON に書き出す"""
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
        # 指定タブが存在しない場合はシート1枚目にフォールバック
        ws = sh.sheet1

    ws.append_rows(rows, value_input_option="USER_ENTERED")
    return True
