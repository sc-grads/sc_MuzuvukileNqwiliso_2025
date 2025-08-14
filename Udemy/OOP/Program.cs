using System;

namespace OOP
{
    internal class Program
    {
        static void Main(string[] args)
        {
            // Create an instance of the class  
            Person person1 = new Person("John Doe", 30, "123 Main St", 1234567890);
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
            Console.WriteLine("Number of cars : {0}",Car.NumberOfCars);
            // partial class SimpleCalculator
            {
                SimpleCalculator calculator = new SimpleCalculator();
                int sum = calculator.Add(5, 10);
                int difference = calculator.Subtract(10, 5);
                Console.WriteLine($"Sum: {sum}, Difference: {difference}");
                calculator.DoMultiply(4, 5); // This will call the partial method Multiply
            }

        }
    }
}