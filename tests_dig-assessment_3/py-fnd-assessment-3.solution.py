import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib
import japanize_matplotlib

def load_game_data(filename):
    df = pd.read_csv(filename)
    return df

def get_average_score_by_game(df):
    return df.groupby("ゲーム")["スコア"].mean()

def get_player_info(df, player_name):
    result = df[df["プレイヤー名"] == player_name]
    return result.iloc[0]

def filter_high_score_players(df, min_score):
    return df[df["スコア"] >= float(min_score)]

def plot_score_chart(average_scores_series, filename):
    plt.figure(figsize=(6, 4))
    average_scores_series.plot(kind="bar")
    plt.xlabel("ゲーム")
    plt.ylabel("平均スコア")
    plt.title("ゲームごとの平均スコア")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
