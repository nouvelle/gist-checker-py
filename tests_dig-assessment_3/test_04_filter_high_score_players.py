import pytest

EXPECTED = ["次郎", "さくら", "大輝", "結愛"]

def test_filter_numeric(submission_module, fixture_csv_path):
    df = submission_module.load_game_data(fixture_csv_path)
    res = submission_module.filter_high_score_players(df, 1300)
    assert set(res["プレイヤー名"]) == set(EXPECTED)

def test_expected_players(submission_module, fixture_csv_path):
    df = submission_module.load_game_data(fixture_csv_path)
    res = submission_module.filter_high_score_players(df, 1300)
    assert res.shape[0] == 4
