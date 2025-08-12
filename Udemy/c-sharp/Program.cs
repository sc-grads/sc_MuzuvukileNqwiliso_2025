using System;

class Program
{
    static void Main(string[] args)
    {
        bool hasDegree = false;
        bool hasExperience = true;

        // AND both conditions must be true
        // OR at least one condition must be true
        // NOT negates the condition
        // XOR exclusive OR, one must be true but not both

        Console.WriteLine("This is going to display true -> {0}",!hasDegree);
        Console.WriteLine("This is going to display false -> {0}",hasDegree);

        if (hasDegree || hasExperience)
        {
            Console.WriteLine("You are qualified for the job.");
        }else
        {
            Console.WriteLine("You are not qualified for the job.");
        }

       Console.WriteLine("Please enter your age: ");
        int age;
        Console.WriteLine();
        if(!int.TryParse(Console.ReadLine(), out age))
        {
            Console.WriteLine("Invalid input. Please enter a valid age.");
            return;
        }
        Console.WriteLine("You entered: " + age);
        if (age >= 18 && age < 65)
        {
            Console.WriteLine("You are eligible to work.");
        }
        else if (age < 18)
        {
            Console.WriteLine("You are too young to work.");
        }
        else if (age >= 65)
        {
            Console.WriteLine("You are not eligible to work.");
        }else
        {
            Console.WriteLine("Invalid age.");
        }


        Console.WriteLine("Do you like games?");
        if (Console.ReadLine().ToLower() == "yes")
        {
            string gameName;
            Console.WriteLine("What is your favorite game?");
            gameName = Console.ReadLine().ToLower();
            if (gameName == "God of War")
            {
                Console.WriteLine("You like God of War too!");
            }
            else if (gameName == "Call of Duty")
            {
                Console.WriteLine("You like The Call of Duty too!");
            }
            else
            {
                Console.WriteLine("You like " + gameName + " too!");
            }
        }
        else
        {
            Console.WriteLine("You don't like games.");
        }
        Console.WriteLine("Please enter a number between 1 and 2: ");
        int number;
        number = int.Parse(Console.ReadLine());
        switch (number)
        {
            case 1:
                Console.WriteLine("You entered one.");
                break;
            case 2:
                Console.WriteLine("You entered two");
                break;
            default:
                                Console.WriteLine("You entered a number other than one or two.");
                break;
        }

            Console.WriteLine("Press any key to exit...");
        Console.ReadKey();
    }


}
