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
            _paymentMethod = paymentMethod;
        }
        public void MakePayment(decimal amount)
        {
            // this argument is passed to the interface method and is going to be used in the different payment methods in diffrent classes 
            // this is an example of polymorphism, where the same method call can result in different behaviors based on the object type
            // CreditCardPayment and PayPalPayment both implement the IPayment interface, allowing us to use them interchangeably
            _paymentMethod.ProcessPayment(amount); // using the interface method
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

            string message = "This is a log message.";  
            File.AppendAllText("log.txt", message+ "\n");

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
