using System;
using System.Collections.Generic;
using System.Dynamic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Quiz_Question_Game
{
    internal class Quiz
    {

        private Questions[] questions; // Array of questions in the quiz, from the Questions class

        private int _score = 0; // Variable to keep track of the score
        public int Score
        {
            get { return _score; } // Getter for the score
            set { _score = value; } // Setter for the score
        }

        public Quiz(Questions[] questions)
        {
            this.questions = questions; // Initialize the quiz with the provided questions
        }


        public  void DisplayQuestions(Questions questions)
        {
            Console.WriteLine(questions.QuestionText); // Display the question text
            for (int i = 0; i < questions.Answers.Length; i++)
            {
                Console.ForegroundColor = ConsoleColor.Cyan; // Set the color for answer options
                Console.Write(" ");
                Console.Write( i + 1);
                Console.ResetColor(); // Reset the color to default
                Console.WriteLine($". {questions.Answers[i]}"); // Display each answer option
            }

            if(GetAnswerIndex() == questions.CorrectAnswerIndex)
            {
                Console.ForegroundColor = ConsoleColor.Green; // Set color for correct answer
                Console.WriteLine("Correct!");
                Score++; // Increment score for correct answer
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Red; // Set color for incorrect answer
                Console.WriteLine("Incorrect. The correct answer was: " + questions.Answers[questions.CorrectAnswerIndex]);
            }
        }

        public int GetAnswerIndex()
        {
            Console.Write("Please enter the number of your answer: ");
            string input = Console.ReadLine(); // Read user input
            int answerIndex;
            // Validate input and convert to index
            while (!int.TryParse(input, out answerIndex) || answerIndex < 1 || answerIndex > questions[0].Answers.Length)
            {
                Console.Write("Invalid input. Please enter a valid answer number: ");
                input = Console.ReadLine();
            }
            return answerIndex - 1; // Convert to zero-based index
        }

        public void DisplayResults(int score, int totalQuestions)
        {
            Console.ForegroundColor = ConsoleColor.Magenta;
            Console.WriteLine("\nQuiz Completed!");
            double percentage = (double)score / totalQuestions * 100; // Calculate percentage score
            if (percentage >= 50)
            {
                Console.ForegroundColor = ConsoleColor.Green; // Set color for passing score
                Console.WriteLine($"You passed the quiz with a score of {score} out of {totalQuestions} ({percentage:F2}%).");
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Red; // Set color for failing score
                Console.WriteLine($"You failed the quiz with a score of {score} out of {totalQuestions} ({percentage:F2}%).");
            }
        }
    }
}
