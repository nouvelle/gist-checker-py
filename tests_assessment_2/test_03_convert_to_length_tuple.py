def test_convert_to_length_tuple_basic(submission_module):
    f = submission_module.convert_to_length_tuple
    data = ["apple", "banana", "kiwi"]
    assert f(data) == [("apple", 5), ("banana", 6), ("kiwi", 4)]

def test_convert_to_length_tuple_various(submission_module):
    f = submission_module.convert_to_length_tuple
    data = ["", "a", "ab"]
    assert f(data) == [("",0),("a",1),("ab",2)]

def test_convert_to_length_tuple_empty(submission_module):
    f = submission_module.convert_to_length_tuple
    assert f([]) == []
