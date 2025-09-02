using System;
using System.Collections.Generic;
using System.Diagnostics;
using CleanCode.Processing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using OrderModel;


namespace CleanCode
{
    internal class SRP
    {
    }

}

namespace OrderModel
{
    public class Order
{
    public int OrderId { get; set; }
    public string ProductName { get; set; }
    public decimal Price { get; set; }
    public int Quantity { get; set; }
    }
}

namespace CleanCode
{


    public class OrderManager
    {
        private List<Order> _orders = new List<Order>();

        private PaymentProcessor _paymentProcessor = new PaymentProcessor();

        public PaymentProcessor PaymentProcessor
        {
            get { return _paymentProcessor; }
            set { _paymentProcessor = value; }
        }

        private int _orderId;
        private string _productName;
        private decimal _price;
        private int _quantity;

        // Constructor
        public OrderManager(int orderId, string productName, decimal price, int quantity)
        {
            _orderId = orderId;
            _productName = productName;
            _price = price;
            _quantity = quantity;
        }

        public OrderManager() { }

        // Add a new order
        public void AddOrder(Order newOrder)
        {


            _orders.Add(newOrder);
            Console.WriteLine($"Order #{newOrder.OrderId} added.");

            _paymentProcessor.ProcessPayment(newOrder, newOrder.Price * newOrder.Quantity);
        }

        // Show all orders
        public void DisplayOrders()
        {
            foreach (var order in _orders)
            {
                Console.WriteLine($"OrderId: {order.OrderId}, Product: {order.ProductName}, Price: {order.Price}, Quantity: {order.Quantity}");
            }

        }

       public int TotalOrders()
        {
            return _orders.Count;
        }

        public  decimal CalculateTotalAmount()
        {
            return _orders.Sum(o => o.Price * o.Quantity);
        }
    }




    public class Logger
    {
        public void Log(string message)
        {
            Debug.WriteLine(message);
        }
    }

    public class Notifier
    {
        public void NotifyCustomer(string message)
        {
            Console.WriteLine($"Notification sent to customer: {message}");
        }
    }
}