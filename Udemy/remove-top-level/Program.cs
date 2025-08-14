namespace remove_top_level
{
    internal class Program
    {
        static void Main(string[] args)
        {
            // this is where we run our methods and other code
            outSideClass();
            Program pr = new Program();
           int results =  pr.newMethod(12);
            Console.WriteLine(results);

            Console.WriteLine("Click any key to terminate the window");
            Console.ReadKey();
        }

        // this is where we write out code, outside of the class
        // STATIC -> this keyword is used when you want to call a function without a need of creating a instance of a class
        public static void outSideClass()
        {
            Console.WriteLine("This is a function outside the class and is static.");
        }

        public int newMethod(int i)
        {
            Console.WriteLine("In this method we add 20 to the user input");
            return i+ 20;
        }

    }
}
