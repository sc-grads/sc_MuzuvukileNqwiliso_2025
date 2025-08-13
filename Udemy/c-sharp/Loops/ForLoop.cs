using System;
using System.Text;

namespace c_sharp.Loops
{
    internal class ForLoop
    {
        public void loopMethod()
        {
            // Countdown from 3 to 0, then launch rocket
            for (int i = 3; i >= 0; i--)
            {
                Console.WriteLine($"Current value of i: {i}");
                if (i == 0)
                {
                    Console.WriteLine(GenerateRocket(":)"));
                }
            }

            Console.WriteLine("Press any key to exit!");
            Console.ReadKey();
        }

        public static string GenerateRocket(string payload)
        {
            if (string.IsNullOrEmpty(payload))
                payload = " ";

            StringBuilder rocket = new StringBuilder();
            rocket.AppendLine("   /\\");
            rocket.AppendLine("  /  \\");
            rocket.AppendLine(" /____\\");
            foreach (char c in payload)
            {
                rocket.AppendLine($"|  {c}   |");
            }
            rocket.AppendLine(" \\____/");
            rocket.AppendLine("  /  \\");
            rocket.AppendLine(" VvV");
            return rocket.ToString();
        }

        public static void WhileLoop(int i)
        {
            Random random = new Random();
            int randomNumber = random.Next(1, 5);
           
            while (i != randomNumber )
            {
                Console.WriteLine($"Your number : {i} -> expected number : {randomNumber}");
                 Console.WriteLine("Please enter a new number:");
                if(int.TryParse(Console.ReadLine(), out i))
                {
                    if (i < randomNumber)
                    {
                        Console.WriteLine("Your number is too low.");
                    }
                    else if (i > randomNumber)
                    {
                        Console.WriteLine("Your number is too high.");
                    }
                    else
                    {
                        Console.WriteLine("Congratulations! You've guessed the number.");
                        break;
                    }
                }
                else
                {
                    Console.WriteLine("Invalid input. Please enter a valid number.");
                }
               

            }
        }
    }
}