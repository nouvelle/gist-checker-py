from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path


def prepare_workdir(base_out: str, student_id: str) -> Path:
    work = Path(base_out) / student_id
    work.mkdir(parents=True, exist_ok=True)
    return work


def copy_fixtures(work_dir: Path, fixtures_dir: str = "fixtures") -> None:
    src = Path(fixtures_dir) / "game_scores.csv"
    dst = work_dir / "game_scores.csv"
    shutil.copy2(src, dst)


def run_pytests(work_dir: Path, tests_dir: str = "tests_assessment_3", timeout_sec: int = 120) -> int:
    project_root = Path(__file__).resolve().parents[1]
    tests_path = project_root / tests_dir  # ← conftestを含むディレクトリを直接指定

    # デバッグ: conftest の存在をログに出す（後で確認しやすい）
    debug = [
        f"[sandbox] project_root={project_root}",
        f"[sandbox] tests_path={tests_path}",
        f"[sandbox] conftest_exists={(tests_path / 'conftest.py').exists()}",
    ]
    (work_dir / "pytest_debug.txt").write_text("\n".join(debug), encoding="utf-8")

    junit_path = work_dir / "junit.xml"
    cmd = ["pytest", "-q", str(tests_path), "--junit-xml", str(junit_path)]

    proc = subprocess.run(
        cmd,
        cwd=work_dir,
        timeout=timeout_sec,
        capture_output=True,
        text=True,
    )
    (work_dir / "pytest_stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
    (work_dir / "pytest_stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
    return proc.returncode
