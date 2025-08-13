using System;
using System.Runtime.InteropServices;
using c_sharp.Calculator;
using c_sharp.Loops;
using c_sharp.Game;

class Program
{
    static void Main(string[] args)
    {

        //Calculator calculator = new Calculator();
        //calculator.SimpleCalculator();

        ForLoop forLoop = new ForLoop();
        //forLoop.loopMethod();

        ////ForLoop.WhileLoop(0);
        //Console.WriteLine("Enter a number to guess:");
        //int userInput;
        //if (int.TryParse(Console.ReadLine(), out userInput))
        //{
        //    ForLoop.WhileLoop(userInput);
        //}
        //else
        //{
        //    Console.WriteLine("Invalid input. Please enter a valid number.");z
        //}
    
        //Console.WriteLine("Press any key to exit!");

        AdventureGame adventureGame = new AdventureGame();
        adventureGame.Game();


        Console.WriteLine("Press any key to exit...");
        Console.ReadKey();
    }


}
