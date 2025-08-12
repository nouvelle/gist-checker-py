from __future__ import annotations
import csv
import json
import os
from typing import List, Any, Optional, Sequence, Dict, Set

import gspread
from google.oauth2.service_account import Credentials


BASE_HEADERS = [
    "time", "student_id", "gist_url",
    "passed", "total_tests", "failed", "errors", "skipped", "pass_rate",
    "notes",
]


def write_reports(results: list, out_dir: str) -> None:
    """結果を CSV / JSON に書き出す。CSV はサマリ＋（おまけで）横展開版も保存。"""
    os.makedirs(out_dir, exist_ok=True)

    # --- サマリ CSV ---
    csv_path = os.path.join(out_dir, "results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["student_id", "gist_url",
                    "passed", "total_tests", "failed", "errors", "skipped", "pass_rate",
                    "notes"])
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

    # --- 横展開 CSV（ヘッダに全テスト名を並べる） ---
    test_names = _collect_all_test_names(results)
    wide_csv = os.path.join(out_dir, "results_wide.csv")
    with open(wide_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        header = BASE_HEADERS + test_names
        w.writerow(header)
        for row in _to_wide_rows(results, test_names):
            w.writerow(row)

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


def push_results_wide_to_google_sheets(results: List[dict], worksheet_name: Optional[str] = None) -> bool:
    """
    サマリの右側に各テスト名列を横展開して1枚のシートに追記する。
    - 既存のヘッダを尊重しつつ、足りないテスト列は末尾に追加
    - pass_rate は "100%" の文字列
    """
    gc, sheet_id = _get_gspread_client()
    if not (gc and sheet_id):
        return False

    sh = gc.open_by_key(sheet_id)
    target_tab = worksheet_name or os.environ.get("RESULT_TAB") or "results"
    try:
        ws = sh.worksheet(target_tab)
    except Exception:
        # 無ければ新規作成＆ヘッダ行
        ws = sh.add_worksheet(title=target_tab, rows=1000, cols=26)
        ws.append_row(BASE_HEADERS, value_input_option="USER_ENTERED")

    # 既存ヘッダを取得（1行目）
    existing_header: List[str] = ws.row_values(1) or []

    # 既存ヘッダのうち、BASE_HEADERS以外は「既存テスト列」とみなす
    existing_test_cols = [h for h in existing_header if h not in BASE_HEADERS]

    # 今回バッチで現れたテスト名を収集
    new_test_names = _collect_all_test_names(results)

    # ヘッダ確定：BASE_HEADERS + 既存テスト列 + （不足分の新テスト列）
    #   ※ BASE_HEADERS の順序は固定
    missing = [t for t in new_test_names if t not in existing_test_cols]
    header = BASE_HEADERS + existing_test_cols + missing

    # ヘッダ更新（必要なら）
    if existing_header != header:
        ws.update("A1", [header])

    # 行データを作成して追記
    test_col_order = header[len(BASE_HEADERS):]  # ヘッダからテスト列リストを抽出
    rows = _to_wide_rows(results, test_col_order)
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
    return True


def _collect_all_test_names(results: Sequence[dict]) -> List[str]:
    names: Set[str] = set()
    for r in results:
        for tc in r.get("tests", []) or []:
            name = tc.get("name")
            if name:
                names.add(name)
    # 見やすさのためアルファベット順
    return sorted(names)


def _to_wide_rows(results: Sequence[dict], test_col_order: Sequence[str]) -> List[List[Any]]:
    import time
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    out_rows: List[List[Any]] = []
    for r in results:
        total  = int(r.get("total_tests", 0) or 0)
        passed = int(r.get("passed", 0) or 0)
        failed = int(r.get("failed", 0) or 0)
        errors = int(r.get("errors", 0) or 0)
        skipped = int(r.get("skipped", 0) or 0)
        rate = f"{(passed/total*100):.0f}%" if total else "0%"
        base = [
            ts, r.get("student_id"), r.get("gist_url"),
            passed, total, failed, errors, skipped, rate,
            r.get("notes", ""),
        ]
        # outcome マップ
        outcomes: Dict[str, str] = {tc.get("name", ""): tc.get("outcome", "") for tc in (r.get("tests") or [])}
        row = base + [outcomes.get(name, "") for name in test_col_order]
        out_rows.append(row)
    return out_rows


# 既存の（サマリのみ）追記APIは残しておきます（未使用でも互換性のため）
def push_results_to_google_sheets(rows: List[List[Any]], worksheet_name: Optional[str] = None) -> bool:
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
