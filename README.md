# Python 自動採点ツール

GitHub Actions 上で、受講生の **Gist 提出**（`assessment-3.py`）を自動で取得→テスト実行→**Google スプレッドシートに結果を書き込み**ます。ローカルでも同じ処理を実行できます。

---

## 主な特徴

* **Gist 取得**：シートの「Name / Gist URL」列（`student_id / gist_url` も可）を読み込む
* **テスト実行**：`pytest` で用意済みテストを実行（CSV・描画含む）
* **結果集計**：`passed / total_tests / failed / errors / skipped / pass_rate` をまとめ、スプレッドシートにで追記
* **成果物**：`.out/` にログ・JUnit・デバッグJSON・CSV を保存。Actions の Artifacts にもアップロード

---

## 前提条件

* GitHub Actions：**GitHub-hosted runner**
* Google アカウント（スプレッドシート利用）
* 受講生は **Gist（公開）** に `assessment-3.py` をアップロード

---

## セットアップ

### 1) Google サービスアカウントの準備

1. Google Cloud でプロジェクト作成
2. 「API とサービス → 認証情報 → **サービスアカウント**」を作成
3. キーを作成 → **JSON** をダウンロード（中身をあとで GitHub Secrets へ）
4. 採点で使う **スプレッドシートをサービスアカウントのメールアドレスで共有**（閲覧/編集権限）

> ※ シートは **入力用（提出一覧）** と **出力用（結果）** を兼ねてもOKです。結果は指定タブに追記されます。

### 2) GitHub Secrets の設定

リポジトリの **Settings → Secrets and variables → Actions** に以下を登録：

* `GOOGLE_SERVICE_ACCOUNT_JSON`：サービスアカウント JSON の**中身を丸ごと**貼り付け
* `GOOGLE_SHEET_ID`：対象スプレッドシートの ID（URL の `.../d/<この部分>/edit`）

### 3) シートの入力タブ

* 1 行目（ヘッダ）に **`Name` / `Gist URL`**（`student_id` / `gist_url` でもOK）
* 2 行目以降に受講生ごとの行を入力

### 4) 依存パッケージ

`requirements.txt` に主要依存が列挙済み。Actions で自動インストールされます。

---

## 使い方

### A. GitHub Actions で実行（推奨）

1. GitHub の **Actions → Grade Submissions** を開く
2. **Run workflow** を押し、必要なら以下を入力

   * `sheet_id`：空なら Secrets の `GOOGLE_SHEET_ID` を使用
   * `sheet_tab`：提出一覧を読むタブ名（未指定なら先頭シート）
   * `result_tab`：結果を書き込むタブ名（既定: `results`）
   * `gists_path`：`gists.txt` を使う場合のみ（通常は空でOK）
3. 実行後：

   * **Artifacts** に `.out/` 一式（各受講生の `junit.xml` / `pytest.out` / `summary_debug.json` 等）
   * 指定の `result_tab` に結果（横展開）を**追記**

### B. ローカルで実行

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# gists.txt から読む場合
python run.py --gists gists.txt --out .out

# Google Sheets から読む場合（結果を書き込みたいときは --push-to-sheets）
export GOOGLE_SERVICE_ACCOUNT_JSON='...JSONの中身...'
export GOOGLE_SHEET_ID='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
python run.py --sheet-id $GOOGLE_SHEET_ID --sheet-tab <入力タブ名> --out .out --push-to-sheets
```

---

## スプレッドシート出力（横展開）

* 書き込み先タブ（`result_tab`、既定: `results`）の 1 行目がヘッダ
* **左側：サマリ列**、**右側：テスト名ごとの列**
* 新しいテスト名が出た場合は**末尾に自動で列追加**

### サマリ列（固定）

| 列名            | 説明                                 |
| ------------- | ---------------------------------- |
| `time`        | 追記した日時（JSTではなくランナーのタイムゾーン準拠）       |
| `student_id`  | シートの `Name`（未入力なら連番 001, 002, ...） |
| `gist_url`    | Gist の URL                         |
| `passed`      | パスしたテスト数                           |
| `total_tests` | 総テスト数                              |
| `failed`      | 失敗数（assert 失敗）                     |
| `errors`      | エラー数（例外など）                         |
| `skipped`     | スキップ数                              |
| `pass_rate`   | 合格率（`"100%"` の**文字列**）             |
| `notes`       | 取得エラーなどのメモ（例：`FetchError: ...`）    |

### テスト列（可変）

* 列名：`tests.test_XX_xxx.test_yyy` のフル名
* セル値：`passed` / `failed` / `error` / `skipped`

---

## テスト仕様（課題要件）

生徒の提出ファイル：**`assessment-3.py`**（Gist）。採点器では `submission.py` として実行。

1. `load_game_data(filename)`

   * CSV を DataFrame で返す
   * ファイル未存在などの読み込みエラーは **`GameDataError`** を送出
2. `get_average_score_by_game(df)`

   * ゲームごとの平均スコア（`pd.Series`）
3. `get_player_info(df, player_name)`

   * 指定プレイヤーの情報（`pd.Series`）。見つからない場合 **`KeyError`**（メッセージに名前を含める）
4. `filter_high_score_players(df, min_score)`

   * `min_score` 以上の行を返す。`min_score` が数値でない場合は **`TypeError("最小スコアは数値で指定してください")`**
5. `plot_score_chart(average_scores_series, filename)`

   * タイトル「**ゲームごとの平均スコア**」/ X「**ゲーム**」/ Y「**平均スコア**」の棒グラフを保存
   * 非インタラクティブ（`MPLBACKEND=Agg`）で保存できること

> 付属の `fixtures/game_scores.csv` を使用。テストは `tests/` を参照してください。

---

## 処理フロー

```
Google Sheets（入力: Name, Gist URL）
           │
workflow_dispatch（GitHub Actions）
           │
  fetch：Gist から assessment-3.py を保存（submission.py として）
           │
  pytest：tests/*.py を実行 → junit.xml / pytest.out 生成
           │
  grade：結果集計 → .out/ に CSV/JSON 出力
           │
  report：Google Sheets の result_tab に 1行追記（右側に各テスト列を横展開）
```

---

## リポジトリ構成（抜粋）

```
.
├─ run.py
├─ requirements.txt
├─ fixtures/                # 課題で使うCSVなど
│  └─ game_scores.csv
├─ tests/                   # 採点用テスト
│  ├─ conftest.py
│  ├─ test_01_load_game_data.py
│  ├─ test_02_get_average_score_by_game.py
│  ├─ test_03_get_player_info.py
│  ├─ test_04_filter_high_score_players.py
│  └─ test_05_plot_score_chart.py
├─ grader/
│  ├─ fetch.py              # Gist 取得
│  ├─ sandbox.py            # pytest 実行（Agg/タイムアウト、JUnit出力）
│  ├─ grade.py              # JUnit/pytest.out の堅牢集計
│  └─ report.py             # CSV出力 & Sheets 追記（横展開）
└─ .github/workflows/grade.yml
```

---


## よくあるエラーと対処

* **Artifacts が「–」/ 何も上がらない**：`.out` が空。ワークフローの「Debug outputs」で `.out` の中身を確認
* **全テストが error（`ModuleNotFoundError`）**：学生コードが外部ライブラリを `import`。必要なら `requirements.txt` に追加
* **`total_tests` が 0**：JUnit が読めていない可能性 → `.out/<ID>/summary_debug.json` の `source` を確認（`junit` が理想、`pytest.out` はフォールバック）
* **Sheets に書かれない**：`GOOGLE_SERVICE_ACCOUNT_JSON` / `GOOGLE_SHEET_ID` / シェア設定（サービスアカウントに権限付与）を再確認
* **Gist に `assessment-3.py` が無い**：`FetchError` を `notes` に記録。ファイル名を合わせてもらうか、`grader/fetch.py` を拡張（別名許可）

---

## 開発・デバッグ Tips

* ローカルでの個別確認：`.out/<ID>/pytest.out` と `junit.xml`、`summary_debug.json` を見る
* 画像生成テストは `Agg` 前提。フォントは Noto CJK を使用
* Actions の Artifacts は `include-hidden-files: true` で `.out` を確実に取得


======

# Gist Checker for Python Assessments

このリポジトリは、Code Chrysalis の Python 課題 (`assessment-2.py` / `assessment-3.py`) を自動採点するツールです。  
提出された Gist または Google Sheets 上の URL からコードを取得し、pytest によるテスト結果を収集・集計します。

---

## 📦 対応バージョン

| 対象ファイル | 対応テストフォルダ | 説明 |
|---------------|--------------------|------|
| `assessment-3.py` | `tests/` | 従来のテスト（ゲームスコア課題など） |
| `assessment-2.py` | `tests_assessment_2/` | 追加課題用。pytestファイルを配置してください。 |

---

## 🚀 ワークフロー実行方法（GitHub Actions）

このリポジトリには `.github/workflows/grade.yml` が含まれています。  
`workflow_dispatch` に対応しているため、**手動実行時に入力フォームから設定**できます。

### 1️⃣ ワークフロー入力項目

| 入力項目 | 説明 | 例 |
|-----------|------|----|
| **mode** | `gists`（テキストファイル入力）または `sheet`（Google Sheets入力） | gists |
| **gists_file** | Gist一覧を記したテキストファイルのパス | gists.txt |
| **sheet_id** | Google Sheets の ID（mode=sheet の場合） | `1AbCdEfgHIjK...` |
| **sheet_tab** | 読み込むシートタブ名 | submissions |
| **out_dir** | 採点結果の出力先ディレクトリ | `.out` |
| **push_to_sheets** | `true` で採点結果をシートに追記 | false |
| **target_file** | 採点対象ファイル名（例: `assessment-2.py` / `assessment-3.py`） | `assessment-3.py` |

---

### 2️⃣ 実行例

#### ✅ Gist モード（gists.txtから採点）

```
mode: gists
gists_file: gists.txt
target_file: assessment-2.py
out_dir: .out
```

#### ✅ Google Sheets モード（Sheetから採点）

```
mode: sheet
sheet_id: 1AbCdEfgHIjK...
sheet_tab: Submissions
push_to_sheets: true
target_file: assessment-3.py
```

> 🔐 `GOOGLE_SERVICE_ACCOUNT_JSON` を GitHub Secrets に設定しておく必要があります。

---

## ⚙️ ローカル実行（手動テスト）

ローカルでテストしたい場合は次のように実行します。

### Gists モード
```bash
python run.py --gists gists.txt --out .out --target-file assessment-3.py
```

### Sheets モード
```bash
export GOOGLE_SERVICE_ACCOUNT_JSON='...JSON文字列...'
export GOOGLE_SHEET_ID='1AbCdEfgHIjK...'
python run.py --sheet-id $GOOGLE_SHEET_ID --sheet-tab submissions --out .out --push-to-sheets --target-file assessment-2.py
```

---

## 🧪 ディレクトリ構成（概要）

```
.
├── run.py
├── fixtures/                # 課題で使うデータ (例: game_scores.csv)
├── tests_assessment_3/      # assessment-3 用のテスト
├── tests_assessment_2/      # assessment-2 用のテスト
├── grader/                  # 採点処理の内部ロジック
│   ├── fetch.py             # Gist 取得ロジック（target_file対応済み）
│   ├── grade.py             # pytest実行と結果集計
│   ├── sandbox.py           # pytestサブプロセス管理
│   └── report.py            # CSV/Sheets出力
└── .github/workflows/grade.yml
```

---

## 🧰 主な更新点

- `--target-file` フラグで **任意のファイル名を指定可能**
- **GitHub Actionsのinputsから `target_file` を受け取れる**
- 対話的な `input()` は廃止（CI対応）
- `assessment-3.py` / `assessment-2.py` の両方を柔軟に採点可能

---

## ✅ 実装メモ

- Gist ページ or raw URL のどちらにも対応
- `target_file` に一致するファイルが Gist に見つからなければ `FetchError`
- pytest 結果は `.out/<student_id>/` に出力
- CSV / JSON レポートは `.out/results.csv` および `.out/results.json` に保存されます

---

## 🧩 拡張予定（任意）

- `assessment-1.py` など他の課題にも対応可能（`fetch.py` の RAW_RE に追加するだけ）
- `tests_assessment_2/` 内で input() や lambda, filter, map 等の課題も自由にテスト可能
