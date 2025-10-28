import pandas as pd
import pytest

def test_returns_dataframe(submission_module, fixture_csv_path):
    df = submission_module.load_game_data(fixture_csv_path)
    assert isinstance(df, pd.DataFrame)

def test_shape_and_cols(submission_module, fixture_csv_path):
    df = submission_module.load_game_data(fixture_csv_path)
    assert df.shape == (10, 5)
    assert df.columns.tolist() == ["プレイヤー名", "ゲーム", "スコア", "プレイ時間", "レベル"]
