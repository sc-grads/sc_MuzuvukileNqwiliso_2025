class Student: 
    def __init__(self,name, *grades):
        self.name = name
        self.grades = grades

    def average(self):
        return sum(self.grades) / len(self.grades)
    
student1 = Student('Malinda', 30,50,80,100)
student2 = Student('Sihle', 80,50,80,100)
print(student1.name)
print(student1.average())
print(student2.name)
print(student2.average())


class Store:
    def __init__(self, name):
        self.name = name
        self.items = []

    def add_item(self, name, price):
        # Use the method arguments, not self.name/self.price
        self.items.append({"name": name, "price": price})

    def stock_price(self):
        # Sum all item prices in self.items
        return sum(item["price"] for item in self.items)

store = Store('Shesha')
store.add_item("Relay", 500)
store.add_item("Cable", 200)
print(store.items)           # [{'name': 'Relay', 'price': 500}, {'name': 'Cable', 'price': 200}]
print(store.stock_price())  


for item in store.items:
    print(item["name"])

# static and class methods
class Book:
    TYPES = ("hardcover","paperback")
    def __init__(self,name,book_type,weight):
        self.name  = name
        self.book_type = book_type
        self.weight = weight

    def __repr__(self):
        return f"<Book({self.name}, {self.book_type}, {self.weight})>"
        
    @classmethod
    def hardcover(cls,name,weight):
        return cls(name, cls.TYPES[0],weight+100) # this is referencing to the class Book
    
    @classmethod
    def paperback(cls,name,weight):
        return cls(name,cls.TYPES[1],weight)

    @staticmethod
    def my_staticMethod():
        pass

book = Book.hardcover("Harry Potter",4000)

print(book.name)


class Store:
    def __init__(self, name):
        self.name = name
        self.items = []

    def add_item(self, name, price):
        self.items.append({
            'name': name,
            'price': price
        })

    def stock_price(self):
        total = 0
        for item in self.items:
            total += item['price']
        return total

    @classmethod
    def franchise(cls, store):
        return (store.name +  " - franchise")
        # Return another store, with the same name as the argument's name, plus " - franchise"

    @staticmethod
    def store_details(store):
        # Return a string representing the argument
        return f"{store.name}, total stock price: {store.stock_price()}"
        # It should be in the format 'NAME, total stock price: TOTAL'


store = Store("Test")
store2 = Store("Amazon")
store2.add_item("Keyboard", 160)
 
print(Store.franchise(store))  # returns a Store with name "Test - franchise"
print(Store.franchise(store2))  # returns a Store with name "Amazon - franchise"
 
print(Store.store_details(store))  # returns "Test, total stock price: 0"
print(Store.store_details(store2) ) # returns "Amazon, total stock price: 160"


# inheritance
class Person :
    def  __init__(self, name, age, height):
        self.name = name
        self.age = age
        self.height = height

    def greet(self):
        return f"Hello, my name is {self.name}."

    def is_adult(self):
        return self.age >= 18

    def grow_older(self, years=1):
        self.age += years
        return self.age

    def info(self):
        return f"Name: {self.name}, Age: {self.age},Height: {self.height}cm"
    
class Student(Person):
    def __init__(self, name, age, height, course):
        super().__init__(name, age, height)
        self.course = course

    def student_info(self):
        return f"{self.name} is enrolled in {self.course}."

    def info(self):
        return f"Name: {self.name}, Age: {self.age}, Height: {self.height}cm, Course:  {self.course}"
    
student_a = Student("Malinda", 21, 170, "Computer Science")
student_b = Student("Sihle", 22, 165, "Mathematics")
student_c = Student("Anele", 20, 172, "Engineering")
student_d = Student("Fezile", 23, 168, "Physics")
student_e = Student("Siza", 19, 175, "Chemistry")

print(student_a.info())
print(student_b.info())
print(student_c.info())
print(student_d.info())
print(student_e.info())


from my_module import greet
# main.py
import tools


# main.py
from tools import greet, add

import tools as t

greet_message = greet("Malinda")
print(greet_message)


print(tools.greet("Mzu"))
print("Version:", tools.version)
print("Sum:", tools.add(5, 3))
print("Users:", tools.users)
print("Config:", tools.config)



print(greet("Thabo"))
print("Addition:", add(10, 7))


print(t.greet("Lerato"))
print("Config theme:", t.config["theme"])
