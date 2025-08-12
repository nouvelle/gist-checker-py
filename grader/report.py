from __future__ import annotations
import csv
import json
import os
from typing import List, Any, Optional

import gspread
from google.oauth2.service_account import Credentials

def write_reports(results: list, out_dir: str) -> None:
    """結果を CSV / JSON に書き出す。CSV はサマリとケース明細をそれぞれ出力。"""
    os.makedirs(out_dir, exist_ok=True)

    # --- サマリ CSV ---
    csv_path = os.path.join(out_dir, "results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "student_id", "gist_url",
            "passed", "total_tests", "failed", "errors", "skipped", "pass_rate",
            "notes",
        ])
        for r in results:
            total  = int(r.get("total_tests", 0) or 0)
            passed = int(r.get("passed", 0) or 0)
            failed = int(r.get("failed", 0) or 0)
            errors = int(r.get("errors", 0) or 0)
            skipped = int(r.get("skipped", 0) or 0)
            rate = f"{(passed/total*100):.0f}%" if total else "0%"
            w.writerow([
                r.get("student_id"), r.get("gist_url"),
                passed, total, failed, errors, skipped, rate,
                r.get("notes", ""),
            ])

    # --- ケース明細 CSV ---
    cases_csv = os.path.join(out_dir, "results_cases.csv")
    with open(cases_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["student_id", "gist_url", "test_name", "outcome", "time_sec"])
        for r in results:
            sid = r.get("student_id")
            url = r.get("gist_url")
            for tc in r.get("tests", []) or []:
                w.writerow([sid, url, tc.get("name", ""), tc.get("outcome", ""), tc.get("time", 0)])

    # --- JSON（詳細そのまま） ---
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
    """採点結果サマリを Google Sheets に追記。書き込み先タブは 引数 > 環境変数 RESULT_TAB > 1枚目。"""
    gc, sheet_id = _get_gspread_client()
    if not (gc and sheet_id):
        return False

    sh = gc.open_by_key(sheet_id)

    target_tab = worksheet_name or os.environ.get("RESULT_TAB")
    try:
        ws = sh.worksheet(target_tab) if target_tab else sh.sheet1
    except Exception:
        ws = sh.sheet1

    ws.append_rows(rows, value_input_option="USER_ENTERED")
    return True

def push_testcases_to_google_sheets(rows: List[List[Any]], worksheet_name: Optional[str] = None) -> bool:
    """各テストケース明細を Google Sheets に追記。書き込み先タブは 引数 > 環境変数 CASES_TAB > 'results_cases'。"""
    if not rows:
        return True
    gc, sheet_id = _get_gspread_client()
    if not (gc and sheet_id):
        return False

    sh = gc.open_by_key(sheet_id)

    target_tab = worksheet_name or os.environ.get("CASES_TAB") or "results_cases"
    try:
        ws = sh.worksheet(target_tab)
    except Exception:
        # 無ければ作る（ヘッダ行も入れる）
        try:
            ws = sh.add_worksheet(title=target_tab, rows=1000, cols=10)
            ws.append_row(["timestamp", "student_id", "gist_url", "test_name", "outcome", "time_sec"], value_input_option="USER_ENTERED")
        except Exception:
            # sheet 追加に失敗した場合は最初のシートに追記
            ws = sh.sheet1

    ws.append_rows(rows, value_input_option="USER_ENTERED")
    return True
