using System.ComponentModel;

namespace Delegates
{
    internal class Program
    {
        // a delegate is a type that represents references to methods with a particular parameter list and return type
        public delegate void MyDelegate(string message);

        public delegate void Notify(string message);

        public delegate void NotifyWithLog(string message, string logMessage);

        public static void MessageWithLog(string message, string logMessage)
        {
            Console.WriteLine("Message: " + message);
            Console.WriteLine("Log: " + logMessage);
        }   

        public static void MyMethod(string message)
        {
            Console.WriteLine(message);
        }

       // public static void Message(string message) => Console.WriteLine("Message: "+message); // the methods must have the same signature as the delegate (delegate => void also normal method)

        public static void Log(string message) => Console.WriteLine($"Log: {message}");

        public delegate string LogToFile(string errorMessage);

        public static string logError(string errorMessage)
        {
            File.AppendAllText("log.txt", errorMessage + Environment.NewLine);
            return errorMessage;
        }

        static void SafeInvocation(Notify? d, string message)
        {
            if (d != null) // checking if the delegate is not null before invoking it
            {
                d(message);
            }
        }

        static void Main(string[] args)
        {
            MyDelegate myDelegate = MyMethod;

            LogToFile logToFile = logError; // delegate instantiation
            string errorMessage =  logToFile("error message displayed in the log delegate...");
            Console.Write(errorMessage);
            Console.WriteLine(" - logged to file.");
            //Notify? message = Message; // delegate instantiation 
            //message += Log; // delegate invocation with multiple methods
            //message += MyMethod; // both these methods are going to be invoked using one delegate with same signature and message parameter
            //message("Hello from Message!"); // delegate invocation
                                            // the varaibles are like object methods, they can be assigned to other variables, passed as parameters, and returned from methods

           // message -= MyMethod; // removing MyMethod from the invocation list

           //SafeInvocation(message, "Hello from Message after removing MyMethod!"); // safe invocation of the delegate

            NotifyWithLog notifyWithLog = MessageWithLog; // delegate instantiation
            notifyWithLog.Invoke("Hello from NotifyWithLog!", "This is a log message!"); // delegate invocation with two parameters

            int[] numbers = { 1, 2, 3, 4, 5 };
            string[] names = { "Alice", "Bob", "Charlie" };
            char[] letters = { 'A', 'B', 'C', 'D', 'E' };
            PrintArray(numbers); // using lambda expression to print each number
            PrintArray(names); // using lambda expression to print each name
            PrintArray(letters); // using lambda expression to print each letter



            Person[] people = new Person[]
            {
                new Person { Name = "Alice", Age = 30 },
                new Person { Name = "Bob", Age = 25 },
                new Person { Name = "Charlie", Age = 35 },
                new Person { Name = "David", Age = 20 },
                new Person { Name = "Eve", Age = 28 }
            };

            //PersonSorter.Sort(people, PersonSorter.CompareByName); // sorting by name
            PersonSorter.Sort(people, PersonSorter.CompareByAge); // sorting by age
            foreach (var person in people)
            {
                Console.WriteLine(person);
            }


            Provider provider = new Provider();
            Subscriber subscriber = new Subscriber();
            provider.OnNotify += subscriber.OnNotify; // subscribing to the event
            provider.RaiseEvent("This is a notification message!"); // raising the event, which will call the OnNotify method of the subscriber


            TemperatureMonitor monitor = new TemperatureMonitor();
            TemperatureAlert alert = new TemperatureAlert();
            monitor.OnTemperatureChanged += alert.HandleTemperatureChange; // subscribing to the event

            monitor.Temperature = 25; // setting temperature, should not trigger alert
            Console.WriteLine("Enter your room temperature : ");
            monitor.Temperature = Convert.ToDouble(Console.ReadLine()); // setting temperature, should trigger alert if above 30



        }
        
        public static void PrintArray<T>(T[] array)
        {
            foreach (var item in array)
            {
                Console.Write(item+" ");
            }
            Console.WriteLine();
        }

     

        class Person
        {
            public string Name { get; set; }
            public int Age { get; set; }
            public override string ToString()
            {
                return $"{Name}, {Age} years old";
            }

        }

        class PersonSorter
        {

            public static void Sort(Person[] person, Compare<Person> compare) // The  compare are the two methods that are used to compare the Person objects
            {
                for (int i = 0; i < person.Length - 1; i++)
                {
                    for (int j = i + 1; j < person.Length; j++)
                    {
                        if (compare(person[i], person[j]) > 0)
                        {
                            // swap
                            var temp = person[i];
                            person[i] = person[j];
                            person[j] = temp;
                        }
                    }
                }
            }

            // The  two below methods are used as comparison methods for sorting
            // They have the same signature as the Compare delegate
            // They can be passed as parameters to the Sort method
            public static int CompareByName(Person x, Person y)
            {
                return string.Compare(x.Name, y.Name);
            }
            public static int CompareByAge(Person x, Person y)
            {
                return x.Age.CompareTo(y.Age);
            }
        }

       

        public delegate void Message(string message); // delegate with a single parameter

        class Provider
        {
            public event Message? OnNotify; // event that uses the delegate
            public void RaiseEvent(string message)
            {
                OnNotify?.Invoke(message); // invoking the event => this will call all the methods that are subscribed to the event
            }
        }

        class Subscriber
        {
            public void OnNotify(string message)
            {
                Console.WriteLine("Subscriber received message: " + message);
            }
        }

    }

    public delegate int Compare<T>(T x, T y);
}
