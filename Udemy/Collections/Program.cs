namespace Collections
{
    internal class Program
    {
        static void Main(string[] args)
        {



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



           

            var myNumbers = new List<int> {1,2,3,4,5,6,7,8,15,25};

            Console.WriteLine("Predicates  numbers");
            Predicate<int> isEven = n => n % 2 == 0;
            List<int> evenNumbers = myNumbers.FindAll(isEven);
            List<int> oddNumbers = myNumbers.FindAll(n => n % 2 != 0);
            int firstEvenNumber = myNumbers.Find(n=> n % 2 == 0); // you must declare a varaiable as a type not as a List <int> because Find returns a single item compared to FindAll which returns a List of items

            int isTwo = myNumbers.Find(n => n == 2);
            
            Console.WriteLine("Number 2 is found "+ isTwo);

            Console.WriteLine("Even numbers:");
            Console.Write("even numbers => ");

            bool largeTtwenty = myNumbers.Any(n => n > 20);

            

            foreach (var number in evenNumbers)
            {
                 Console.Write(number + " ");
            }
            Console.WriteLine();
            Console.Write("odd numbers => ");
            foreach (var oddNumber in  oddNumbers)
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

        }
    }
}
