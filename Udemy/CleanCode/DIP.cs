using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CleanCode
{
    internal class DIP
    {
    }

    /// <summary>
    ///  This class represents a message service that can send messages. (Email, SMS)
    /// </summary>
    public interface IMessageService
    {

        /// <summary>
        ///  This method sends a message to a specified recipient.
        /// </summary>
        /// <param name="message"></param>
        /// <param name="recipient"></param>
        void SendMessage(string message, string recipient);
    }

    public class EmailService : IMessageService
    {
        public void SendMessage(string message, string recipient)
        {
            Console.WriteLine($"Email sent to {recipient} with message: {message}");
        }
    }

    public class SMSService : IMessageService
    {
        public void SendMessage(string message, string recipient)
        {
            Console.WriteLine($"SMS sent to {recipient} with message: {message}");
        }
    }

    public class PushNotificationService : IMessageService
    {
        public void SendMessage(string message, string recipient)
        {
            Console.WriteLine($"Push Notification sent to {recipient} with message: {message}");
        }
    }

    /// <summary>
    /// This class manages notifications and depends on the IMessageService abstraction.
    /// </summary>
    public class NotificationManager
    {
        private readonly IMessageService _messageService;

        /// <summary>
        /// In this methid we are injecting the dependency of IMessageService via constructor injection.
        /// (SMS Object or  Email Object)
        /// </summary>
        /// <param name="messageService"></param>
        public NotificationManager(IMessageService messageService)
        {
            _messageService = messageService;
   
        }
        /// <summary>
        ///  These method sends a notification using the injected message service.
        /// </summary>
        /// <param name="message"></param>
        /// <param name="recipient"></param>

        public void Notify(string message, string recipient)
        {
            _messageService.SendMessage(message, recipient);
        }
    }

}
