using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace OOP
{
    internal partial class SimpleCalculator
    {

        public int Add(int a, int b)
        {
            return a + b;
        }

       partial void Multiply(int a, int b);

        public void DoMultiply(int a, int b)
        {
            Multiply(a, b);
        }
    }

    internal partial class SimpleCalculator
    {
        public int Subtract(int a, int b)
        {
            return a - b;
        }

        partial void Multiply(int a, int b)
        {
            Console.WriteLine($"Multiplication result: {a * b}");
        }

    }

}
