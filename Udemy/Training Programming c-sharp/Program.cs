using System.Globalization;
using Training_Programming_c_sharp;

List<Student> studentList =
[
    new Student("Alice", 20, "S12345", "alice20", "password123"),
];

Console.WriteLine("Enter your username");
string inputUsername = Console.ReadLine();

Console.WriteLine(studentList[0].Username == inputUsername
    ? "Username is correct."
    : "Username is incorrect.");

Console.WriteLine("Enter your password");
string inputPassword = Console.ReadLine();

Console.WriteLine(studentList[0].VerifyPassword(inputPassword)
    ? "Password is correct."
    : "Password is incorrect.");

if (studentList[0].VerifyPassword(inputPassword) && studentList[0].Username == inputUsername)
{
    studentList[0].Introduce();
}

namespace Training_Programming_c_sharp
{
    interface IPerson
    {
        string Name { get; set; }
        int Age { get; set; }
        void Introduce();
    }

    class Student : IPerson
    {
        private string _password;

        public string Name { get; set; }
        public int Age { get; set; }
        public string StudentID { get; set; }
        public string Username { get; set; }

        public string Password
        {
            get => _password;
            set
            {
                if (value.Length < 8)
                {
                    Console.WriteLine("Password must be at least 8 characters long.");
                }
                else
                {
                    _password = value;
                }
            }
        }

        // Constructor
        public Student(string name, int age, string studentID, string username, string password)
        {
            Name = name;
            Age = age;
            StudentID = studentID;
            Username = username;
            Password = password; // will use the property validation
        }

        public void Introduce()
        {
            Console.WriteLine($"Hello, I'm {Name}, {Age} years old, and my student ID is {StudentID}.");
        }

        public string SetPassword(string pass)
        {
            if (pass.Length < 8)
            {
                return "Password must be at least 8 characters long.";
            }

            Password = pass;
            return "Password set successfully.";
        }

        public bool VerifyPassword(string pass) => pass == Password;
    }
}
