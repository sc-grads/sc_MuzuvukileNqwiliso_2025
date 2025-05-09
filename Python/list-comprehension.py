"""[expression for item in iterable]"""

addition = [i+i+1 for i in [4,6,7]]

squares = [x*x for x in range(5)]
print(squares)
print(addition)

names = ["mzu", "nqwiliso"]
upper_names = [name.upper() for name in names]

print(upper_names)
lower_names = [name.lower() for name in names]
print(lower_names)