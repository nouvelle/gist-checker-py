import pandas as pd
import pytest

def test_returns_dataframe(submission_module, fixture_csv_path, add_score):
    df = submission_module.load_game_data(fixture_csv_path)
    assert isinstance(df, pd.DataFrame)
    add_score("q1", "returns_df")

def test_shape_and_cols(submission_module, fixture_csv_path, add_score):
    df = submission_module.load_game_data(fixture_csv_path)
    assert df.shape == (10, 5)
    assert df.columns.tolist() == ["プレイヤー名", "ゲーム", "スコア", "プレイ時間", "レベル"]
    add_score("q1", "shape_cols")

def test_raises_custom_error_on_missing(submission_module, add_score, tmp_path):
    with pytest.raises(submission_module.GameDataError):
        submission_module.load_game_data(str(tmp_path / "missing.csv"))
    add_score("q1", "raises_custom")
