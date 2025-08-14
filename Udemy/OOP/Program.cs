namespace OOP
{
    internal class Program
    {
        static void Main(string[] args)
        {
            // Create an instance of the class  
           Person person1= new Person("John Doe", 30, "123 Main St", 1234567890);
           Person person2 = new Person("Jane Smith", 25, "456 Elm St", 9876543210);
           Person person3 = new Person("Alice Johnson", 28);
           Person person4 = new Person(9876543210, "789 Oak St");

            Person person = new Person();

            Console.WriteLine("What is your Fullname ? ");
            person.FullName = Console.ReadLine();
            Console.WriteLine("What is your Age ? ");
            person.Age = int.Parse(Console.ReadLine());
            Console.WriteLine("What is your Address ? ");
            person.Address = Console.ReadLine();
            Console.WriteLine("What is your Phone Number ? ");
            person.PhoneNumber = long.Parse(Console.ReadLine());
            Console.WriteLine("\nPerson Details:");
            Console.WriteLine($"Full Name: {person.FullName}");
            Console.WriteLine($"Age: {person.Age}");
            Console.WriteLine($"Address: {person.Address}");
            Console.WriteLine($"Phone Number: {person.PhoneNumber}");



            Console.WriteLine("Press any key t close the window...");
            Console.ReadKey();  
        }
    }
}
