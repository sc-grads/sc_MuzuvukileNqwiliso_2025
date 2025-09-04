using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;


namespace Domain
{
    [method: Obsolete("Needed by EF")]
    public partial class Flight(int numberOfSeats)
    {
        private List<Booking> _bookingList = new();

        public IEnumerable<Booking> Bookings => _bookingList;

        public int NumberOfSeats { get; set; } = numberOfSeats;

        public int RemaingingSeats { get; set; } = numberOfSeats;

        public Guid Id { get;}
        public object? BookSeats(string booker, int numberOfSeats)
        {

            if (numberOfSeats > RemaingingSeats)
            {
                return new OverBookingError();
            }

            _bookingList.Add(new Booking(booker, numberOfSeats));
            RemaingingSeats -= numberOfSeats;
            return null;
        }

        public object? CancelBookedSeats(string passanger, int cancelSeats)
        {
            if(!_bookingList.Any(booking=> booking.PassangerEmail == passanger))
            {
                return new BookingNotFoundError();
            }

            _bookingList.Remove(new Booking(passanger, cancelSeats));
            RemaingingSeats += cancelSeats;
            return null;
        }
    }

}
