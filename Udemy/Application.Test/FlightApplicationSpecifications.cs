using FluentAssertions;
using Data;
using Domain;
using Microsoft.EntityFrameworkCore;
namespace Application.Test
{
    public class FlightApplicationSpecifications
    {
        private readonly Entities entities = new Entities(new DbContextOptionsBuilder<Entities>().
                UseInMemoryDatabase("FlightsData").Options);

        private readonly BookingSerivce bookingService;

        public FlightApplicationSpecifications()
        {
            bookingService = new BookingSerivce(entities);
        }

        [Theory]
        [InlineData("alice@g.com",3)]
        [InlineData("bob@g.com",3)]
        public void Remember_bookings(string passangerEmail, int noBookedSeats)
        {
            // This creates a fake database called => 'FlightsData', is stored locally or inMemory

            var flight = new Flight(3);
            entities.Flights.Add(flight); // List of Flights => add new flight
            entities.SaveChanges();


        
            bookingService.Book(new BookDto(
               flightId: flight.Id, passangerEmail, noBookedSeats
                ));
            bookingService.FindBookings(flight.Id).
                            Should().
                            ContainEquivalentOf(new BookingRm(
                                passangerEmail, noBookedSeats
                                ));
        }


        [Theory]
        [InlineData(2)]
        [InlineData(10)]
        public void Frees_up_seasts_after_booking(int intialCapacity)
        {
            // Given
         
            var flight = new Flight(3);
            entities.Flights.Add(flight); // List of Flights => add new flight
            entities.SaveChanges();

            bookingService.Book(new BookDto(
              flightId: flight.Id, "alice@g.com", 3
               ));

            // When
            bookingService.CancelBooking(
                new CancelBookingDto(
                    Guid.NewGuid(),
                    "alice@g.com",
                    3
                    )
                );

            // Then

            bookingService.GetRemainingNumberOfSeats(flight.Id).Should().Be(intialCapacity);

        }

    }
}
