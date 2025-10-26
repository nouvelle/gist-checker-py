def test_convert_to_length_tuple_basic(submission_module):
    f = submission_module.convert_to_length_tuple
    data = ["apple", "banana", "kiwi"]
    assert f(data) == [("apple", 5), ("banana", 6), ("kiwi", 4)]

def test_convert_to_length_tuple_empty(submission_module):
    f = submission_module.convert_to_length_tuple
    assert f([]) == []

def test_convert_to_length_tuple_various(submission_module):
    f = submission_module.convert_to_length_tuple
    data = ["A", "AB", "ABC", ""]
    assert f(data) == [("A", 1), ("AB", 2), ("ABC", 3), ("", 0)]
