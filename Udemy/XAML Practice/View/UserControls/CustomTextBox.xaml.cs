using System;
using System.Collections.Generic;
using System.Linq;
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

namespace XAML_Practice.View.UserControls
{
    /// <summary>
    /// Interaction logic for CustomTextBox.xaml
    /// </summary>
    public partial class CustomTextBox : UserControl
    {
        public CustomTextBox()
        {
            InitializeComponent();
        }

        private string _placeholder;

        public string Placeholder
        {
            get { return _placeholder; }
            set {
                _placeholder = value;
                 tbPlaceholder.Text = _placeholder;
            }
        }


        private void clearControl(object sender, RoutedEventArgs e)
        {
            txtControl.Text = string.Empty;
            txtControl.Focus();
        }

        private void txtControl_TextChanged(object sender, TextChangedEventArgs e)
        {
            if(txtControl.Text != string.Empty)
            {
                tbPlaceholder.Visibility = Visibility.Hidden;
            }else
            {
                tbPlaceholder.Visibility = Visibility.Visible;
            }
        }
    }
}
