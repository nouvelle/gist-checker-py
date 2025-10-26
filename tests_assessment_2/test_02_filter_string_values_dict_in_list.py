def test_filter_string_values_dict_in_list_basic(submission_module, monkeypatch):
    g = submission_module.filter_string_values_dict_in_list
    # helper を使っているかの簡易チェック（呼び出しをスパイ）
    called = {"value": False}
    real_helper = submission_module.filter_string_values_in_dict

    def spy(d):
        called["value"] = True
        return real_helper(d)

    # submission モジュール内の参照を書き換え
    monkeypatch.setattr(submission_module, "filter_string_values_in_dict", spy)

    data = [
        {"a": "apple", "b": 1},
        {"x": 10, "y": "yes"},
        {"k": None, "m": "moon"},
    ]
    expected = [
        {"a": "apple"},
        {"y": "yes"},
        {"m": "moon"},
    ]
    assert g(data) == expected
    assert called["value"], "filter_string_values_in_dict を内部で使ってください"

def test_filter_string_values_dict_in_list_returns_new_list(submission_module):
    g = submission_module.filter_string_values_dict_in_list
    src = [{"k": "v"}, {"n": "x"}]
    out = g(src)
    assert isinstance(out, list)
    assert all(isinstance(d, dict) for d in out)
    assert out is not src
