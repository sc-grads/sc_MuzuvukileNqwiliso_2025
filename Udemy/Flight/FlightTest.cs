using FluentAssertions;
using Domain;
namespace Flight
{
    public class FlightTest
    {
        [Fact]
        public void Book_flight_reduced_by_number_of_bookings()
        {
            // If the number of seats booked is less than the available seats then the remaining seats should be reduced by the number of seats booked
            // if the booked seats returns null then the booking was successful
            // if the booking seats returns overbooking error then the booking was not successful
            var flightManager = new Domain.FlightManager(numberOfSeats: 4);
            flightManager.BookSeats("Alice", 1);
            flightManager.BookSeats("Bob", 1);
            flightManager.RemaingingSeats.Should().Be(2);
        }

        [Fact]
        public void Booking_more_seats_than_available_should_throw()
        {
            // If the booking of the seas is more than the available seats then an OverBookingError should be returned
            // If the booking is successful then null should be returned
            var flightManager = new Domain.FlightManager(numberOfSeats: 2);
            var error = flightManager.BookSeats("Alice", 4);
            error.Should().BeOfType<OverBookingError>();
        }

        [Fact]
       
        public void Booking_has_been_successful_should()
        {
            // If the booking of flight returns null then the booking was successful
            // if it returns an error object then the booking was not successful
            var flightManager = new Domain.FlightManager(numberOfSeats: 2);
            var error = flightManager.BookSeats("Alice", 1);
            error.Should().BeNull();
        }

    }
}
