using System;

namespace Generics.Task_Manager
{
    public class EmailTask : ITask<string>
    {
        public void Execute(string message)
        {
            Console.WriteLine($"Sending email with message: {message}");
        }
    }
}