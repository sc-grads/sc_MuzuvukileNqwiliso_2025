using c_sharp.Methods;

//int[] randomNumbers = new int[5];
//Random random = new Random();
//for (int i = 0; i < randomNumbers.Length; i++)
//{
//    randomNumbers[i] = random.Next(1,10);

//}

//double[] randomNumbers2 = {2.4,67.6};

//double[] doubleNumbers = [1,4,6.8];
//Console.WriteLine(doubleNumbers[2]);

//string[] names = { "Alice", "Brian", "Cynthia" };
//string name = "";

//do
//{
//    Console.WriteLine("Please guess the name:");
//    name = Console.ReadLine();

//    // Pick a random name from the array
//    string chosenName = names[random.Next(0, names.Length)];

//    if (name.Equals(chosenName, StringComparison.OrdinalIgnoreCase))
//    {
//        Console.WriteLine("Good guess!");
//        break;
//    }
//    else
//    {
//        Console.WriteLine("Wrong guess. Try again.");
//    }

//} while (Array.Exists(names, n => n.Equals(name, StringComparison.OrdinalIgnoreCase)));

//for (int i = 0; i < randomNumbers.Length;i++)
//{
//    Console.WriteLine(randomNumbers[i]);
//}


//int[,] randomNumbers3 = { { 23, 45 }, { 32, 56 }, { 23, 45 } };

//Console.WriteLine(randomNumbers3[2, 1]); // Prints: 45

//for (int i = 0; i < randomNumbers3.GetLength(0); i++) // rows
//{
//    for (int j = 0; j < randomNumbers3.GetLength(1); j++) // columns
//    {
//        Console.WriteLine(randomNumbers3[i, j]);
//    }
//}


//int[] numbers = { 1, 2, 3, 4, 5 };
//for (int i = 0; i < numbers.Length; i++)
//{
//    Console.WriteLine(numbers[i]);
//}

//int sum = 0;
//int[,] numbers = new int[3, 3];

//numbers[0, 0] = 1;
//numbers[0, 1] = 2;
//numbers[0, 2] = 3;
//numbers[1, 0] = 4;
//numbers[1, 1] = 5;
//numbers[1, 2] = 6;
//numbers[2, 0] = 7;
//numbers[2, 1] = 8;
//numbers[2, 2] = 9;

//for (int i = 0; i < numbers.GetLength(0); i++)
//{
//    Console.WriteLine();
//    for (int j = 0; j < numbers.GetLength(1);j++)
//    {
//        Console.Write(numbers[i, j]+ " ");
//        sum += numbers[i, j];
      
//    }
//   Console.WriteLine();
//    Console.WriteLine("Sum : {0}", sum);
//    sum = 0;
//}

void MyMethod()
{
    Console.WriteLine("This is inside the method");
}

void MyMethod2(string Username)
{

    if ("Lazola" == Username) Console.WriteLine($"Hello {Username}");
}

//void login(string Username, string password)
//{
//    if (Username == "Fennic" && password == "password")
//    {
//        Console.WriteLine("Sucessful login");
//    }else
//    {
//        Console.WriteLine("Incorrect details. Try Again");
//    }
//}


//MyMethod();
//MyMethod2("Lazola");

//Console.WriteLine("Enter your username: ");
//string username = Console.ReadLine();
//Console.WriteLine("Enter your Password: ");
//string password = Console.ReadLine();

//login(username, password);

double addMethod(double num1, double num2)
{
    return num1 + num2;
}

//Console.WriteLine("Enter num 1 : ");
//double num1 = double.Parse(Console.ReadLine());
//Console.WriteLine("Enter num 2 : ");
//double num2 = double.Parse(Console.ReadLine());


//double results = addMethod(num1, num2);
//Console.WriteLine("Results {0}", results);




Methods methods = new Methods();
int number = 10000;
methods.MethodValue(ref number);
Console.WriteLine("This is a number method, with this value : {0} ", number); // This is the reference method that have the power to change the value of the varaibles passed to it.

Console.WriteLine("What is your age? ");
int age = 20;
int value = methods.MethodParameter(out age); // this will be overriden by the value in assigned in the method on another file.
// this acts as reference type the only difference with it is that the value in the method inside must be assigned. 
Console.WriteLine($"{age} {value}"); 

Console.WriteLine("Below is a IN method..."); 
int num  = 203;
methods.MethodParamter2(in num);

Console.WriteLine();
    Console.WriteLine("Press any key to close the window.");
Console.ReadKey();