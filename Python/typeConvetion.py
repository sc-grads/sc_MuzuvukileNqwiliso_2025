# Type convertion is the way of convecting one type to another type
num_1 : int = 1
print(type(num_1))
num_2 : float = float(num_1)
print(type(num_2))

""" With this you are also able to convert a number that it's in str type to float or int """
str_num = '100.87'
print(type(str_num))
float_num : float = float(str_num)
print(type(str_num))
print(round(float_num ** 23),2)