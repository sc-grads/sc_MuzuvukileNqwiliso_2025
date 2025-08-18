using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Quiz_Question_Game
{
    

    internal class Questions
    {
        // properties

        public string QuestionText { get; set; }
        public string[] Answers { get; set; }
        public int CorrectAnswerIndex { get; set; }

        public Questions(string questionText, string[] answers, int correctAnswerIndex)
        {
            QuestionText = questionText;
            Answers = answers;
            CorrectAnswerIndex = correctAnswerIndex;
        }

        public bool IsCorrect(int answerIndex)
        {
            return answerIndex == CorrectAnswerIndex;
        }
    }
}
