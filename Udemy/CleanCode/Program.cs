using CleanCode;
using OrderModel;

int numberOfStudents = 5;   
string[] studentNames = new string[numberOfStudents];

//for (int i = 0; i < numberOfStudents; i++)
//{
//    Console.Write($"Enter the name of student {i + 1}: ");
//    studentNames[i] = Console.ReadLine();
//}

//Console.WriteLine("\nList of Students:");
//for (int i = 0; i < numberOfStudents; i++)
//{
//    Console.WriteLine($"Student {i + 1}: {studentNames[i]}");
//}

Test customer = new
(1, "John");

customer.Display();

//Order Order = new()
//{
//    OrderId = 101,
//    OrderDate = DateTime.Now
//};

Console.WriteLine();
Customer cust = new(2, "Alice");
//cust.Display(Order);
double rate  = cust.DiscountRate(Customer.CustomerType.VIP, 1500);
Console.WriteLine($"Discount Rate for Premium Customer on $1500: {rate * 100}%");

// Demonstrating Liskov Substitution Principle (LSP)
Console.WriteLine();
Bird sparrow = new Sparrow();
sparrow.MakeSound(); // this method is from the base class Bird
((Sparrow)sparrow).Fly(); // this method is from the derived class Sparrow, in order for me to access the Fly method I have to cast the sparrow object to Sparrow class
Bird penguin = new Penguin();
// since I am using a Bird class I want to access the MakeSound method from the base class Bird
penguin.MakeSound(); // this method is from the base class Bird
((Penguin)penguin).Swim(); // this method is from the derived class Penguin, in order for me to access the Swim method I have to cast the penguin object to Penguin class


// Demonstrating Single Responsibility Principle (SRP)
OrderManager orderManager = new OrderManager();
orderManager.AddOrder(new Order { OrderId = 103, ProductName = "Tablet", Price = 600m, Quantity = 3 });
orderManager.AddOrder(new Order { OrderId = 104, ProductName = "Monitor", Price = 300m, Quantity = 2 });
orderManager.AddOrder(new Order { OrderId = 105, ProductName = "Keyboard", Price = 50m, Quantity = 5 });
orderManager.AddOrder(new Order { OrderId = 106, ProductName = "Mouse", Price = 25m, Quantity = 10 });
orderManager.AddOrder(new Order { OrderId = 107, ProductName = "Headphones", Price = 120m, Quantity = 4 });


orderManager.DisplayOrders();
Console.WriteLine("We have : {0} orders.",orderManager.TotalOrders());
Console.WriteLine($"Total Amount: ${orderManager.CalculateTotalAmount()}");

// Demonstrating Interface Segregation Principle (ISP)
Console.WriteLine();
IWorker worker = new Human();
worker.Work();
((IFeedable)worker).Eat();
IWorker robotWorker = new Robot();
robotWorker.Work();  // A robot cannot eat so we don't implement IFeedable interface
// the ISP principle is close similar to LSP principle but the difference is that ISP is about interfaces and LSP is about classes

Console.WriteLine();

// The DIP principle is about dependency injection and the difference between DIP and SRP is that DIP is about high-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details. Details should depend on abstractions.
IMessageService emailService = new EmailService();
IMessageService smsService = new SMSService();
IMessageService pushNotificationService = new PushNotificationService();
emailService.SendMessage("Hello via Email!", "Alice" );
smsService.SendMessage("Hello via SMS!", "Bob" );
pushNotificationService.SendMessage("Hello via Push Notification!", "Charlie");
NotificationManager notificationWithEmail = new(emailService);
NotificationManager notificationWithSMS = new(smsService);
NotificationManager notificationWithPush = new(pushNotificationService);

/// <summary>
/// Represents a program demonstrating naming conventions in C#.
/// These commets explain the naming conventions used in the code. and are the documentation comments for the class.
/// </summary>

public partial class Program // PascalCase, class names must be nouns
{
    private int _studentCount; // camelCase
    public  string StudentName { get; set; } // PascalCase

    public const double PI = 3.14; // all uppercase with underscores

    public bool IsEnrolled { get; set; } // PascalCase and the bool variable starts with "Is" or "Has"

    public bool IsGraduated() // PascalCase , methods must be verbs and the bool variable starts with "Is" or "Has"
    {
        return _studentCount > 0;
    }

    //has, is, can, should, get, set

    public static readonly string SCHOOL_NAME = "ABC University"; // all uppercase with underscores

    public void GetStudentCount() // PascalCase , methods must be verbs
    {
        Console.WriteLine($"Number of Students: {_studentCount}");
    }

    public void SetStudentName(string name) // PascalCase , methods must be verbs
    {
        StudentName = name;
    }

    public void PrintSchoolName() // PascalCase , methods must be verbs
    {
        Console.WriteLine($"School Name: {SCHOOL_NAME}");
    }

    public void DisplayStudentInfo() // PascalCase , methods must be verbs
    {
        Console.WriteLine($"Number of Students: {_studentCount}");
        Console.WriteLine($"Student Name: {StudentName}");
    }

    // the comments must be in English and explain the naming conventions used in the code
    // they must be why not what or how 
    // TODO: Add more methods to demonstrate naming conventions
    public Program(int studentCount, string studentName) // PascalCase and camelCase
    {
        _studentCount = studentCount;
        StudentName = studentName;
    }

    
    public static void Main(string[] args)
    {
      
    }
}

/// <summary>
/// Represents a customer with naming conventions.
/// </summary>
public class Customer(int customerId, string firstName)
{
    public int CustomerId { get; set; } = customerId;
    public string FirstName { get; set; } = firstName;

    public enum CustomerType // PascalCase, enum names must be nouns
    {
        Regular,
        Premium,
        VIP
    }

    public double DiscountRate(CustomerType customerType, double amount)
    {
        double rate;

        switch (customerType)
        {
            case CustomerType.Regular:
                rate = amount > 1000 ? 0.05 : 0.02;
                break;
            case CustomerType.Premium:
                rate = amount > 1000 ? rate = 0.10 : rate = 0.07;
                break;
            case CustomerType.VIP:
                rate = 0.15;
                break;
            default:
                rate = 0.0;
                break;
        }
        return rate;
    }

    public void DisplayCustomerInfo() // PascalCase , methods must be verbs
    {
        Console.WriteLine($"Customer ID: {CustomerId}, First Name: {FirstName}");
    }

    public bool isValidOrder(Order order) // PascalCase , methods must be verbs and the bool variable starts with "Is" or "Has"
    {
        if (order != null && order.OrderId > 0)
        {
            return true;
        }
        else
        {
            return false;
        }
    }

    //public void PlaceOrder(Order order) // PascalCase , methods must be verbs
    //{
    //    if (isValidOrder(order))
    //    {
    //        Console.WriteLine($"Order {order.OrderId} placed successfully on {order.OrderDate}");
    //    }
    //    else
    //    {
    //        Console.WriteLine("Invalid order");
    //    }
    //}

    public void NotifyCustomer(string message) // PascalCase , methods must be verbs
    {
        Console.WriteLine($"Notification to {FirstName}: {message}");
    }

    public void Display(Order order) // PascalCase , methods must be verbs
    {
        Console.WriteLine($"Customer ID: {CustomerId}, First Name: {FirstName}");

        if(isValidOrder(order))
        {
            //PlaceOrder(order);
            NotifyCustomer("Your order has been placed successfully.");
        }
    }

}

//public class Order
//{
//    public int OrderId { get; set; }
//    public DateTime OrderDate { get; set; }
//}