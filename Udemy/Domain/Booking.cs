using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Domain
{
    public class Booking(string passangerEmail, int numberOfSeats)
    {
        public string PassangerEmail { get; set; } = passangerEmail;
        public int NumberOfSeats { get; set; } = numberOfSeats;
    }
}
