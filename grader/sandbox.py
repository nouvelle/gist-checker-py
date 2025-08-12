# grader/sandbox.py（差し替え）
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

def run_pytests(work_dir: Path, tests_dir: str = "tests", timeout_sec: int = 120) -> int:
    """
    pytest をサブプロセスで実行。
    - cwd は work_dir（conftest が submission.py を拾えるように）
    - tests_dir はリポジトリ内 tests の “絶対パス” を渡す
    """
    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")
    env["PYTHONPATH"] = str(work_dir)
    env["SCORE_OUTPUT"] = str(work_dir / "scores.json")

    # リポジトリの tests ディレクトリの絶対パス
    repo_root = Path(__file__).resolve().parent.parent  # grader/ の親 = リポジトリルート
    tests_abs = (repo_root / tests_dir).resolve()

    junit = work_dir / "junit.xml"
    log_path = work_dir / "pytest.out"

    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_abs),        # ← 絶対パスで指定
        "-q", "--timeout=20",
        f"--junitxml={junit}"
    ]
    with open(log_path, "w", encoding="utf-8") as logf:
        proc = subprocess.run(
            cmd, cwd=str(work_dir), env=env,
            stdout=logf, stderr=subprocess.STDOUT, timeout=timeout_sec
        )
    return proc.returncode
