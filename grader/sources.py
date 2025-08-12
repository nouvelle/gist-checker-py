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


def _pick(d: dict, keys: list[str]) -> str | None:
    """辞書 d から候補キーのどれかを見つけて値を返す（空文字は無視）。"""
    for k in keys:
        if k in d and str(d[k]).strip():
            return str(d[k]).strip()
    # ゆるめの小文字化一致も試す
    lower = {str(k).strip().lower(): v for k, v in d.items()}
    for k in keys:
        lk = str(k).strip().lower()
        if lk in lower and str(lower[lk]).strip():
            return str(lower[lk]).strip()
    return None


def load_from_sheet(sheet_id: str, worksheet: str | None = None) -> List[Tuple[str, str]]:
    """
    Google Sheets から提出URLを読む。
    対応ヘッダ（先勝ち）:
      - 学籍/氏名:  "Name", "student_id"
      - GistURL :  "Gist URL", "gist_url"
    いずれも無ければ、Name は連番(001,002,...)、URL は空ならスキップ。
    """
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
        # ヘッダの候補を順に探す（新: Name / Gist URL、旧: student_id / gist_url）
        sid = _pick(rec, ["Name", "student_id"]) or f"{i:03d}"
        url = _pick(rec, ["Gist URL", "gist_url"]) or ""
        if not url:
            continue
        rows.append((sid, url))
    return rows
