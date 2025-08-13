using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Threading.Tasks;

namespace c_sharp.Game
{
    internal class AdventureGame
    {
        private readonly Random _random = new Random();

        public void Game()
        {
            Console.WriteLine("Welcome to the Adventure Game!");

            // Player setup
            var (name, type, health) = SetupPlayer();

            Console.WriteLine($"\n{name} the {type}, you find yourself at the edge of a dark forest!");
            Console.WriteLine("Do you want to (enter/camp)?");

            string choice = Console.ReadLine()?.ToLower() ?? "";

            if (choice == "enter")
            {
                ExploreForest(name, type, ref health);
            }
            else
            {
                Console.WriteLine("\nYou've decided to camp outside the forest. As night falls, you hear strange noises...");
                Console.WriteLine("In the morning, the forest entrance has mysteriously vanished. Your adventure ends here.");
            }

            Console.WriteLine("\nGame Over!");
            Console.WriteLine("Thank you for playing!");
        }

        private (string name, string type, int health) SetupPlayer()
        {
            Console.WriteLine("\nWhat is your name, adventurer?");
            string name = Console.ReadLine()?.Trim() ?? "Unknown";

            string type;
            while (true)
            {
                Console.WriteLine("\nChoose your character type (Warrior, Wizard, Archer):");
                type = Console.ReadLine()?.ToLower()?.Trim() ?? "";

                if (new[] { "warrior", "wizard", "archer" }.Contains(type))
                    break;

                Console.WriteLine("Invalid choice. Please select Warrior, Wizard, or Archer.");
            }

            int health = type switch
            {
                "warrior" => 120,
                "wizard" => 80,
                "archer" => 100,
                _ => 100
            };

            Console.WriteLine($"\nWelcome {name} the {type}! You have {health} health points.");
            return (name, type, health);
        }

        private void ExploreForest(string name, string type, ref int health)
        {
            Console.WriteLine("\nYou step into the dark forest. The trees loom overhead, blocking most of the sunlight.");

            bool hasTreasure = false;
            bool inForest = true;

            while (inForest && health > 0)
            {
                Console.WriteLine("\nDo you want to go (left/right/back)?");
                string direction = Console.ReadLine()?.ToLower()?.Trim() ?? "";

                switch (direction)
                {
                    case "left":
                        ExploreLeftPath(ref health, ref hasTreasure);
                        break;

                    case "right":
                        ExploreRightPath(name, type, ref health, ref hasTreasure);
                        break;

                    case "back":
                        Console.WriteLine("\nYou decide to retreat from the forest.");
                        if (hasTreasure)
                        {
                            Console.WriteLine($"\n{name} returns safely with treasure! You win!");
                        }
                        else
                        {
                            Console.WriteLine("\nYou leave the forest empty-handed.");
                        }
                        inForest = false;
                        break;

                    default:
                        Console.WriteLine("\nYou hesitate and lose time. Night is approaching...");
                        break;
                }

                // Random forest event
                if (inForest && health > 0 && _random.Next(1, 4) == 1)
                {
                    TriggerRandomEvent(name, ref health);
                }
            }

            if (health <= 0)
            {
                Console.WriteLine($"\n{name} has been defeated in the forest...");
            }
        }

        private void ExploreLeftPath(ref int health, ref bool hasTreasure)
        {
            Console.WriteLine("\nYou take the left path and find a small clearing.");

            if (!hasTreasure && _random.Next(1, 3) == 1)
            {
                Console.WriteLine("There's a treasure chest here! You open it and find gold!");
                hasTreasure = true;
            }
            else
            {
                Console.WriteLine("The clearing is peaceful but empty. You rest and recover some health.");
                health = Math.Min(health + 20, 120);
                Console.WriteLine($"Your health is now {health}");
            }
        }

        private void ExploreRightPath(string name, string type, ref int health, ref bool hasTreasure)
        {
            Console.WriteLine("\nYou take the right path and encounter a wild beast!");
            Console.WriteLine("Do you want to (fight/flee)?");

            string choice = Console.ReadLine()?.ToLower()?.Trim() ?? "";

            if (choice == "fight")
            {
                int attackPower = type switch
                {
                    "warrior" => _random.Next(15, 25),
                    "wizard" => _random.Next(10, 30),
                    "archer" => _random.Next(12, 22),
                    _ => _random.Next(10, 20)
                };

                Console.WriteLine($"\nYou attack the beast with {attackPower} power!");

                if (attackPower > 18)
                {
                    Console.WriteLine("You defeat the beast!");

                    if (_random.Next(1, 3) == 1)
                    {
                        Console.WriteLine("The beast was guarding a treasure! You found gold!");
                        hasTreasure = true;
                    }
                }
                else
                {
                    int damage = _random.Next(10, 30);
                    health -= damage;
                    Console.WriteLine($"The beast fights back! You take {damage} damage. Health: {health}");
                }
            }
            else
            {
                if (_random.Next(1, 3) == 1)
                {
                    Console.WriteLine("You successfully flee from the beast!");
                }
                else
                {
                    int damage = _random.Next(5, 15);
                    health -= damage;
                    Console.WriteLine($"The beast attacks as you flee! You take {damage} damage. Health: {health}");
                }
            }
        }

        private void TriggerRandomEvent(string name, ref int health)
        {
            int eventType = _random.Next(1, 5);

            switch (eventType)
            {
                case 1:
                    Console.WriteLine("\nYou hear strange whispers in the wind...");
                    break;
                case 2:
                    Console.WriteLine("\nA sudden gust of wind chills you to the bone.");
                    break;
                case 3:
                    int healthChange = _random.Next(-10, 15);
                    health += healthChange;

                    if (healthChange > 0)
                    {
                        Console.WriteLine($"\nYou find some healing herbs! +{healthChange} health. Now: {health}");
                    }
                    else if (healthChange < 0)
                    {
                        Console.WriteLine($"\nYou step on a thorn! {healthChange} health. Now: {health}");
                    }
                    break;
                case 4:
                    Console.WriteLine("\nYou see mysterious glowing eyes watching you from the darkness...");
                    break;
            }
        }
    }
}