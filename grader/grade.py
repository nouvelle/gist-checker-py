from __future__ import annotations
from pathlib import Path
import xml.etree.ElementTree as ET
import re
import json

from grader.fetch import detect_and_fetch, FetchError
from grader.sandbox import prepare_workdir, copy_fixtures, run_pytests
from grader.report import (
    write_reports,
    push_results_wide_to_google_sheets,  # ← 追加：横展開で1枚に追記
)


def _parse_pytest_fallback(log_path: Path) -> dict:
    """junit.xml が無い/読めない時のフォールバック：pytest.out をざっくり集計。"""
    summary = {
        "source": "pytest.out",
        "passed": 0, "failed": 0, "errors": 0, "skipped": 0,
        "total_tests": 0, "tests": []
    }
    if not log_path.exists():
        return summary
    text = log_path.read_text(encoding="utf-8", errors="ignore")

    def pick(pat: str) -> int:
        mm = re.search(pat, text)
        return int(mm.group(1)) if mm else 0

    collected = re.search(r"collected\s+(\d+)\s+items", text)
    passed = pick(r"(\d+)\s+passed")
    failed  = pick(r"(\d+)\s+failed")
    errors  = pick(r"(\d+)\s+error(?:s)?")
    skipped = pick(r"(\d+)\s+skipped")

    total = int(collected.group(1)) if collected else (passed + failed + errors + skipped)

    summary.update({
        "passed": passed, "failed": failed, "errors": errors, "skipped": skipped,
        "total_tests": total,
    })
    return summary


def _parse_junit(junit_path: Path) -> dict:
    """
    JUnit XML を集計。まず <testsuite> の属性（tests/failures/errors/skipped）で合計値を確定。
    個別 <testcase> があれば明細も作る。失敗時は pytest.out フォールバック。
    """
    if not junit_path.exists():
        return _parse_pytest_fallback(junit_path.with_name("pytest.out"))

    try:
        tree = ET.parse(str(junit_path))
        root = tree.getroot()

        suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))

        total = failed = errors = skipped = 0
        testcases = []

        for ts in suites:
            # 属性で合計を集計（確実）
            t = int(ts.get("tests", 0) or 0)
            f = int(ts.get("failures", 0) or 0)
            e = int(ts.get("errors", 0) or 0)
            s = int(ts.get("skipped", 0) or 0)
            total += t; failed += f; errors += e; skipped += s

            # 明細（あれば）
            for tc in ts.findall("testcase"):
                cls = tc.get("classname") or ""
                name = tc.get("name") or ""
                dotted = cls + ("." if cls and name else "") + name
                outcome = "passed"
                if tc.find("failure") is not None:
                    outcome = "failed"
                elif tc.find("error") is not None:
                    outcome = "error"
                elif tc.find("skipped") is not None:
                    outcome = "skipped"
                tsec = float(tc.get("time", 0) or 0)
                testcases.append({"name": dotted, "outcome": outcome, "time": tsec})

        passed = max(0, total - failed - errors - skipped)
        return {
            "source": "junit",
            "total_tests": total, "passed": passed, "failed": failed, "errors": errors, "skipped": skipped,
            "tests": testcases,
        }

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
            "source": "fetch_error",
            "passed": 0, "failed": 0, "errors": 0, "skipped": 0, "total_tests": 0,
            "tests": [], "notes": f"FetchError: {e}",
        })
        return result

    copy_fixtures(work)
    _ = run_pytests(work)

    junit = work / "junit.xml"
    summary = _parse_junit(junit)
    result.update(summary)

    # デバッグ出力
    try:
        (work / "summary_debug.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass

    return result


def grade_all(list_path: str | None, out_dir: str, push_to_sheets: bool = False,
              sheet_id: str | None = None, sheet_tab: str | None = None) -> None:
    from grader.sources import load_from_file, load_from_sheet
    urls = load_from_sheet(sheet_id, sheet_tab) if sheet_id else load_from_file(list_path)

    results = [grade_one(sid, url, out_dir) for sid, url in urls]
    write_reports(results, out_dir)

    if push_to_sheets:
        push_results_wide_to_google_sheets(results)  # ← これ1発で横展開して追記


def _to_rows(results: list) -> list:
    """
    （ローカルCSV用）サマリのみの行を構築。Sheets は push_results_wide_to_google_sheets() を使用。
    - pass_rate は **"100%" の文字列**で出力
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
        rate_str = f"{(passed/total*100):.0f}%" if total else "0%"

        rows.append([
            ts, r.get("student_id"), r.get("gist_url"),
            passed, total, failed, errors, skipped, rate_str,
            r.get("notes", ""),
        ])
    return rows
