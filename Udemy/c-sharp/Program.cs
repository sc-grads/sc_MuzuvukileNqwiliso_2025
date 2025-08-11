using System;

class Program
{
    static void Main(string[] args)
    {
        //PrintUserName();

        // Below is the method to ask a user for their name
        //userinput();
        // Below is the method to perform a simple calculator operation
        //Calculator();

        //Console.WriteLine("Enter something!");
        //int num1 = 0;
        //Console.WriteLine($"Number :- {num1}");

        //Console.WriteLine("Enter a whole number: ");
        //int number = int.Parse(Console.ReadLine());
        //Console.WriteLine($"You entered: {number}");

        //Console.WriteLine("Enter your first descimal no : ");
        //double firumber = double.Parse(Console.ReadLine());
        //Console.WriteLine("Enter your second descimal no :");
        //double secondnumber = double.Parse(Console.ReadLine());
        //double sum = firumber + secondnumber;
        //Console.WriteLine($"Sum: {sum}");

        int intNum = 0;
        double doubleNum = 12.45;
        intNum = Convert.ToInt32(doubleNum); 
        Console.WriteLine(intNum);

        Console.ReadKey();
    }

    static void userinput()
    {
       
    }

    static void PrintUserName()
    {
        string name = "User";
        Console.WriteLine("Please enter your name:");
        string userName = Console.ReadLine();
        Console.WriteLine($"Hello, {name}!");
    }

    static void Calculator()
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
