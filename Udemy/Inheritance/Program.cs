namespace Inheritance
{
    internal class Program
    {
        static void Main(string[] args)
        {
            // Usage
            Animal a1 = new Dog();
            Animal a2 = new Cat();
        

            a1.Speak(); // Dog barks
            a2.Speak(); // Cat meows

            a1.diplayInfo(); // Name: , Age: 0, Species:

            a2.diplayInfo(); // Name: , Age: 0, Species:


            Console.WriteLine("Below will demonstrate what will be displayed when the based class method is overriden and at the same time called");
            a2.Speak(); // Cat meows. this is on the cat class which is a derived class



            Employee employee = new Employee("John Doe", 30, "Software Engineer", 60000);
            Console.WriteLine("Employee created successfully.");
           

        }
    }

   abstract class Animal
    {

        public string name; // this is public, accessible from anywhere
        protected int age; // this  protected, accessible in derived classes
        private string species; // this is private, accessible only within this class

        public abstract void Speak(); // by default this method is virtual, meaning derived classes can override it

        public void Eat()
        {  // this is a normal method, not overriding or hiding
            Console.WriteLine("Animal eats");
        }

        public virtual void diplayInfo()
        {
            Console.WriteLine($"Name: {name}, Age: {age}, Species: {species}");
        }

    }

    class Dog : Animal
    {
        public override void Speak()
        {
            Console.WriteLine("Dog barks");
        }

        public new void Eat()
        {   // this is a new method, hiding the base class method
            Console.WriteLine("Dog eats dog food");
        }



    }

    class Cat : Animal
    {
        public override void Speak()
        { // this is an overridden method

   
            Console.WriteLine("Cat meows. this is on the cat class which is a derived class");
        }

        public override void diplayInfo()
        {
            name = "Whiskers";
            age = 3;

            Console.WriteLine($"Cat Name: {name}, Age: {age}");
        }

        // the overridden method is good when you want to change the behavior of a base class method 
        // whereas the new method is good when you want to provide a completely different implementation, it will not affect the base class method

    }


    public class Person
    {
        private string Name { get; set; }
        private int Age { get; set; }

        public Person(string name, int age)
        {
            Name = name;
            Age = age;
            Console.WriteLine($"Person created: Name = {Name}, Age = {Age}");
        }
    }

    public class Employee: Person { 
    

         private string Position { get; set; }
        private double Salary { get; set; }

        public Employee(string name, int age, string position, double salary) : base(name, age)
        {
       
            Position = position;
            Salary = salary;
            Position = position;
            Salary = salary;   
            
            Console.WriteLine($"Employee created: Name = {name}, Age = {age}, Position = {Position}, Salary = {Salary}");
        }

    }


}