using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Schema;

namespace OOP
{
    internal class Car
    {
        // Properties of the Car class


        private string _model;
        private string _make;
        private int _year;

        public string Model {
            get
            {
                if (isLuxury)
                {
                    return "Luxury " + _model;
                } else
                {
                    return _model;
                }
            }
            set
            {
                if (string.IsNullOrEmpty(value))
                {
                    Console.WriteLine("Model cannot be empty or null.");
                }
                _model = value;
            }
        }
        public int Year { get => _year;
            set {
                if (value < 1886 || value > DateTime.Now.Year)
                {
                    Console.WriteLine("Year must be between 1886 and the current year.");
                }
                else
                {
                    _year = value;
                }
            }
        }

        public bool isLuxury { get; set; }
        public string Make { get => _make;
            set
            {
                if (string.IsNullOrEmpty(value))
                {
                    Console.WriteLine("Make cannot be empty or null.");
                }
                else
                {
                    _make = value;
                }

            }
        }

        public Car()
        {
            Model = "Default Model";
            Make = "Default Make";
            Year = DateTime.Now.Year;
        }

        public Car(string model, string make, int year, bool isLuxury = false)
        {
            Model = model;
            Make = make;
            Year = year;
            this.isLuxury = isLuxury;
        }

        public void Drive()
        {
            Console.WriteLine($"Driving a {Year} {Make} {Model}.");
        }

        public void Stop()
        {
            Console.WriteLine($"Stopping the {Year} {Make} {Model}.");
        }

        public void carInfo(string model, string make, int year)
        {
            Model = model;
            Make = make;
            Year = year;
            Console.WriteLine($"Car Info: {Year} {Make} {Model}");
        }

        public class InnerClass
        {
            public InnerClass()
            {
             Console.WriteLine("This is a inner class...");
            }

            public void InnerClassMethod()
            {
                Console.WriteLine("This is a inner class method....");
            }
        }

    }
}

   
