# tests/conftest.py
import ast
import pathlib
import types
import sys
import pytest

def _safe_import_submission(path: pathlib.Path):
    """
    提出物 submission.py を『安全インポート』する。
    - トップレベルの実行文（関数呼び出し・print 等）は全て無視
    - 以下のみを残して読み込む：Import / ImportFrom / FunctionDef / ClassDef
      → 受講生の末尾にある手元テスト等は実行されない
    """
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))

    keep_nodes = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            keep_nodes.append(node)
        else:
            # Assign/Expr/If などトップレベル実行は捨てる
            # ※ if __name__ == "__main__": の中身も実行しない方針
            continue

    mod_ast = ast.Module(body=keep_nodes, type_ignores=[])
    code = compile(mod_ast, str(path), "exec")

    module = types.ModuleType("submission")
    module.__file__ = str(path)

    # 実行
    exec(code, module.__dict__)
    sys.modules["submission"] = module
    return module


@pytest.fixture(scope="session")
def submission_module():
    """
    work_dir（.out/<id>/）直下の submission.py を『安全インポート』して返す。
    - ファイルが無ければ skip
    - 構文エラー等でどうしても読み込めなければ、pytest 既定のエラーになる
      （※構文エラーは全テスト継続が困難なため）
    """
    p = pathlib.Path.cwd() / "submission.py"
    if not p.exists():
        pytest.skip("submission.py が見つかりません")

    return _safe_import_submission(p)


@pytest.fixture(scope="session")
def fixture_csv_path():
    # work_dir にコピー済みを想定
    p = pathlib.Path.cwd() / "game_scores.csv"
    if not p.exists():
        pytest.skip("game_scores.csv が見つかりません")
    return str(p)
