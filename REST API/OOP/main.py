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