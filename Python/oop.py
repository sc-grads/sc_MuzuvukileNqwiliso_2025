class Person :
    def __init__(self):
        pass


class Employee: 
    def __init__(self,name,age,job):
        self.name = name
        self.age = age
        self.job = job

    def printInfo(self,name,age,job):
        print(f'My name is {name}')