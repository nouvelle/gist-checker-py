from __future__ import annotations
import json
from typing import List, Tuple
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo  # ← 追加：標準ライブラリでJST

from grader.fetch import detect_and_fetch, FetchError
from grader.sandbox import prepare_workdir, copy_fixtures, run_pytests
from grader.report import write_reports, push_results_wide_to_google_sheets


def _pick_tests_dir_from_target(target_filename: str) -> str:
    """
    target_filename からテストディレクトリを判定。
    - assessment-2.py → tests_assessment_2
    - assessment-3.py → tests_assessment_3
    """
    u = (target_filename or "").lower()
    if "assessment-2.py" in u:
        return "tests_assessment_2"
    if "assessment-3.py" in u:
        return "tests_assessment_3"
    return "tests_assessment_3"  # デフォルト



def _parse_junit(junit_path: Path) -> dict:
    """junit.xml からテスト結果を集計（何問中いくつパスしたか＋各テストの結果）。"""
    summary = {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "total_tests": 0,
        "tests": [],  # {name, outcome}
    }
    if not junit_path.exists():
        return summary

    try:
        tree = ET.parse(str(junit_path))
        root = tree.getroot()
        suites = []
        if root.tag == "testsuite":
            suites = [root]
        elif root.tag == "testsuites":
            suites = list(root.findall("testsuite"))

        tests = []
        for ts in suites:
            for tc in ts.findall("testcase"):
                name = tc.get("classname")
                name = (name + "." if name else "") + (tc.get("name") or "")
                outcome = "passed"
                if tc.find("failure") is not None:
                    outcome = "failed"
                elif tc.find("error") is not None:
                    outcome = "error"
                elif tc.find("skipped") is not None:
                    outcome = "skipped"
                tests.append({"name": name, "outcome": outcome})

        summary["tests"] = tests
        summary["total_tests"] = len(tests)
        summary["passed"] = sum(1 for t in tests if t["outcome"] == "passed")
        summary["failed"] = sum(1 for t in tests if t["outcome"] == "failed")
        summary["errors"] = sum(1 for t in tests if t["outcome"] == "error")
        summary["skipped"] = sum(1 for t in tests if t["outcome"] == "skipped")
    except Exception:
        # 解析失敗時は summary を初期値のまま返す
        pass

    return summary


def grade_one(sid: str, url: str, out_dir: str) -> dict:
    work = prepare_workdir(out_dir, sid)

    # 1) 提出物取得
    submission_path = work / "submission.py"
    result = {"student_id": sid, "gist_url": url, "notes": ""}
    try:
        detect_and_fetch(url, str(submission_path))
    except FetchError as e:
        result.update({
            "passed": 0, "failed": 0, "errors": 0, "skipped": 0, "total_tests": 0,
            "tests": [],
            "notes": f"FetchError: {e}",
        })
        return result

    # 2) フィクスチャ配置
    copy_fixtures(work)

    # 3) テスト実行
    _ = run_pytests(work)

    # 4) junit.xml からパス数を集計
    junit = work / "junit.xml"
    summary = _parse_junit(junit)

    result.update(summary)
    return result


def grade_all(
    list_path: str | None,
    out_dir: str,
    push_to_sheets: bool = False,
    sheet_id: str | None = None,
    sheet_tab: str | None = None,
    target_filename: str = "assessment-3.py"
) -> None:
    from grader.sources import load_from_file, load_from_sheet

    if sheet_id:
        urls = load_from_sheet(sheet_id, sheet_tab)
    else:
        assert list_path, "list_path か sheet_id のどちらかが必要です"
        urls = load_from_file(list_path)

    results = [
        grade_one(sid, url, out_dir, target_filename=target_filename)
        for sid, url in urls
    ]
    write_reports(results, out_dir)

    if push_to_sheets:
        push_results_wide_to_google_sheets(results)
