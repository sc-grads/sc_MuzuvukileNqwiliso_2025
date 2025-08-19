using System;

namespace ErrorCatch
{
    internal class Program
    {
        static void Main(string[] args)
        {
            try
            {
                Console.WriteLine("Please enter your first whole number");
                int n1 = Convert.ToInt32(Console.ReadLine());
                Console.WriteLine("Please enter the second whole number");
                int n2 = Convert.ToInt32(Console.ReadLine());
                double results = (double)n1 / n2;
                Console.WriteLine($"The result of {n1} divided by {n2} is {results}");
            }
            catch (DivideByZeroException)
            {
                Console.WriteLine("You cannot divide by zero.");
            }
            catch (FormatException)
            {
                Console.WriteLine("Please enter valid whole numbers.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"An unexpected error occurred: {ex.Message}");
            }

            Console.WriteLine("Please enter your age:");
            try
            {
                PrintMessage(Console.ReadLine());
            }
            catch (ArgumentOutOfRangeException ex)
            {
                Console.WriteLine(ex.Message);
            }
            catch (FormatException ex)
            {
                Console.WriteLine(ex.Message);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"An unexpected error occurred: {ex.Message}");
            }
        }

        static void PrintMessage(string input)
        {
            if (int.TryParse(input, out int age))
            {
                if (age < 1 || age > 120)
                {
                    throw new ArgumentOutOfRangeException("Age must be between 1 and 120.");
                   
                }
                Console.WriteLine($"You entered the number: {age}");
            }
            else
            {
                throw new FormatException("Invalid input. Please enter a valid number.");
            }
        }
    }
}