import pytest

EXPECTED = ["次郎", "さくら", "大輝", "結愛"]

def test_filter_numeric(submission_module, fixture_csv_path, add_score):
    df = submission_module.load_game_data(fixture_csv_path)
    res = submission_module.filter_high_score_players(df, 1300)
    assert set(res["プレイヤー名"]) == set(EXPECTED)
    add_score("q4", "filter_numeric")

def test_expected_players(submission_module, fixture_csv_path, add_score):
    df = submission_module.load_game_data(fixture_csv_path)
    res = submission_module.filter_high_score_players(df, 1300)
    assert res.shape[0] == 4
    add_score("q4", "expected_players")

def test_typeerror_message(submission_module, fixture_csv_path, add_score):
    df = submission_module.load_game_data(fixture_csv_path)
    with pytest.raises(TypeError) as ei:
        submission_module.filter_high_score_players(df, "abc")
    assert str(ei.value) == "最小スコアは数値で指定してください"
    add_score("q4", "typeerror_msg")
