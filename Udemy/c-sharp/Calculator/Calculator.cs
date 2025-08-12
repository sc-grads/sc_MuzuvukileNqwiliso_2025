using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace c_sharp.Calculator
{
    internal class Calculator
    {
        public void SimpleCalculator()
        {
            int num1, num2;
            double result = 0;
            char operation;

            Console.WriteLine("Enter first number:");
            num1 = Convert.ToInt32(Console.ReadLine());
            Console.WriteLine("Enter an operator (+, -, *, /):");
            operation = Console.ReadKey().KeyChar;
            Console.WriteLine(); // To move to the next line after reading the operator
            Console.WriteLine("Enter second number:");
            num2 = Convert.ToInt32(Console.ReadLine());

            if (operation == '+')
            {
                result = num1 + num2;
                Console.WriteLine($"Result: {result}");
            }
            else if (operation == '-')
            {
                result = num1 - num2;
                Console.WriteLine($"Result: {result}");
            }
            else if (operation == '*')
            {
                result = num1 * num2;
                Console.WriteLine($"Result: {result}");
            }
            else if (operation == '/')
            {
                if (num2 != 0)
                {
                    result = num1 / num2;
                    Console.WriteLine($"Result: {result}");
                }
                else
                {
                    Console.WriteLine("Error: Division by zero is not allowed.");
                }
            }
            else
            {
                Console.WriteLine("Error: Invalid operator.");
            }
        }
    }

   
}
