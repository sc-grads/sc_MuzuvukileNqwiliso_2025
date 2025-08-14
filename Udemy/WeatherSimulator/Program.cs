namespace WeatherSimulator
{
    internal class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Enter the number of days you  want to simulate");
            int days = int.Parse(Console.ReadLine());
            int[] temperature = new int[days];
            string[] conditions = { "Cloudy", "Rainy", "Sunny", "Snowy" };
            string[] weatherConditions = new string[days];

            Random random = new Random();
            for (int i = 0; i < days; i++)
            {
                temperature[i] = random.Next(-10, 40);
                weatherConditions[i] = conditions[random.Next(conditions.Length)];

            }

            PrintWeather(temperature, weatherConditions);

            AverageTemperature(temperature);
            Console.WriteLine("Temperature MAX {0} °C", temperature.Max());
            Console.WriteLine("Temperature MIN {0} °C", temperature.Min());
            Console.WriteLine("Weather simulation completed.");



            Console.WriteLine("Press any key to exit...");
            Console.ReadKey();

        }

        public static void PrintWeather(int[] temperature, string[] weatherConditions)
        {
            for (int i = 0; i < temperature.Length; i++)
            {
                if (temperature[i] < 0)
                {
                    weatherConditions[i] = "Snowy";
                }
                else if (temperature[i] < 20)
                {
                    weatherConditions[i] = "Cloudy";
                }
                else if (temperature[i] < 30)
                {
                    weatherConditions[i] = "Rainy";
                }
                else
                {
                    weatherConditions[i] = "Sunny";
                }
                Console.WriteLine($"Day {i + 1}: {temperature[i]}°C, {weatherConditions[i]}");
            }
        }

        public static void AverageTemperature(int[] temperature)
        {
            double average = 0;
            for (int i = 0; i < temperature.Length; i++)
            {
                average += temperature[i];
            }
            average /= temperature.Length;
            Console.WriteLine($"Average Temperature: {Math.Round(average,2)}°C");

        }
    }
}
