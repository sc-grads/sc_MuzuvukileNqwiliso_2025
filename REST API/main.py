var = input('Enter Value: ')
print(var)
num = float(input('Enter number : '))
print(f'This is a number {num:.2f}')

# set, list , dictionary 
num_list = sorted([1,4,5,6],reverse=True)
for num in num_list:
    print(num,end=',')

num_set = {1, 20, 45, 3}
print(type(num_set))
print(num_set)
print(dir(num_set))

num_set.add(7)
num_set.remove(20)
num_set.clear()
print(num_set)

num_list = 10  #
for num in range(num_list):
    num_set.add(num)

for value in num_set:
    print(value, end=' ')


for value in range(num_set):
    print(value, end=' ')

# comparisons and booleans
print(4 > 4)
print(4 == 4)
print(10 != 50)

isPreg = True
if isPreg :
    print("Yes, it's preg...")
else:
    print("It's not preg...")

# if statements

dayOfWeek = input('What is the day of the week? ').capitalize()

if dayOfWeek == 'Monday':
    print("It's Monday.")
elif dayOfWeek == 'Tuesday':
    print("It's tuesday.")
else:
    print("Go wild.")


# alternative
match dayOfWeek:
    case 'Monday':
        print('It\'s Monday')
    case _:
        print('Not valid day!')

answer = input('Would you like you play if yes type (Y/N): \n').upper()
number = 8
match answer:
    case 'Y':
        user_number = int(input('Guess our number: '))
        if user_number == 8 : 
            print('Yey!!!, you got it right.')
        else:
            print('Naah, you did\'t got is right. Try again... ')
    case _:
        print('I hope we will play next time...')

answer = input('Would you like you play if yes type (Y/N): \n').upper()
number = 8
while answer != 'N':
    match answer:
        case 'Y':
            user_number = int(input('Guess our number: '))
            if user_number == 8 : 
                print('Yey!!!, you got it right.')
            else:
                print('Naah, you did\'t got is right. Try again... ')
        case _:
            print('I hope we will play next time...')
    answer = input('Would you like you play if yes type (Y/N): \n').upper()    
    

grades = [23, 40, 60, 80]
for i in range(len(grades)):
    print(grades[i], end='%' + '\n')
    if grades[i] == 80:
        print('Yey!!! you got a distinction.')
    elif grades[i] == 60:
        print('You tried your best.')
    else:
        print('you must work.')


# even numbers 
# -- Part 1 --
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9]

evens = []
for number in numbers:
    if number%2 == 0:
         evens.append(number)

# list comprehension newlist = [expression for item in iterable if condition == True]
random_numbers = [2,501,55,64,2,45,66]
even_numbers = [even for even in random_numbers if even % 2 == 0]
print(even_numbers)


# dictionary 
list_friends = [{"name":"Bob", "age":21}, {"name":"Malinda", "age":23}]
length = len(list_friends)
while length >=1 :
    print("My name is "+list_friends[length-1]["name"] + " I am "+str(list_friends[length-1]["age"])+" years old.")
    length -=1

list_friends = [{"name":"Bob", "age":21}, {"name":"Malinda", "age":23}]
for friend in list_friends:
    print(friend.get("name"))

list_friends = [{"name":"Bob", "age":21}, {"name":"Malinda", "age":23}]
for friend in list_friends: 
    print(friend.keys())

list_friends = [{"name":"Bob", "age":21}, {"name":"Malinda", "age":23}]
for friend in list_friends: 
    print(friend.values())

list_friends = [{"name":"Bob", "age":21}, {"name":"Malinda", "age":23}]
for friend in list_friends:
    friend.values()

# distructuring 
my_tuple = 1,2,5
print(my_tuple)

my_tuple = 1,2,5
one, two, five = my_tuple
print(one)
print(two)
print(five)

my_friends = [("Anele",23),("Fezile",30)]
for name, age in my_friends:
    print(f"My name is {name} "+" I am {age} year old." )

# function
def user_func() :
    print("Hello I am a function...")

user_func()

def user_func(name, age) : # parameters 
    user_name = name
    user_age = age
    print(f'Hello 😊, My name is {user_name}, I am {user_age} year old.')

user_func('Malinda',23) # arguments
user_func(name= 'Lindo',age =29) # arguments


def user_func(name ='Uknown', age = 0) : # parameters 
    user_name = name
    user_age = age
    if user_name ==  'Uknown' or age == 0:
        print('Please provide user details.')
    else: 
        print(f'Hello 😊, My name is {user_name}, I am {user_age} year old.')

user_func(name= 'Siya', age = 23)

def user_func(name ='Uknown', age = 0) -> str : # parameters 
    user_name = name
    user_age = age
    if user_name ==  'Uknown' or age == 0:
       return 'Please provide user details 😁.'
    else: 
        return f'Hello 😊, My name is {user_name}, I am {user_age} year old.'
    
message = user_func(name= 'Siya', age = 0)
print(message)

#lambda arguments : expression
add = lambda a : a + 4 # This is a function
print(add(14))
multiply = lambda a : a * 20
print(multiply(20))
devide = lambda a, b : b / a
print(devide(6,0))
devide = lambda a, b : b // a
print(devide(6,0))
power = lambda a, b : b ** a
print(power(6,4))
print_me = lambda a : print(a)
print_me(1)

# dictionary comprehensive 
users [
    (0, "Malinda", "malindapass"),
    (1,"Siza","sizapass")
]


# exercise
students = [
    {
        "name": "Jose",
        "school": "Computing",
        "grades": (66, 77, 88)
    },
    {
        "name": "Malinda",
        "school": "Engineering",
        "grades": (75, 80, 90)
    },
    {
        "name": "Siza",
        "school": "Mathematics",
        "grades": (60, 65, 70)
    },
    {
        "name": "Anele",
        "school": "Science",
        "grades": (85, 87, 90)
    },
    {
        "name": "Fezile",
        "school": "Arts",
         "grades": (72, 78, 80)

    }
]
# Assume the argument, data, is a dictionary.
# Modify the grades variable so it accesses the 'grades' key of the data dictionary.
def average_grade(data):
    grades =  [grade for grade in data["grades"]]
    return sum(grades) / len(grades)
 

def average_grade_all_students(student_list):
    total = 0
    count = 0
    for student in student_list:
        grades = student["grades"]
        total += sum(grades)
        count += len(grades)
    return total / count if count != 0 else 0

print(average_grade_all_students(students))


# unpacking parameters 
def multiply(*args): # arguments
    print(*args)
    results = 1
    for arg in args:
        results *= arg
    return results

def add(*args): # arguments
    print(*args)
    results = 0
    for arg in args:
        results += arg
    return results

def minus(*args): # arguments
    print(*args)
    results = 100
    for arg in args:
        results -= arg
    return results


def calculator(*args, oparator):
    match oparator :
        case '*':
            return f'Multiply results : { multiply(*args)}'
        case '+':
            return f'Add results : {add(*args)}'
        case '-':
            return f'Minus results : {minus(*args)}'
        case _:
            return "Enter a valid operator😥."
        
results = calculator(2,4,6,8,10,oparator= '+')
print(results)


