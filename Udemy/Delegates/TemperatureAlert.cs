using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Delegates
{
    internal class TemperatureAlert
    {
        public void HandleTemperatureChange(string message)
        {
            Console.WriteLine( message);
        }
    }
}
