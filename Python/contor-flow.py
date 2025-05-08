num_1: int = 0
num_1 = int(input('Enter num 1: '))
if num_1 >= 9 :
    print('Num_1 is is greater or equal to 9')
else:
    print('Num_1 is not greater than or equal to 9')


if num_1 != 9  : 
    print('Num 1 is not equal to 9')
elif num_1 > 9 :
    print('Num 1 is greater than 9')
else :
    print('Num 1 is less than 9') 
  

enter_name = input('What is you name?')
name = 'Luigi' if enter_name == 'Luigi' else 'Mario'
print(f'My name is {name}')