using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CleanCode
{
    internal class LRP
    {



    }

    public class Bird
    {
        public virtual void MakeSound()
        {
            Console.WriteLine("Chirp Chirp");
        }
    }

    public interface IFlyable
    {
        void Fly();
    }

    public interface ISwimmable
    {
        void Swim();
    }

    /// <summary>
    /// This class represents a Sparrow, which is a type of Bird that can fly but cannot swim.
    /// </summary>
    public class Sparrow : Bird,IFlyable
    {
        public void Fly()
        {
            Console.WriteLine("The sparrow is flying.");
        }

        public override void MakeSound()
        {
            Console.WriteLine("Chirp Chirp");
        }
    }

    /// <summary>
    /// This class represents a Penguin, which is a type of Bird that can swim but cannot fly.
    /// </summary>

    public class Penguin : Bird,ISwimmable
    {
        public void Swim()
        {
            Console.WriteLine("The penguin is swimming.");
        }
        public override void MakeSound()
        {
            Console.WriteLine("Honk Honk");
        }
    }

}
