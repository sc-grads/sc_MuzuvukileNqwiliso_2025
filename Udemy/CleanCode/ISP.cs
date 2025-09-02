using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CleanCode
{
    internal class ISP
    {
    }

    /// <summary>
    /// Reresents a worker that can perform work.
    /// </summary>

    public interface IWorker
    {
        void Work();
    }

    /// <summary>
    /// Represents an entity that can be fed.
    /// </summary>


   
    public interface IFeedable
    {
        void Eat();
    }

    public class Human : IWorker, IFeedable
    {
        public void Work()
        {
            Console.WriteLine("Human is working.");
        }
        public void Eat()
        {
            Console.WriteLine("Human is eating.");
        }
    }

  
     public class Robot : IWorker
    {
        public void Work()
        {
            Console.WriteLine("Robot is working.");
        }
    }

}
