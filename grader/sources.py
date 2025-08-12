from __future__ import annotations
from typing import List, Tuple
import csv
import os
import json
import gspread
from google.oauth2.service_account import Credentials


def load_from_file(list_path: str) -> List[Tuple[str, str]]:
    rows = []
    with open(list_path, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            u = line.strip()
            if not u or u.startswith("#"):
                continue
            sid = f"{i:03d}"
            rows.append((sid, u))
    return rows


def load_from_sheet(sheet_id: str, worksheet: str | None = None) -> List[Tuple[str, str]]:
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON が未設定です")

    info = json.loads(sa_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(worksheet) if worksheet else sh.sheet1

    values = ws.get_all_records()  # 1行目をヘッダとして辞書化
    rows: List[Tuple[str, str]] = []
    for i, rec in enumerate(values, start=1):
        sid = str(rec.get("student_id") or f"{i:03d}")
        url = (rec.get("gist_url") or "").strip()
        if not url:
            continue
        rows.append((sid, url))
    return rows

def load_urls(list_path: str) -> List[Tuple[str, str]]:
    """gists.txt（1行1URL）を student_id 付き配列に正規化。
    例: [("001", url1), ("002", url2), ...]
    """
    rows: List[Tuple[str, str]] = []
    with open(list_path, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            u = line.strip()
            if not u or u.startswith("#"):
                continue
            sid = f"{i:03d}"
            rows.append((sid, u))
    return rows
