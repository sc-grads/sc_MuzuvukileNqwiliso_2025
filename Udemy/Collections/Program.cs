using System.Collections;
using System.Reflection.Metadata;

namespace Collections

{

    public class Student {

        public string Name { get; set; } = String.Empty;
        public int Id { get; set; }
        public double Grade { get; set; }   

    }


    internal class Program
    {
        static void Main(string[] args)
        {

            //Name: John, Id: 1, Grade: 85
            //Name: Alice, Id: 2, Grade: 90
            //Name: Bob, Id: 3, Grade: 78

            var students5 = new Dictionary<string, Student>
            {
                ["John"] = new Student { Name = "John", Id = 1, Grade = 85 },
                ["Alice"] = new Student { Name = "Alice", Id = 2, Grade = 90 },
                ["Bob"] = new Student { Name = "Bob", Id = 3, Grade = 78 }
            };

            foreach (var student in students5)
            {
                Console.WriteLine($"Name: {student.Value.Name}, Id: {student.Value.Id}, Grade: {student.Value.Grade}");
            }


            Console.WriteLine();

            // Product list
            var products = new List<Product>
            {
                new Product { Name = "Apple", Price = 1.2m },
                new Product { Name = "Banana", Price = 0.8m },
                new Product { Name = "Cherry", Price = 2.5m }
            };

            foreach (var product in products)
            {
                Console.WriteLine($"Product: {product.Name}, Price: {product.Price:C}");
            }





            var myNumbers = new List<int> { 1, 2, 3, 4, 5, 6, 7, 8, 15, 25 };

            Console.WriteLine("Predicates  numbers");
            Predicate<int> isEven = n => n % 2 == 0;
            List<int> evenNumbers = myNumbers.FindAll(isEven);
            List<int> oddNumbers = myNumbers.FindAll(n => n % 2 != 0);
            int firstEvenNumber = myNumbers.Find(n => n % 2 == 0); // you must declare a varaiable as a type not as a List <int> because Find returns a single item compared to FindAll which returns a List of items

            int isTwo = myNumbers.Find(n => n == 2);

            Console.WriteLine("Number 2 is found " + isTwo);

            Console.WriteLine("Even numbers:");
            Console.Write("even numbers => ");

            bool largeTtwenty = myNumbers.Any(n => n > 20);



            foreach (var number in evenNumbers)
            {
                Console.Write(number + " ");
            }
            Console.WriteLine();
            Console.Write("odd numbers => ");
            foreach (var oddNumber in oddNumbers)
            {
                Console.Write(oddNumber + " ");
            }

            Console.WriteLine();
            if (largeTtwenty)
            {
                Console.WriteLine("There is a number larger than 20");
            }
            else
            {
                Console.WriteLine("There is no number larger than 20");
            }

            // using LINQ to filter and sort

            var filteredNumbers = myNumbers
                .Where(myNumbers => myNumbers > 10)
                .Order()
                .ToList();
            // this returns a list of numbers larger than 20 and sorts them in ascending order

            var numbersGreaterThanTen = myNumbers.Where(n => n > 10).OrderDescending().ToList();

            Console.WriteLine("Numbers greater than 10 in ascending order:");

            foreach (var number in numbersGreaterThanTen)
            {
                Console.WriteLine($"Numbers greater than 10 : {number}");
            }

            foreach (var number in filteredNumbers)
            {
                Console.WriteLine($"Filtered number: {number}");
            }


            Hashtable hashtable = new Hashtable();

            Dictionary<int, Student> studentDictionary = new Dictionary<int, Student>();

            // Adding students to the hashtable and dictionary
            studentDictionary.Add(1, new Student { Name = "Alice", Id = 1, Grade = 3.5 });
            studentDictionary.Add(2, new Student { Name = "Bob", Id = 2, Grade = 3.8});
            Console.WriteLine("Students in the dictionary:");
            foreach (var student in studentDictionary)
            {
                Console.WriteLine($"Student ID: {student.Key}, Name: {student.Value.Name}, Grade: {student.Value.Grade}");
            }
            Console.WriteLine();
            Student[] students = new Student[]
            {
                new Student { Name = "Alice", Id = 1, Grade = 3.5 },
                new Student { Name = "Bob", Id = 2, Grade = 3.8 },
                new Student { Name = "Charlie", Id = 3, Grade = 3.2 },
                new Student { Name = "David", Id = 4, Grade = 3.9 } 
            };

            foreach (var student in students)
            {
                hashtable.Add(student.Id, student);
            }
            Console.WriteLine();
            Console.WriteLine("Students in the hashtable: ");
            for (int i = 0; i < hashtable.Count; i++)
            {
                var student = (Student)hashtable[i + 1]; 
                Console.WriteLine($"Student ID: {student.Id}, Name: {student.Name}, Grade: {student.Grade}");
            }
            Console.WriteLine();
            Console.WriteLine("Students in the hashtable: in Dictionary ");

            foreach (DictionaryEntry entry in hashtable)
            {
                var student = (Student)entry.Value;
                Console.WriteLine($"ID: {entry.Key}, Name: {student.Name}, Grade: {student.Grade}");
            }
            Console.WriteLine();
            Console.WriteLine("Students in the array: ");

            foreach (var student in students)
            {
                Console.WriteLine($"Student Name: {student.Name}, ID: {student.Id}, Grade: {student.Grade}");
            }

            //Dictionary<int, User> users = new Dictionary<int, User>
            //{
            //    { 1, new User { Id = 1, Name = "James" } },
            //    { 2, new User { Id = 2, Name = "Lindo" } }
            //};


            //var users = new Dictionary<int, User>
            //{
            //    { 1, new User { Id = 1, Name = "James" } },
            //    { 2, new User { Id = 2, Name = "Lindo" } }
            //};

            var users = new Dictionary<int, User>
            {
                [1] = new User { Id = 1, Name = "James"},
                [2] = new User { Id = 2, Name = "Lindo"},
                [3] = new User { Id = 3, Name = "John"},
                [4] = new User { Id = 4, Name = "Jane" }   
            };  // This is a new way of initializing a dictionary in C# 9.0 and later 
            Console.WriteLine();
           foreach (var user in users)
            {
                Console.WriteLine("UserId : {0} , Fullname : {1}", user.Key, user.Value.Name);
            }

            Console.WriteLine();
            Console.WriteLine("Dummy data to practice");
            foreach (var user in users)
            {
                Console.WriteLine("UserId : {0} , Fullname : {1}", user.Key, user.Value.Name);
            }

            var valuesByKey = new Dictionary<string, List<int>>
            {
                ["Key1"] = new List<int> { 1, 2, 3 },
                ["Key2"] = new List<int> { 4, 5, 6 },
                ["Key3"] = new List<int> { 7, 8, 9 }
            };
            
            foreach (var kvp in valuesByKey)
            {
                Console.WriteLine($"{string.Join(" ", kvp.Value)} ");
            }
        }

    } 

    public class User
    {
        public int Id { get; set; }
        public string Name { get; set; }

    }

   
}
