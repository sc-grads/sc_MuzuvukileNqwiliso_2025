using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace c_sharp.Loops
{
    public class ForLoop
    {

        public void loopMethod()
        {
            // For loop example
            for (int i = 0; i < 10; i++)
            {
                Console.WriteLine("Current value of i: " + i);
            }
            // Nested for loop example
            for (int i = 0; i < 5; i++)
            {
                for (int j = 0; j < 3; j++)
                {
                    Console.WriteLine($"i: {i}, j: {j}");
                }
            }
            // Using a for loop to iterate through an array
            string[] fruits = { "Apple", "Banana", "Cherry" };
            for (int i = 0; i < fruits.Length; i++)
            {
                Console.WriteLine("Fruit: " + fruits[i]);
            }
        }
    }

}
