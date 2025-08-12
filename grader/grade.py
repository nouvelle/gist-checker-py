from __future__ import annotations
import csv
import json
import os
import time
from pathlib import Path
from typing import List, Tuple

from grader.fetch import detect_and_fetch, FetchError
from grader.sandbox import prepare_workdir, copy_fixtures, run_pytests
from grader.report import write_reports, push_results_to_google_sheets
from grader.sources import load_from_file, load_from_sheet


# def load_urls(list_path: str) -> List[Tuple[str, str]]:
#     """gists.txt（1行1URL）を student_id 付き配列に正規化。
#     例: [("001", url1), ("002", url2), ...]
#     """
#     rows: List[Tuple[str, str]] = []
#     with open(list_path, encoding="utf-8") as f:
#         for i, line in enumerate(f, start=1):
#             u = line.strip()
#             if not u or u.startswith("#"):
#                 continue
#             sid = f"{i:03d}"
#             rows.append((sid, u))
#     return rows


def grade_one(sid: str, url: str, out_dir: str) -> dict:
    work = prepare_workdir(out_dir, sid)

    # 1) 提出物取得
    submission_path = work / "submission.py"
    result = {"student_id": sid, "gist_url": url, "notes": ""}
    try:
        detect_and_fetch(url, str(submission_path))
    except FetchError as e:
        result.update({
            "total": 0, "q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0,
            "notes": f"FetchError: {e}"
        })
        return result

    # 2) フィクスチャ配置
    copy_fixtures(work)

    # 3) テスト実行
    rc = run_pytests(work)

    # 4) スコア読込
    scores_file = work / "scores.json"
    if scores_file.exists():
        with open(scores_file, encoding="utf-8") as f:
            scores = json.load(f)
    else:
        scores = {}

    # 問題ごとに合計（存在しなければ0）
    q1 = sum(scores.get("q1", {}).values())
    q2 = sum(scores.get("q2", {}).values())
    q3 = sum(scores.get("q3", {}).values())
    q4 = sum(scores.get("q4", {}).values())
    q5 = sum(scores.get("q5", {}).values())
    total = q1 + q2 + q3 + q4 + q5

    result.update({"total": total, "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5})
    return result


def grade_all(list_path: str | None, out_dir: str, push_to_sheets: bool = False,
              sheet_id: str | None = None, sheet_tab: str | None = None) -> None:
    if sheet_id:
        urls = load_from_sheet(sheet_id, sheet_tab)
    else:
        assert list_path, "list_path か sheet_id のどちらかが必要です"
        urls = load_from_file(list_path)

    results = []
    for sid, url in urls:
        res = grade_one(sid, url, out_dir)
        results.append(res)
    write_reports(results, out_dir)
    if push_to_sheets:
        # （採点結果の）Sheets追記は既存の実装のまま
        rows = _to_rows(results)
        push_results_to_google_sheets(rows)


def _to_rows(results: list) -> list:
    import time
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for r in results:
        rows.append([
            ts, r.get("student_id"), r.get("gist_url"), r.get("total", 0),
            r.get("q1", 0), r.get("q2", 0), r.get("q3", 0), r.get("q4", 0), r.get("q5", 0),
            r.get("notes", "")
        ])
    return rows
