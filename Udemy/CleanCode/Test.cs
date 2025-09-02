using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CleanCode
{
    /// <summary>
    /// Represents a customer with ID and first name. from the base class
    /// </summary>

    internal class Test : Customer
    {
        public void Display()
        {
            Console.WriteLine("Test class");
            Console.WriteLine($"Customer ID: {CustomerId}, First Name: {FirstName}");
        }



        public Test(int customerId, string firstName) : base(customerId, firstName)
        {
           Console.WriteLine("Test class constructor called");
        }
    }
}
