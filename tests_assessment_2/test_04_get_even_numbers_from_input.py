import builtins

def test_get_even_numbers_from_input_simple(submission_module, monkeypatch):
    f = submission_module.get_even_numbers_from_input
    monkeypatch.setattr(builtins, "input", lambda: "1,2,3,4,5,6")
    assert f() == [2, 4, 6]

def test_get_even_numbers_from_input_with_spaces(submission_module, monkeypatch):
    f = submission_module.get_even_numbers_from_input
    monkeypatch.setattr(builtins, "input", lambda: " 10 , 15 , 20 , 25 ")
    assert f() == [10, 20]

def test_get_even_numbers_from_input_no_even(submission_module, monkeypatch):
    f = submission_module.get_even_numbers_from_input
    monkeypatch.setattr(builtins, "input", lambda: "1,3,5,7")
    assert f() == []
