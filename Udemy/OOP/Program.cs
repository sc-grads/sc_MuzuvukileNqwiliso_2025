using System;

namespace OOP
{
    internal class Program
    {
        static void Main(string[] args)
        {
            // Create an instance of the class  
            Person person1 = new Person("John Doe", 30, "123 Main St", 1234567890);
            Person person2 = new Person("Jane Smith", 25, "456 Elm St", 9876543210);
            Person person4 = new Person("Bob Brown", 35, "789 Oak St", 1122334455);
            Person person3 = new Person("Alice Johnson", 28);
            Car mustang = new Car();
            Car car2 = new Car("Model S", "Tesla", 2022, true);
            Car.InnerClass innerClass = new Car.InnerClass();
            mustang.Drive();
            mustang.Model = "Mustang GT";
            mustang.Make = "Ford";
            mustang.Year = 2023;
            mustang.isLuxury = true;
            mustang.carInfo(mustang.Model, mustang.Make, mustang.Year);
            innerClass.InnerClassMethod();
            person1.userInfo(person1.FullName, person1.Age, person1.Address, person1.PhoneNumber);
            person4.Password = "password123"; // Setting password for person4
            person4.GetDetails();
            person3.Password = "mypassword"; // Setting password for person3
            person3.GetDetails();
            person2.GetDetails();
            Console.WriteLine("Number of cars : {0}",Car.NumberOfCars);
            // partial class SimpleCalculator
            {
                SimpleCalculator calculator = new SimpleCalculator();
                int sum = calculator.Add(5, 10);
                int difference = calculator.Subtract(10, 5);
                Console.WriteLine($"Sum: {sum}, Difference: {difference}");
                calculator.DoMultiply(4, 5); // This will call the partial method Multiply
            }

            Console.WriteLine("This is an Id for person 2 "+person2.Id);
            person2.Password = "securepassword123"; 
            
        }
    }
}