using FluentAssertions;
using Domain;
namespace FlightUnitTests
{
    public class FlightTest
    {
        [Theory]
        [InlineData(4,1,2)]
        public void Book_flight_reduced_by_number_of_bookings(int flightSeats, int numberOfSeats, int remainingSeats)
        {
            // If the number of seats booked is less than the available seats then the remaining seats should be reduced by the number of seats booked
            // if the booked seats returns null then the booking was successful
            // if the booking seats returns overbooking error then the booking was not successful
            var flightManager = new Flight(numberOfSeats:flightSeats);
            flightManager.BookSeats("Alice", numberOfSeats);
            flightManager.BookSeats("Bob", numberOfSeats);
            flightManager.RemaingingSeats.Should().Be(remainingSeats);
        }

        [Theory] // Test with different data sets
        [InlineData(2,4)] // Booking more seats than available
        public void Booking_more_seats_than_available_should_throw(int flightSeats, int numberOfSeats)
        {
            // If the booking of the seas is more than the available seats then an OverBookingError should be returned
            // If the booking is successful then null should be returned
            var flightManager = new Flight(numberOfSeats: flightSeats);
            var error = flightManager.BookSeats("Alice", numberOfSeats);
            error.Should().BeOfType<OverBookingError>();
        }

        [Theory]
        [InlineData(4, 3)]
        public void Booking_has_been_successful_should(int flightSeats, int numberOfSeats)
        {
            // If the booking of flight returns null then the booking was successful
            // if it returns an error object then the booking was not successful
            var flightManager = new Flight(numberOfSeats: flightSeats);
            var error = flightManager.BookSeats("Alice", numberOfSeats);
            error.Should().BeNull();
        }

        [Fact]
        public void Rember_bookings()
        {
      
            var flight = new Flight(10);
            flight.BookSeats("Alice", 3);
            // this must be in a list provided to the flight
            // these are passangers who have booked the flight
            // if one of them is not in the list then the test will fail
            flight.Bookings.Should().ContainEquivalentOf(new Booking("Alice", 3));

        }

        [Theory]
        [InlineData(10,4,2,8)]
        [InlineData(4,2,2,4)]

        public void Cencel_booking_seats_remaining_should_be(int intialSeats, int bookedSeats, int cancelSeats, int remainderSeats)
        {
            var flight = new Flight(numberOfSeats: intialSeats);
            flight.BookSeats("Alice", bookedSeats);
            flight.CancelBookedSeats("Alice",cancelSeats);
            flight.RemaingingSeats.Should().Be(remainderSeats);
        }

        [Fact]
        public void Doesnt_cancel_bookings_for_passangers_who_have_not_booked()
        {
            var flight = new Flight(numberOfSeats: 3);
            var error = flight.CancelBookedSeats(passanger: "Alice", cancelSeats: 1);
            error.Should().BeOfType<BookingNotFoundError>();
        }

        [Fact]
        public void Returns_null_when_successfully_cancels_a_booking_seats()
        {
            var flight = new Flight(numberOfSeats: 3);
            flight.BookSeats(booker: "Alice", numberOfSeats: 2);
            var error = flight.CancelBookedSeats(passanger: "Alice", cancelSeats: 1);
            error.Should().BeNull();
        }
    }
}
