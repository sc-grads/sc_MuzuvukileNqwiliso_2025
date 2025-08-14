using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection.Metadata.Ecma335;
using System.Text;
using System.Threading.Tasks;

namespace c_sharp.Methods
{
    internal class Methods
    {
        public Methods() { }
        // parameter modifiers 
        // ref
       public  int MethodValue(ref int number) // this is a REF method
        {
            number = 100;
            return number;
        }


        public int MethodParameter(out int number) // this is a OUT  method
        {
            number = 2004; 
            return number;
        }


        public void MethodParamter2(in int number) // this is a IN method
        {
            Console.WriteLine(number);
        }

    }
}
