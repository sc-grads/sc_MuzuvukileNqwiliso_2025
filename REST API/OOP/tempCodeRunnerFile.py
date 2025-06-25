class Book:
    TYPES = ("hardcover","paperback")
    def __init__(self,name,book_type,weight):
        self.name  = name
        self.book_type = book_type
        self.weight = weight

    def __repr__(self):
        return f"<Book({self.name} {self.book_type} {self.weight})>"
        

book = Book('Harry Potter',"Sciefy",1500)
print(book)