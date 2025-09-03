namespace Threads
{
    internal class Program
    {
        static void Main(string[] args)
        {
            //Console.WriteLine("Hello, World!1");
            //Thread.Sleep(1000); 
            //Console.WriteLine("Hello, World!1");
            //Thread.Sleep(1000);
            //Console.WriteLine("Hello, World!1");
            //Thread.Sleep(1000);
            //Console.WriteLine("Hello, World!1");

            //new Thread(()=>
            //{
            //    Thread.Sleep(1000);
            //    Console.WriteLine("Hello, World 1");
            //}).Start();

            //new Thread(()=>
            //{
            //    Thread.Sleep(1000);
            //    Console.WriteLine("Hello, World 2");

            //}).Start();


            //new Thread(()=>
            //{
            //    Thread.Sleep(1000);
            //    Console.WriteLine("Hello, World 3");

            //}).Start();

            //Console.ReadLine();

            //var taskCompletionSource = new TaskCompletionSource<bool>();
            //var thread = new Thread(() =>
            //{
            //    Console.WriteLine("Thread {0} started, doing some work...", Thread.CurrentThread.ManagedThreadId);
            //    Thread.Sleep(5000);
            //    taskCompletionSource.TrySetResult(true);
            //    Console.WriteLine("Thread {0} is done, doing some work...", Thread.CurrentThread.ManagedThreadId);
            //});

            //thread.Start();
            //var test = taskCompletionSource.Task.Result;
            //Console.WriteLine("Main thread {0} received signal from worker thread.", Thread.CurrentThread.ManagedThreadId);

            //Console.WriteLine("Numerious threads");

            //Enumerable.Range(0, 10).ToList().ForEach(i =>
            //{
            //    Console.WriteLine("Starting thread {0}", i);
            //    new Thread(() =>
            //    {
            //        Console.WriteLine("Thread {0} started, doing some work...", Thread.CurrentThread.ManagedThreadId);
            //        Thread.Sleep(2000);
            //        Console.WriteLine("Thread {0} is done, doing some work...", Thread.CurrentThread.ManagedThreadId);
            //    }).Start();
            //});


            Console.WriteLine("Main thread {0} is doing other work...", Thread.CurrentThread.ManagedThreadId);

            var thread1 = new Thread(Thread1Method);
            var thread2 = new Thread(Thread2Method);

            thread1.Start();
            thread2.Start();

            // This will out put Thread 1 did not complete within 2 seconds. because the Thread1Method sleeps for 3 seconds.
            // The join method blocks

            if (thread1.Join(1000))
            {
                Console.WriteLine("Thread 1 completed within 1 seconds.");
            }
            else
            {
                Console.WriteLine("Thread 1 did not complete within 2 seconds.");
            }

            if(thread1.IsAlive)
            {
                 Console.WriteLine("Thread 1 is still running.");
                 Console.WriteLine("Because it will took 3 seconds to complete.");
            }
            else
            {
                 Console.WriteLine("Thread 1 has finished.");
            }

                thread2.Join(); // Wait for thread2 to finish before exiting the program
            Console.WriteLine("Thread 2 has completed.");
            Console.WriteLine("Main thread {0} is done.", Thread.CurrentThread.ManagedThreadId);
        }


        static void Thread1Method()
        {
            Console.WriteLine("Thread 1 starting.");
            Thread.Sleep(1000);
            // The  below line will not be printed because the main thread will continue after 1 second due to the Join timeout.
            Console.WriteLine("Thread 1 completed and is returning back to main thread.");
        }

        static void Thread2Method()
        {
            Console.WriteLine("Thread 2 starting.");

        }

    }
}
