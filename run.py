import argparse
import os
from grader.grade import grade_all

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gists", help="gists.txt（file）。省略時は --sheet-id を使用")
    ap.add_argument("--sheet-id", help="提出URLを読む Google Sheets のID")
    ap.add_argument("--sheet-tab", help="ワークシート名（未指定なら1枚目）")
    ap.add_argument("--out", default=".out")
    ap.add_argument("--push-to-sheets", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    grade_all(list_path=args.gists, out_dir=args.out, push_to_sheets=args.push_to_sheets,
              sheet_id=args.sheet_id, sheet_tab=args.sheet_tab)
