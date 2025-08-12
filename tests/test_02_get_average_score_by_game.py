import pandas as pd

def test_average_values(submission_module, fixture_csv_path):
    df = submission_module.load_game_data(fixture_csv_path)
    s = submission_module.get_average_score_by_game(df)
    assert isinstance(s, pd.Series)
    assert s["マリオカート"] == 1082.5
    assert s["ドンキーコング"] == 1250.0
    assert s["パックマン"] == 1450.0
