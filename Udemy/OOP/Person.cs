using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace OOP
{
    internal class Person
    {

        // This is a constructor
        // It is called when an instance of the class is created
        // It initializes the properties of the class
        // The constructor has the same name as the class
        // It does not have a return type
        // It can take parameters to initialize the properties
        // Example: public Car(string make, string model, int year)

        public static int nextId = 0;
        private readonly int _Id;

        public const int MaxAge = 120; // Constant for maximum age - this is static and cannot be changed. It is shared across all instances of the class. Compile-time constant.

        public readonly int MinAge = 0; // Readonly field for minimum age - this can only be set in the constructor and cannot be changed later. Runtime constant.

        public int Id
        {
            get => _Id;
        }

        private string _password;

        public string Password
        {
            set
            {
                if (value.Length >= 8)
                {
                    _password = value;
                }
                else
                {
                   Console.WriteLine("Password must be at least 8 characters long.");
                }
            }
        }
        public string FullName { get; set; }
        public int Age { get; set; }
        public string Address { get; set; }

        public long PhoneNumber { get; set; }

        // Constructor with parameters
        public Person(string fullName, int age, string address, long phoneNumber)
        {
            if (age < MinAge || age > MaxAge)
            {
                throw new ArgumentOutOfRangeException(nameof(age), $"Age must be between {MinAge} and {MaxAge}.");
            }
            _Id = nextId++;
            FullName = fullName;
            Age = age;
            Address = address;
            PhoneNumber = phoneNumber;
           
        }
       
        public Person(string fullName, int age)
        {
            _Id = nextId++;
            FullName = fullName;
            Age = age;
        }

        // Constructor with one parameter
        public Person(string fullName)
        {
            _Id = nextId++;
            FullName = fullName;
        }

   

        public Person(string fullName, long phoneNumber)
        {
            _Id = nextId++;
            FullName = fullName;
            PhoneNumber = phoneNumber;
        }


        public Person(long phoneNumber, string address)
        {
            _Id = nextId++;
            PhoneNumber = phoneNumber;
            Address = address;
        }



        // Default constructor

        public Person()
        {
            _Id = nextId++;
            FullName = "Unknown";
            Age = 0;
            Address = "Unknown";
            PhoneNumber = 0;
        }

        public void userInfo(string fullname, int age, string address, long phoneNumber)
        {

            FullName = fullname;
            Age = age;
            Address = address;
            PhoneNumber = phoneNumber;

            Console.WriteLine($"Name: {FullName}, Age: {Age}, Address: {Address}, Phone Number: {PhoneNumber}");
        }

        public void GetDetails()
        {
            Console.WriteLine($"ID: {_Id}, Name: {FullName}, Age: {Age}, Address: {Address}, Phone Number: {PhoneNumber} password : {_password}");
        }
    }


}
