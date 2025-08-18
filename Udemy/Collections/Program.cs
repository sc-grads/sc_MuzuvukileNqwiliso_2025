namespace Collections
{
    internal class Program
    {
        static void Main(string[] args)
        {
            var colors = new List<string> { "red", "blue", "green", "yellow", "red", "purple", "orange", "red" };


            foreach (var color in colors)
            {
                Console.WriteLine("Current Items:   "+  color);
            }

            // Remove "red" safely using a for loop (backwards)
            for (int i = colors.Count - 1; i >= 0; i--)
            {
                if (colors[i] == "red")
                {
                    colors.RemoveAt(i);
                }
            }

            string [] colors2 = colors.ToArray();
            for (int i = 0; i < colors2.Length; i++)
            {
                Console.WriteLine("Array color : "+colors2[i]);
            }


            var myNumbers = new List<int> { 10,6,45,54,2,35,23,23,65};

            Console.WriteLine("Predicates  numbers");
            List<int> evenNumbers = myNumbers.FindAll(n => n % 2 == 0);
            List<int> oddNumbers = myNumbers.FindAll(n => n % 2 != 0);
            int firstEvenNumber = myNumbers.Find(n=> n % 2 == 0); // you must declare a varaiable as a type not as a List <int> because Find returns a single item compared to FindAll which returns a List of items

            Console.WriteLine("Even numbers:");
            Console.Write("even numbers => ");
            foreach (var number in evenNumbers)
            {
                 Console.Write(number + " ");
            }
            Console.WriteLine();
            Console.Write("odd numbers => ");
            foreach (var oddNumber in  oddNumbers)
            {
                Console.Write(oddNumber + " ");
            }
            Console.WriteLine();
            Console.WriteLine("Before sorting:");
            foreach (var number in myNumbers)
            {
                Console.WriteLine(number);
            }

            myNumbers.Sort();
            Console.WriteLine("After sorting:");
            foreach (var number in myNumbers)
            {
                Console.WriteLine(number);
            }

        }
    }
}
