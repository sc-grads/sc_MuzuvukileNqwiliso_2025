namespace Application.Test
{
    internal class CancelBookingDto
    {
        public Guid FlightId;

        public string PassangerEmail;

        public int NoBookedSeasts;

        public CancelBookingDto(Guid flightId, string passangerEmail, int noBookedSeats)
        {
            FlightId = flightId;
            PassangerEmail = passangerEmail;
            NoBookedSeasts = noBookedSeats;
        }
    }
}