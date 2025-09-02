

using LINQ;

int[] numbers = { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 };
var varsityManager = new VarsityManger();
varsityManager.DisplayVarsityHasMostStudents();
varsityManager.DisplayStudentsUnder20();

varsityManager.FemaleStudents();
Console.WriteLine();
varsityManager.MaleStdudents();

Console.ReadKey();

void OddNumber(int[] numbers)
{
    IEnumerable<int> oddNumbers = numbers.Where(n => n % 2 != 0);
    IEnumerable<int> oddNumbersQuery = from number in numbers where number % 2 != 0 select number;
    // from numbers select one number, then test if it's an odd number, if so, select it or return it store it on the ienumerable object varable
    // from number in number where number % 2 != 0 select number;

    Console.WriteLine("IEnumerable Object: ");
    Console.WriteLine(oddNumbers);

    Console.WriteLine("Odd Numbers:");

    foreach (var number in oddNumbers)
    {
        Console.Write(number + " ");
    }
    Console.WriteLine();
}

void EvenNumbers(int[] numbers)
{
    IEnumerable<int> evenNumbers = numbers.Where(n => n % 2 == 0);
    IEnumerable<int> evenNumbersQuery = from number in numbers where number % 2 == 0 select number;
    Console.WriteLine("Even Numbers:");
    foreach (var number in evenNumbers)
    {
        Console.Write(number + " ");
    }
}


namespace LINQ
{
    class VarsityManger
    {
        private readonly List<Varsity> Varsities;
        private readonly List<Student> Students;

        public VarsityManger()
        {
            Varsities = [];
            Students = [];

            Varsities.Add(new Varsity { Id = 1, Name = "Harvard University", Location = "Cambridge, MA" });
            Varsities.Add(new Varsity { Id = 2, Name = "Stanford University", Location = "Stanford, CA" });
            Varsities.Add(new Varsity { Id = 3, Name = "MIT", Location = "Cambridge, MA" });

            Students.Add(new Student { Id = 1, Name = "Alice", Age = 20, Gender = "Female", VarsityId = 1 });
            Students.Add(new Student { Id = 2, Name = "Bob", Age = 22, Gender = "Male", VarsityId = 1 });
            Students.Add(new Student { Id = 3, Name = "Charlie", Age = 21, Gender = "Male", VarsityId = 2 });
            Students.Add(new Student { Id = 4, Name = "Diana", Age = 23, Gender = "Female", VarsityId = 2 });
            Students.Add(new Student { Id = 5, Name = "Eva", Age = 19, Gender = "Female", VarsityId = 3 });
        }

        public void MaleStdudents()
        {
            var maleStudents = from student in Students where string.Equals(student.Gender, "male", StringComparison.OrdinalIgnoreCase) select student;
            Console.WriteLine("Male Stduents : ");
            foreach (var student in maleStudents)
            {
                Console.WriteLine($"{student.Name} is a male student.");
            }
        }

        public void FemaleStudents()
        {
            var femaleStudents = from student in Students where string.Equals(student.Gender, "female", StringComparison.OrdinalIgnoreCase) select student;
            Console.WriteLine("Female Students : ");
            foreach (var student in femaleStudents)
            {
                Console.WriteLine($"{student.Name} is a femal student.");

            }
        }


        public void DisplayStudentsUnder20()
        {
            var youStudents = from student in Students where student.Age < 20 select student;
            Console.WriteLine("Students under 20:");
            foreach (var student in youStudents)
            {

                if (string.Equals(student.Gender, "male", StringComparison.OrdinalIgnoreCase))
                    Console.WriteLine($"{student.Name} is young, he has {student.Age} year old.");
                else
                    Console.WriteLine($"{student.Name} is young, she has {student.Age} year old.");

            }
        }


        public void DisplayVarsityHasMostStudents()
        {
            var varsityStudentCounts = from student in Students
                                       group student by student.VarsityId into g
                                       select new
                                       {
                                           VarsityId = g.Key,
                                           StudentCount = g.Count()
                                       };

            int maxCount = varsityStudentCounts.Max(x => x.StudentCount);

            var varsitiesWithMostStudents = from varsityCount in varsityStudentCounts
                                            where varsityCount.StudentCount == maxCount
                                            join varsity in Varsities on varsityCount.VarsityId equals varsity.Id
                                            select varsity;

            Console.WriteLine("Varsity/Varsities with the most students:");
            foreach (var varsity in varsitiesWithMostStudents)
            {
                Console.WriteLine($"{varsity.Name} has {maxCount} students");
            }
        }

        public void SortStudentsByName()
        {
            var sortedStudents = from student in Students orderby student.Name select student;
            Console.WriteLine("Students sorted by name:");
            foreach (var student in sortedStudents)
            {
                Console.WriteLine(student.Name);
            }
        }
    }

}




class Student
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public int Age { get; set; }

        public string Gender { get; set; }

        public int VarsityId { get; set; }

        public void Display()
        {
            Console.WriteLine($"Id: {Id}, Name: {Name}, studying at VarsityId: {VarsityId}");
        }

    }

    class Varsity
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Location { get; set; }


        public void Display()
        {
            Console.WriteLine($"Id: {Id}, Name: {Name}, Location: {Location}");
        }
    }
}
