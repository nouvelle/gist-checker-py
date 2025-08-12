import pathlib, importlib.util, sys, pytest

@pytest.fixture(scope="session")
def submission_module():
    p = pathlib.Path.cwd() / "submission.py"
    if not p.exists():
        pytest.skip("submission.py が見つかりません")
    spec = importlib.util.spec_from_file_location("submission", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["submission"] = mod
    spec.loader.exec_module(mod)
    return mod

@pytest.fixture(scope="session")
def fixture_csv_path():
    p = pathlib.Path.cwd() / "game_scores.csv"
    if not p.exists():
        pytest.skip("game_scores.csv が見つかりません")
    return str(p)
