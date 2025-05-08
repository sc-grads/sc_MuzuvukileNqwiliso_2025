def func(a) :
    print(f'This is a {a} parameter from the function...')

func(56)

def func_2():
    print('This is a function with no parameters...')

func_2()

def func_3(a: int, b: int) -> int:
    sum: int = a + b
    return sum

def func_4(func):
    result = func(4, 6)  
    mult = 3 * result
    print('This is the function inside another function...')
    print(f'This is the multiplication {mult} done with the sum of the parameter func')

func_4(func_3)

def add(a, b):
    return a + b  

result = add(5, 3)
print(result)  


def future_function():
    pass  

def show_names(*args):
    for name in args:
        print(name)

show_names("Mzu", "Alex", "Sam")


def show_info(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")

show_info(name="Mzu", age=25, location="Cape Town")
