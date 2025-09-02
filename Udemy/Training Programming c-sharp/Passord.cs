using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Training_Programming_c_sharp
{
    interface IPassord
    {


        string setPassword(string pass);

        string GetPassword();

        bool VerifyPassword(string pass);
       
    }
}
