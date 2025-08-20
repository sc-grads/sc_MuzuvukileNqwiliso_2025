using System;

namespace Interface
{
    interface IPayment
    {
        void ProcessPayment(decimal amount);
    }

    // below are two classes implementing the IPayment interface, they are different payment methods

    class CreditCardPayment : IPayment // interface implementation
    {
        public void ProcessPayment(decimal amount) // interface method implementation
        {
            Console.WriteLine($"Processing credit card payment of {amount:C}.");
        }
    }

    class PayPalPayment : IPayment // interface implementation
    {
        public void ProcessPayment(decimal amount) // interface method implementation
        {
            Console.WriteLine($"Processing PayPal payment of {amount:C}.");
        }
    }

    class PaymentProcessor
    {
        private readonly IPayment _paymentMethod;
        public PaymentProcessor(IPayment paymentMethod) // constructor injection
        {
            this._paymentMethod = paymentMethod;
        }
        public void MakePayment(decimal amount)
        {
            // this argument is passed to the interface method and is going to be used in the different payment methods in diffrent classes 
            // this is an example of polymorphism, where the same method call can result in different behaviors based on the object type
            // CreditCardPayment and PayPalPayment both implement the IPayment interface, allowing us to use them interchangeably
            _paymentMethod.ProcessPayment(amount); // using the interface method
        }
    }


    public interface IPrinter
    {
        void Print(string message);
    }

    public interface IScanner
    {
        void Scan(string document);
    }

    public class Printer : IPrinter, IScanner
    {

        public void Print(string message)
        {
            Console.WriteLine($"Printing: {message}");
        }
        public void Scan(string document)
        {
            Console.WriteLine($"Scanning: {document}");
        }
}

public interface ILogger // Changed to public
    {
        void Log(string message);
    }

    public class FileLogger : ILogger
    {
       public void Log(string message)
        {
            string baseFilePath = @"C:\sc_MuzuvukileNqwiliso_2025\Udemy\Interface";
            string filePath = Path.Combine(baseFilePath, "log.txt");
            if (!Directory.Exists(baseFilePath))
            {
                Directory.CreateDirectory(baseFilePath);
            }
            File.AppendAllText(filePath, message + Environment.NewLine);
        }
    }

    public class DatabaseLogger: ILogger
    {
        public void Log(string message)
        {
            // Implementation for logging to a database would go here
            // This is just a placeholder as the actual database logic is not implemented
            Console.WriteLine("Logging to the database is not implemented yet.");
            Console.WriteLine("Here is a message: being logged {0}", message);
        }
    }

    public class MainApp // Changed to public
    {
        private readonly ILogger _logger;

        public MainApp(ILogger logger) // Constructor remains unchanged
        {
            this._logger = logger;
        }

        public void Run()
        {
            _logger.Log("Application started.");
            // Other application logic goes here
            _logger.Log("Application finished.");
        }
    }

    public class Hammer
    {
        public void Hit()
        {
            Console.WriteLine("The hammer hits the nail.");
        }
    }

    public class Screwdriver
    {
        public void Turn()
        {
            Console.WriteLine("The screwdriver turns the screw.");
        }
    }

    public class Builder
    {

        private readonly Hammer _hammer;
        private readonly Screwdriver _screwdriver;

        public Builder(Hammer hammer, Screwdriver screwdriver) // Constructor injection
        {
            this._hammer = hammer; // more flexible way to inject dependencies
            this._screwdriver = screwdriver;

            this._hammer = new Hammer(); // Initializing Hammer
            this._screwdriver = new Screwdriver(); // Initializing Screwdriver
        }
        public void Build()
        {
            _hammer.Hit(); // Using the Hammer class

        }

    }
    internal class Program
    {
        static void Main(string[] args)
        {
          IPayment paymentMethod = new CreditCardPayment(); // using the CreditCardPayment class
          IPayment paymentMethod2 = new PayPalPayment(); // using the PayPalPayment class
          PaymentProcessor processor = new PaymentProcessor(paymentMethod); // injecting the payment method into the processor
          PaymentProcessor processor2 = new PaymentProcessor(paymentMethod2); // injecting the second payment method into the processor
          processor.MakePayment(100.00m); // making a payment using the CreditCardPayment class
          processor2.MakePayment(200.00m); // making a payment using the PayPalPayment class

          ILogger logger = new FileLogger(); // using the FileLogger class
          ILogger dbLogger = new DatabaseLogger(); // using the DatabaseLogger class
            MainApp app = new MainApp(logger); // injecting the logger into the MainApp class
            MainApp app2 = new MainApp(dbLogger); // injecting the database logger into the MainApp class
            app.Run(); // running the application
            dbLogger.Log("This is a log message for the database logger."); // logging a message using the database logger




          Printer printer = new Printer(); // using the Printer class
            printer.Print("Hello, World!"); // printing a message using the Printer class
            printer.Scan("Document1.pdf"); // scanning a document using the Printer class
        }


    }

    interface IAnimal
    {
        void MakeSound();
        void Eat(string food);
    }

    class Cat : IAnimal
    {
        public void Eat(string food)
        {
            Console.WriteLine($"The cat eats {food}.");
        }

        public void MakeSound()
        {
            Console.WriteLine("The cat says: Meow!");
        }
    }
}
