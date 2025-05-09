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



class Book:
    def __init__(self, title, pages):
        self.title = title
        self.pages = pages

    def __str__(self):
        return f"'{self.title}' has {self.pages} pages."

book1 = Book("Python Basics", 250)
print(book1) 


def greet(name):
    return f"Hello, {name}!"

print(greet("Mzu"))

class Person:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hi, I’m {self.name}."

p1 = Person("Mzu")
print(p1.greet()) 


class Animal:
    def speak(self):
        print("This animal makes a sound.")

class Dog(Animal): 
    def bark(self):
        print("Woof!")




class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        print(f"{self.name} makes a sound.")

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)  
        self.breed = breed

    def speak(self):
        super().speak() 
        print(f"{self.name} barks. It's a {self.breed}.")


class MathOperations:
    @staticmethod
    def add(x, y):
        return x + y

print(MathOperations.add(5, 3)) 


class Car:
    wheels = 4

    @classmethod
    def change_wheels(cls, number_of_wheels):
        cls.wheels = number_of_wheels

Car.change_wheels(6)
print(Car.wheels)  


from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        print("Woof!")

class Cat(Animal):
    def speak(self):
        print("Meow!")

dog = Dog()
dog.speak()

def greet(name, callback):
    print(f"Hello, {name}!")
    callback()  

def say_goodbye():
    print("Goodbye!")

greet("Mzu", say_goodbye)



