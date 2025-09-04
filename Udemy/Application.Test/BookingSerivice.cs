using Data;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Application.Test
{
    public class BookingSerivce
    {

        public Entities Entities { get; set; }


        public BookingSerivce(Entities entities)
        {

            Entities = entities;

        }

        public void Book(BookDto bookDto)
        {
            var flight = Entities.Flights.Find(bookDto.FlightId);
            flight.BookSeats(bookDto.PassangerEmail, bookDto.NoBookedSeats);
            Entities.SaveChanges();
        }

        public IEnumerable<BookingRm> FindBookings(Guid Id)
        {
            return Entities.Flights.
                 Find(Id).
                 Bookings.
                 Select
                 (booking =>
                 new BookingRm(booking.PassangerEmail, booking.NumberOfSeats
                 ));
        }

        internal void CancelBooking(CancelBookingDto cancelBookingDto)
        {
            var flight = Entities.Flights.Find(cancelBookingDto);
            flight.CancelBookedSeats(cancelBookingDto.PassangerEmail,cancelBookingDto.NoBookedSeasts);
            Entities.SaveChanges();
          
        }

        internal object GetRemainingNumberOfSeats(Guid Id)
        {
            return Entities.Flights.Find(Id).RemaingingSeats;
        }
    }
}
