using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Application.Test
{
    public class BookingRm
    {
        public string PassangerEmail { get; set; }

        public int NoBookedSeats { get; set; }

        public BookingRm(string passangerEmail, int noBookedSeats)
        {
            PassangerEmail = passangerEmail;
            NoBookedSeats = noBookedSeats;
        }
    }
}
