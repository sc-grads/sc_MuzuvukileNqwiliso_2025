using OrderModel;


namespace CleanCode.Processing
{
    public class PaymentProcessor
    {
        

        public void ProcessPayment(Order order, decimal amount)
        {
            Console.WriteLine($"Processing payment of {amount} for Order ID: {order.OrderId}");
        }
    }
}