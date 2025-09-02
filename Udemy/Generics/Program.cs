namespace Generics
{
    internal class Program
    {
        static void Main(string[] args)
        {
            Box<string> box = new Box<string>("Hello, Generics!");
            Console.WriteLine(box.GetContent());
            Console.WriteLine();
            box.UpdadteContent("Updated Content");
            Console.WriteLine(box.GetContent());

            Console.WriteLine();

            Repo<User> userRepo = new Repo<User>();
            //userRepo.Add(new User { Id = 1, Name = "Alice" });
            //userRepo.Add(new User { Id = 2, Name = "Bob" });
            //User user = userRepo.GetById(1);
            //Console.WriteLine($"User ID: {user.Id}, Name: {user.Name}");

            Console.WriteLine();
            Program program = new();
            Program program1 = new();
            Console.WriteLine(AreEqual(program, program1)); // false because they are different instances

            Console.WriteLine();

            Product product = new Product();
            product = new Product { Id = 1, Name = "Laptop" };
            ProductRepo productRepo = new ProductRepo();
            productRepo.Add(product);
            Product fetchedProduct = productRepo.GetById(1);
            Console.WriteLine($"Product ID: {fetchedProduct.Id}, Name: {fetchedProduct.Name}");

            Console.WriteLine();

            Action<int> action = (x)=> Console.WriteLine($"Action called with {x}"); // Action is a delegate that takes a parameter and returns void
            action(5);
            Func<int, int, int> func = (x, y) => x + y; // Func is a delegate that takes parameters and returns a value, The first n-1 parameters are the input parameters and the last parameter is the return type
            int result = func(3, 4);
            Console.WriteLine($"Func result: {result}");
            Predicate<int> isOdd = (x) => x%2 != 0; // Predicate is a delegate that takes a parameter and returns a boolean

            List<int> numbers = [1,2,33,4,5,6,8];

           foreach(var number in numbers.FindAll(isOdd)) // FindAll is a method that takes a predicate and returns a list of all the elements that match the predicate
            {
                Console.WriteLine($"Predicate matched: {number}");
            }
          

        }

        public void GenericMethod<T>(T parameter) // The T in parenthesis is a placeholder for any data type and is referencing the T in angle brackets next to the method name
                                                  // if the method name doesn't not gave the T next to it, you can not use the T in the method body
        {
            Console.WriteLine($"Parameter type: {typeof(T)}, Value: {parameter}");
        }

        public static bool AreEqual<T>(T a, T b) where T : class// This is a generic method that takes two parameters of the same type and returns true if they are equal
        {
            return EqualityComparer<T>.Default.Equals(a, b);
        }


    }

    class Box<T>(T content)
    {
        public T Content = content;

        public void UpdadteContent(T newContent)
        {
            Content = newContent;
        }

        public T GetContent()
        {
            return Content;
        }

    }

    class Box2<T1, T2>(T1 content1, T2 content2)
    {
        public T1 Content1 = content1;
        public T2 Content2 = content2;
        public void UpdateContents(T1 newContent1, T2 newContent2)
        {
            Content1 = newContent1;
            Content2 = newContent2;
        }
        public (T1, T2) GetContents()
        {
            return (Content1, Content2);
        }
    }

    class Box3<T>
    {
        // In order for you to use a generic type, you must make sure it have a reference type constraint where T 

        public T Content;
    }


    class Human<T> where T : class // This means that T must be a reference type
    {
        public T FirstName { get; set; }
        public T LastName { get; set; }
        public Human(T firstName, T lastName)
        {
            FirstName = firstName;
            LastName = lastName;
        }
    }




    class Repo<T> where T : IEntity // This means that T must implement the IEntity interface
    {
        private List<T> entities = new List<T>();
        public void Add(T entity)
        {
            entities.Add(entity);
        }
        public void Remove(T entity)
        {
            entities.Remove(entity);
        }
        public T GetById(int id)
        {
            return entities.FirstOrDefault(e => e.Id == id);
        }
        public List<T> GetAll()
        {
            return entities;
        }
    }

    interface IEntity
    {
        int Id { get; set; }
    }


    class User : IEntity
    {
        public int Id { get; set; }

    }


    interface IRepository<T> where T : IEntity
    {
        void Add(T entity);
        void Remove(T entity);
        T GetById(int id);
        List<T> GetAll();

    }


    class Product : IEntity
    {
        public int Id { get; set; }

        public string Name { get; set; }    
    }

    class ProductRepo : IRepository<Product>
    {

        private List<Product> products = new();

        public void Add(Product entity)
        {
            products.Add(entity);
        }

        public List<Product> GetAll()
        {
            return products;
        }

        public Product GetById(int id)
        {
            return products.FirstOrDefault(p => p.Id == id);
        }

        public void Remove(Product entity)
        {
            products.Remove(entity);
        }
    }

}
