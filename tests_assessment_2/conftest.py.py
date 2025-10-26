# 安全に submission.py を読み込むための簡易版 conftest
import ast
import pathlib
import types
import sys
import pytest

def _safe_import_submission(path: pathlib.Path):
    """
    提出物 submission.py を『安全インポート』する。
    - トップレベル実行文（関数呼び出し・print 等）は無視
    - Import / ImportFrom / FunctionDef / ClassDef のみ評価対象
    """
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))

    kept = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef)):
            kept.append(node)
    new_mod = ast.Module(body=kept, type_ignores=[])
    code = compile(new_mod, str(path), "exec")

    module = types.ModuleType("submission")
    module.__file__ = str(path)
    sys.modules["submission"] = module
    exec(code, module.__dict__)
    return module

@pytest.fixture(scope="session")
def submission_module():
    p = pathlib.Path.cwd() / "submission.py"
    if not p.exists():
        pytest.skip("submission.py が見つかりません")
    return _safe_import_submission(p)
