using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace LoginApp
{
    /// <summary>
    /// Interaction logic for LoginView.xaml
    /// </summary>
    public partial class LoginView : UserControl
    {
        public LoginView()
        {
            InitializeComponent();
            LoginButton.IsEnabled = false;

        }

        private void LoginButton_Click(object sender, RoutedEventArgs e)
        {
            string? envVaraible = Environment.GetEnvironmentVariable("InvoiceManagement");
            var password = PasswordBox.Password;

            if (envVaraible != null)
            {
                if (envVaraible == password)
                {
                    MessageBox.Show("Login Successful");
                }else
                {
                   MessageBox.Show("Login Failed");
                }
            }else
            {
               MessageBox.Show("Environment variable not set");
            }
        }

        private void OnPasswordChanged(object sender, RoutedEventArgs e)
        {
            LoginButton.IsEnabled = !string.IsNullOrEmpty(PasswordBox.Password);
        }
    }
}
