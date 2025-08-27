namespace Training_Programming_c_sharp
{
    internal class Program
    {
        static void Main(string[] args)
        {
            List<Person> students = new List<Person>
            {
                new Person { Name = "Alice", Age = 22 },
                new Person { Name = "Bob", Age = 20 },
                new Person { Name = "Charlie", Age = 23 }
            };

            students.Sort(); // Sorts alphabetically by Name

            foreach (Person person in students)
            {

                Console.WriteLine(person.Name);
            }

        }
    }

    class Person : IComparable<Person>
    {

        private string _name;
        private int _age;

        public int Age
        {
            get { return _age; }
            set { _age = value; }
        }


        public string Name
        {
            get { return _name; }
            set { _name = value; }
        }

        public int CompareTo(Person? other)
        {
            if (other == null) return 1;
            if (other == this) return 0;
            return Age.CompareTo(other.Age);
        }  // This will use the Name property to compare
    }
}
