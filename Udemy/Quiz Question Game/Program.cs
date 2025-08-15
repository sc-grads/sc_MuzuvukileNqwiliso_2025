namespace Quiz_Question_Game
{
    internal class Program
    {
        static void Main(string[] args)
        {
            Questions[] questions = new Questions[] {
              new Questions(  "What is the capital of France?",
                new string[] { "Berlin", "Madrid", "Paris", "Rome" },
                2),
                new Questions(  "What is the largest planet in our solar system?",
                new string[] { "Earth", "Jupiter", "Saturn", "Mars" },
                1),
                new Questions(  "What is the chemical symbol for water?",
                new string[] { "H2O", "CO2", "O2", "NaCl" },
                0),
                new Questions(  "Who wrote 'To Kill a Mockingbird'?",
                new string[] { "Harper Lee", "Mark Twain", "Ernest Hemingway", "F. Scott Fitzgerald" },
                0)
           };

            int totalQuestions = questions.Length;

            Quiz quiz = new Quiz(questions);

            Console.WriteLine("===============================================================================");
            Console.WriteLine("======================== Welcome to the Quiz Game! ============================");
            Console.WriteLine("===============================================================================");

            if (questions.Length == 0)
            {
                Console.WriteLine("No questions available for the quiz.");
                return;
            }
            else
            {
                Console.WriteLine("Let's start the quiz!");
               quiz.DisplayQuestions(questions[0]); // Display the first question
                for (int i = 1; i < questions.Length; i++)
                {
                    Console.WriteLine("\nNext Question:");
                    quiz.DisplayQuestions(questions[i]); // Display subsequent questions
                }
            }

            quiz.DisplayResults(quiz.Score, totalQuestions); // Display final score
        }
    }
}
