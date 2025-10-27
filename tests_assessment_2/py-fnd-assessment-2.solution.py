def filter_string_values_in_dict(dict):
    result = {}
    for key in dict:
        if type(dict[key]) is str:
            result[key] = dict[key]
    return result


def filter_string_values_dict_in_list(listOfDicts):
    result = []
    for dict in listOfDicts:
        result.append(filter_string_values_in_dict(dict))
    return result

def convert_to_length_tuple(strings):
    return list(map(lambda s: (s, len(s)), strings))

# for loop での実装例（今回のアセスメントでは非推奨のコード）
# def convert_to_length_tuple(listOfStrings):
#     result = []
#     for word in listOfStrings:
#         result.append((word, len(word)))
#     return result


def get_even_numbers_from_input():
    line = input()
    parts = line.split(",")
    result = []
    for part in parts:
        part = part.strip()
        if part != "":
            num = int(part)
            if num % 2 == 0:
                result.append(num)
    return result
