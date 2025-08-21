using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Delegates
{
    internal class TemperatureMonitor
    {

      public delegate void TemperatureChangedHandler(string message);
      
        private double _temperature;

        public double Temperature
        {
            get { return _temperature; }
            set
            {
                _temperature = value;
                if(_temperature > 30)
                {
                    // RAISE EVENT!!
                    RaiseTemperatureChangedEvent($"Warning: High temperature detected: {_temperature}°C");
                }else
                {
                    RaiseTemperatureChangedEvent($"Temperature is normal: {_temperature}°C");
                }
            }
        }

        public event TemperatureChangedHandler? OnTemperatureChanged;

        public void RaiseTemperatureChangedEvent(string message)
        {
            if (OnTemperatureChanged != null)
            {
                OnTemperatureChanged?.Invoke(message);
            }
        }
    }

   
}
