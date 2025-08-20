namespace Struct
{
    public struct Point
    {
        //public int X; // I made them to be fields instead of properties so that they can be initialized directly
        //public int Y;

        public int X;
        public int Y { get; } // Making Y read-only property
        public Point(int x, int y)
        {
            X = x;
            Y = y;
        }
        public void Display()
        {
            Console.WriteLine($"Point: ({X}, {Y})");
        }
    }

    public class Pointer
    {
        public int X;
        public int Y { get; } // Making Y read-only property
        public Pointer(int x, int y)
        {
            X = x;
            Y = y;
        }
        public void Display()
        {
            Console.WriteLine($"Pointer: ({X}, {Y})");
        }
    }

    enum Color
    {
        Red,
        Green,
        Blue
    }

    internal class Program
    {
        static void Main(string[] args)
        {
            Point point = new Point(20, 10);
            point.Display();
            Point p1 = new Point(23, 56); // Uninitialized struct
            p1.Display(); // Displaying the values of p1

            point.X = 100; // This line will cause a compile-time error because X is read-only
            p1.X = 200; // This line will also cause a compile-time error because X is read-only

            point.Display(); // Displaying the values of point after trying to modify X
            p1.Display(); // Displaying the values of p1 after trying to modify X

            Pointer pointer = new Pointer(30, 40);
            pointer.X = 300;
            Pointer p2 = pointer;
            p2.X = 400; // This line will not cause a compile-time error because X is a field in a class, not a read
            pointer.Display(); // Displaying the values of pointer after modifying X
            p2.Display(); // Displaying the values of p2 after modifying X

            Color color_red = Color.Red; // This line will cause a compile-time error because Color is an enum, not a variable
            Color color_green = Color.Green; // This line will also cause a compile-time error because Color is an enum, not a variable
            Color color_blue = Color.Blue; // This line will also cause a compile-time error because Color is an enum, not a variable
            Console.WriteLine($"Color: {color_red}"); // Displaying the value of color_red

            Console.WriteLine(((int)color_red));
            Console.WriteLine(((int)color_blue));

            Program program = new Program();


            DateTime current = new DateTime(2023, 10, 1, 12, 0, 0);
            TimeSpan results = current.Subtract(DateTime.Now); // Subtracting 1 hour from the current DateTime

            DateTime now = DateTime.Now; // Current local date and time
            DateTime utcNow = DateTime.UtcNow; // Current UTC date and time
            DateTime today = DateTime.Today; // Today's date, time set to 00:00:00
            DateTime specific = new DateTime(2023, 10, 1, 12, 0, 0); // Year, Month, Day, Hour, Minute, Second

            Console.WriteLine("What is your date of birth?");
            DateTime birthDate = DateTime.Parse(Console.ReadLine() ?? "");
            int age = DateTime.Now.Year - birthDate.Year;
            Console.WriteLine($"You are {age} years old.");
            Console.WriteLine("So next year you will be: {0}",program.NextYearAge(age));
        }

        public DateTime GetCurrentDateTime()
        {
            return DateTime.Now; // Returns the current local date and time
        }

        public int NextYearAge(int age)
        {
            return  age + 1; // Returns the date of the next birthday
        }
    }


    
}
