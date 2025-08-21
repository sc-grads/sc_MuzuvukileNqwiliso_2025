
using System.Text.RegularExpressions;

namespace RegexDemo
{
    internal class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Enter a string to validate:");
            string pattern = @"^[a-zA-Z0-9]+$"; // Example pattern: alphanumeric characters only
            var regex = new Regex(pattern); // This now refers to System.Text.RegularExpressions.Regex
       
           Console.WriteLine("Enter your password in alphanumeric format:");
            string input = Console.ReadLine();
            if (regex.IsMatch(input))
            {
                Console.WriteLine("Valid input.");
            }
            else
            {
                Console.WriteLine("Invalid input. Please enter only alphanumeric characters.");
            }
            // Example of using the regex to find matches in a string
            string text = "Sample123 Text456";
            MatchCollection matches = regex.Matches(text);
            Console.WriteLine($"Found {matches.Count} matches in the text:");
            foreach (Match match in matches)
            {
                Console.WriteLine(match.Value);
            }
        }
    }
}
