from __future__ import annotations
from pathlib import Path
import xml.etree.ElementTree as ET
import re

from grader.fetch import detect_and_fetch, FetchError
from grader.sandbox import prepare_workdir, copy_fixtures, run_pytests
from grader.report import write_reports, push_results_to_google_sheets


def _parse_pytest_fallback(log_path: Path) -> dict:
    """junit.xml が無い/読めない時のフォールバック：pytest.out をざっくり集計。"""
    summary = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "total_tests": 0, "tests": []}
    if not log_path.exists():
        return summary
    text = log_path.read_text(encoding="utf-8", errors="ignore")

    m = re.search(r"collected\s+(\d+)\s+items", text)
    if m:
        summary["total_tests"] = int(m.group(1))

    def pick(pat: str) -> int:
        mm = re.search(pat, text)
        return int(mm.group(1)) if mm else 0

    summary["passed"]  = pick(r"(\d+)\s+passed")
    summary["failed"]  = pick(r"(\d+)\s+failed")
    summary["errors"]  = pick(r"(\d+)\s+error(?:s)?")
    summary["skipped"] = pick(r"(\d+)\s+skipped")
    return summary


def _parse_junit(junit_path: Path) -> dict:
    """
    JUnit XML を集計。まず <testsuite> の属性（tests/failures/errors/skipped）を読む。
    個別 <testcase> があれば明細も作る。ダメなら pytest.out フォールバック。
    """
    base = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "total_tests": 0, "tests": []}

    if not junit_path.exists():
        return _parse_pytest_fallback(junit_path.with_name("pytest.out"))

    try:
        tree = ET.parse(str(junit_path))
        root = tree.getroot()

        # testsuites or testsuite 配下の testsuite 群を列挙
        suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
        total = failed = errors = skipped = 0
        testcases = []

        for ts in suites:
            t = int(ts.get("tests", 0))
            f = int(ts.get("failures", 0))
            e = int(ts.get("errors", 0))
            s = int(ts.get("skipped", 0))
            total += t; failed += f; errors += e; skipped += s

            for tc in ts.findall("testcase"):
                name = (tc.get("classname") or "") + ("." if tc.get("classname") else "") + (tc.get("name") or "")
                outcome = "passed"
                if tc.find("failure") is not None:
                    outcome = "failed"
                elif tc.find("error") is not None:
                    outcome = "error"
                elif tc.find("skipped") is not None:
                    outcome = "skipped"
                testcases.append({"name": name, "outcome": outcome})

        passed = max(0, total - failed - errors - skipped)
        base.update({"total_tests": total, "passed": passed, "failed": failed, "errors": errors, "skipped": skipped})
        if testcases:
            base["tests"] = testcases
        return base

    except Exception:
        # 解析に失敗した場合はフォールバック
        return _parse_pytest_fallback(junit_path.with_name("pytest.out"))


def grade_one(sid: str, url: str, out_dir: str) -> dict:
    work = prepare_workdir(out_dir, sid)
    submission_path = work / "submission.py"
    result = {"student_id": sid, "gist_url": url, "notes": ""}

    try:
        detect_and_fetch(url, str(submission_path))
    except FetchError as e:
        result.update({
            "passed": 0, "failed": 0, "errors": 0, "skipped": 0, "total_tests": 0,
            "tests": [], "notes": f"FetchError: {e}",
        })
        return result

    copy_fixtures(work)
    _ = run_pytests(work)

    junit = work / "junit.xml"
    summary = _parse_junit(junit)
    result.update(summary)
    return result


def grade_all(list_path: str | None, out_dir: str, push_to_sheets: bool = False,
              sheet_id: str | None = None, sheet_tab: str | None = None) -> None:
    from grader.sources import load_from_file, load_from_sheet
    urls = load_from_sheet(sheet_id, sheet_tab) if sheet_id else load_from_file(list_path)

    results = [grade_one(sid, url, out_dir) for sid, url in urls]
    write_reports(results, out_dir)

    if push_to_sheets:
        rows = _to_rows(results)
        push_results_to_google_sheets(rows)


def _to_rows(results: list) -> list:
    """
    Sheets 追記用の行を構築。
    - pass_rate は 0〜1 の **数値** を渡す（Sheets で「パーセント」表示にするため）
    - CSV は report.write_reports() 側で "100%" 形式の文字列を出力する
    """
    import time
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for r in results:
        total = int(r.get("total_tests", 0) or 0)
        passed = int(r.get("passed", 0) or 0)
        failed = int(r.get("failed", 0) or 0)
        errors = int(r.get("errors", 0) or 0)
        skipped = int(r.get("skipped", 0) or 0)
        rate_value = (passed / total) if total else 0.0  # 0〜1 の数値

        rows.append([
            ts, r.get("student_id"), r.get("gist_url"),
            passed, total, failed, errors, skipped, rate_value,
            r.get("notes", ""),
        ])
    return rows
