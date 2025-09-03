using Microsoft.AspNetCore.Mvc;
namespace WebApp.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class CalculatorController : ControllerBase
    {
    

        [HttpGet(Name = "Add({num1}/{num2})")]
        public int Get(int num1, int num2)=> num1 + num2;

    }
}
