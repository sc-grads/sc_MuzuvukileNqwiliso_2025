using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;


namespace Domain
{
    public class FlightManager(int numberOfSeats)
    {

        public int NumberOfSeats { get; set; } = numberOfSeats;

        public int RemaingingSeats { get; set; } = numberOfSeats;

        public object? BookSeats(string booker, int numberOfSeats)
        {

            if (numberOfSeats > RemaingingSeats)
            {
                return new OverBookingError();
            }

            RemaingingSeats -= numberOfSeats; // 2 - 1 = 1 if the number of seats that should be remaining are above what is expected then there is a problem
            return null;
        }

    }
}
