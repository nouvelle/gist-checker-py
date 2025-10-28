import argparse
import os
from grader.grade import grade_all

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gists", help="gists.txt（file）。省略時は --sheet-id を使用")
    ap.add_argument("--sheet-id", help="提出URLを読む Google Sheets のID")
    ap.add_argument("--sheet-tab", help="提出URLを読むワークシート名（未指定なら1枚目）")
    ap.add_argument("--out", default=".out", help="出力先ディレクトリ")
    ap.add_argument("--target-file", default=None, help="取得するファイル名（例: assessment-3.py / assessment-2.py）")
    ap.add_argument("--variant", default="", help="同名(assessment-3.py)で内容が異なるテストを使う場合の識別子（例: dig）")
    ap.add_argument("--push-to-sheets", action="store_true", help="Google Sheetsに追記")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # 取得ファイル名の決定：未指定なら対話入力
    target_file = args.target_file
    if not target_file:
        try:
            target_file = input("取得するファイル名を入力してください [assessment-3.py]: ").strip() or "assessment-3.py"
        except Exception:
            target_file = "assessment-3.py"


    grade_all(
        list_path=args.gists,
        out_dir=args.out,
        push_to_sheets=args.push_to_sheets,
        sheet_id=args.sheet_id,
        sheet_tab=args.sheet_tab,
        target_filename=target_file,
        variant=args.variant,
    )
