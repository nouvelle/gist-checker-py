def test_filter_string_values_in_dict_basic(submission_module):
    f = submission_module.filter_string_values_in_dict
    data = {"a": "apple", "b": 100, "c": "car", "d": True}
    assert f(data) == {"a": "apple", "c": "car"}

def test_filter_string_values_in_dict_empty(submission_module):
    f = submission_module.filter_string_values_in_dict
    assert f({"x": 10, "y": 20}) == {}
    assert f({}) == {}

def test_filter_string_values_in_dict_all_strings(submission_module):
    f = submission_module.filter_string_values_in_dict
    data = {"name": "Alice", "city": "Tokyo"}
    assert f(data) == data
