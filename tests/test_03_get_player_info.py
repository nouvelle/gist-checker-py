import pytest

def test_player_series_taro(submission_module, fixture_csv_path):
    df = submission_module.load_game_data(fixture_csv_path)
    s = submission_module.get_player_info(df, "太郎")
    assert s["ゲーム"] == "マリオカート"
    assert s["スコア"] == 1250

def test_player_missing_keyerror(submission_module, fixture_csv_path):
    df = submission_module.load_game_data(fixture_csv_path)
    missing = "存在しない人"
    with pytest.raises(KeyError) as ei:
        submission_module.get_player_info(df, missing)

    # メッセージに名前を含む
    assert missing in str(ei.value)
