import pandas as pd


def test_average_values(submission_module, fixture_csv_path, add_score):
    df = submission_module.load_game_data(fixture_csv_path)
    s = submission_module.get_average_score_by_game(df)
    assert isinstance(s, pd.Series)
    add_score("q2", "series_type")

    assert s["マリオカート"] == 1082.5
    add_score("q2", "avg_mario")

    assert s["ドンキーコング"] == 1250.0
    add_score("q2", "avg_donkey")

    assert s["パックマン"] == 1450.0
    add_score("q2", "avg_pac")
