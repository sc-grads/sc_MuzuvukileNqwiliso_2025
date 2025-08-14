using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace c_sharp.Loops
{
    internal class Calculator
    {
        public Calculator() {
            Console.WriteLine("Welcome to My Calculator!!!");

            int currentScore = 0;
            int sum = 0;
            int counter = 0;
            do
            {
                Console.WriteLine("Enter you student scores");
                currentScore = int.Parse(Console.ReadLine());
                if (currentScore > 0)
                {
                    sum = sum + currentScore;
                }
                counter++;
            }while (currentScore > 0);

            int average = 0;
            average = sum / counter;
            Console.WriteLine("Your students average is {0}", average);
            Console.ReadKey(true);
        }
    }
}
