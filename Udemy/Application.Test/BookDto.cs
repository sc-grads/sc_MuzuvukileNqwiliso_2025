using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Application.Test
{
    public class BookDto
    {
        public Guid FlightId { get; set; }

        public string PassangerEmail { get; set; }

        public int NoBookedSeats { get; set; }

        public BookDto(Guid flightId, string passangerEmail, int noBookedSeats)
        {
            FlightId = flightId;
            PassangerEmail = passangerEmail;
            NoBookedSeats = noBookedSeats;
        }
    }
}
