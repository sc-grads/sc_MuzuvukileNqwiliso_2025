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
