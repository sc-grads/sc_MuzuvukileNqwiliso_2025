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