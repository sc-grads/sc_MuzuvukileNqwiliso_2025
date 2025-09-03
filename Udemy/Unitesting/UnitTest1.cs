using Domain;
using FluentAssertions;
namespace Unitesting
{
    public class UnitTest1
    {
        [Fact]
        // The name of the test method should describe the expected behavior
        public void Sum_of_2_and_2_should_be_4()=> new Calculator().Sum(2, 2).Should().Be(4);



    }
}
