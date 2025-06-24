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
