import json
import os
import pathlib
import importlib.util
import sys
import types
import pytest

# 各問題の配点（20点×5 = 100点）
POINTS = {
    "q1": {"returns_df": 8, "shape_cols": 6, "raises_custom": 6},
    "q2": {"series_type": 5, "avg_mario": 5, "avg_donkey": 5, "avg_pac": 5},
    "q3": {"series_taro": 8, "raises_keyerror": 6, "keyerror_msg": 6},
    "q4": {"filter_numeric": 8, "expected_players": 6, "typeerror_msg": 6},
    "q5": {"file_saved": 6, "labels_present": 8, "non_interactive": 6},
}


@pytest.fixture(scope="session")
def score_board():
    return {"q1": {}, "q2": {}, "q3": {}, "q4": {}, "q5": {}}


@pytest.fixture(scope="session")
def write_scores(score_board):
    # セッション終了時に JSON へ書き出し
    yield
    out = os.environ.get("SCORE_OUTPUT", "scores.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(score_board, f, ensure_ascii=False, indent=2)


@pytest.fixture
def add_score(score_board):
    def _add(qkey: str, item: str):
        pts = POINTS[qkey][item]
        score_board[qkey][item] = pts
    return _add


@pytest.fixture(scope="session")
def submission_module(tmp_path_factory):
    # カレント（work_dir）にある submission.py を import
    p = pathlib.Path.cwd() / "submission.py"
    if not p.exists():
        pytest.skip("submission.py が見つかりません")
    spec = importlib.util.spec_from_file_location("submission", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["submission"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def fixture_csv_path():
    # work_dir にコピー済みを想定
    p = pathlib.Path.cwd() / "game_scores.csv"
    if not p.exists():
        pytest.skip("game_scores.csv が見つかりません")
    return str(p)


@pytest.fixture(autouse=True)
def _finalize_session(write_scores):
    # セッション終了後に write_scores を呼び出すためのダミー
    yield
