import pytest

def test_player_series_taro(submission_module, fixture_csv_path):
    df = submission_module.load_game_data(fixture_csv_path)
    s = submission_module.get_player_info(df, "太郎")
    assert s["ゲーム"] == "マリオカート"
    assert s["スコア"] == 1250
