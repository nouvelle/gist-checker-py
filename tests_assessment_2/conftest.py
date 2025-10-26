import ast
import pathlib
import types
import sys
import pytest

def _safe_import_submission(path: pathlib.Path):
    """
    提出物 submission.py を安全にインポートする。
    トップレベル実行文は無視して関数定義などだけ評価。
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
    path = pathlib.Path.cwd() / "submission.py"
    if not path.exists():
        pytest.skip("submission.py が見つかりません")
    return _safe_import_submission(path)
