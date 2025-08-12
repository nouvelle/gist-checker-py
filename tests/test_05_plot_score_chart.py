import os

LABEL_TITLE = "ゲームごとの平均スコア"
LABEL_X = "ゲーム"
LABEL_Y = "平均スコア"

def test_plot_and_labels(submission_module, fixture_csv_path, add_score):
    # 非インタラクティブ（Agg）で動くことを前提に実行
    assert os.environ.get("MPLBACKEND", "") == "Agg"
    add_score("q5", "non_interactive")

    df = submission_module.load_game_data(fixture_csv_path)
    s = submission_module.get_average_score_by_game(df)
    out = "average_scores.png"
    if os.path.exists(out):
        os.remove(out)

    submission_module.plot_score_chart(s, out)

    assert os.path.exists(out), "画像が保存されていません"
    assert os.path.getsize(out) > 500, "画像サイズが小さすぎます"
    add_score("q5", "file_saved")

    # 学生のコードに期待ラベル文字列が含まれているかを簡易チェック
    try:
        with open("submission.py", encoding="utf-8") as f:
            src = f.read()
        assert LABEL_TITLE in src and LABEL_X in src and LABEL_Y in src
        add_score("q5", "labels_present")
    except Exception:
        pass
