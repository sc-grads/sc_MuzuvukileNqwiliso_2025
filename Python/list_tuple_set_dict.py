""" these are types that hold a list of a structure """
list_nums: list[int] = [3,5,62,6]

print(list_nums.reverse)
print(list_nums.remove(3))
print(list_nums)

tuple_strings = ("Spong Bob","Luigi","Mario")
print(tuple_strings)
print(tuple_strings.count("Spong Bob"))
print(tuple_strings.index("Luigi"))

tuple_to_list: list[str] = list(tuple_strings)
print(type(tuple_to_list))
tuple_to_list.append("Ben 10")
list_to_tuple: tuple[str] = tuple(tuple_to_list)
print(list_to_tuple)