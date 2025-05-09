print("Hello"  #  Missing closing bracket - Syntax error
      

print(age)  #  age is not defined yet

print("Age: " + 25)  #  can't add string and integer

num = int("hello")  # "hello" can't be turned into a number

colors = ["red", "blue"]
print(colors[5])  #  only 2 items exist


person = {"name": "Mzu"}
print(person["age"])  # ❌ no "age" key

print(10 / 0)  #  not allowed

try: 

except SomeError:


finally

try:
    result = 10 / 0
except ZeroDivisionError:
    print("You can't divide by zero!")
