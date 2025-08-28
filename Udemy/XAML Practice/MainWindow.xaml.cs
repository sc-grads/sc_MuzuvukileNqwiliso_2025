using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using XAML_Practice.View.UserControls;


namespace XAML_Practice
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window, INotifyPropertyChanged
    {

        private string _name;

        public event PropertyChangedEventHandler PropertyChanged;

        public string Name
        {
            get { return _name; }
            set
            {

                _name = value;
                PropertyChanged?.Invoke(this, new PropertyChangedEventArgs("Name"));
            }
        }

        public MainWindow()
        {
            DataContext = this;
            InitializeComponent();
            this.SourceInitialized += MainWindow_SourceInitialized;
         
        }

        private void MainWindow_SourceInitialized(object sender, EventArgs e)
        {
            var hwnd = new WindowInteropHelper(this).Handle;

            // DWMWINDOWATTRIBUTE = 33 means corner preference
            const int DWMWA_WINDOW_CORNER_PREFERENCE = 33;
            // DWM_WINDOW_CORNER_PREFERENCE enum values
            const int DWMWCP_DEFAULT = 0;
            const int DWMWCP_DONOTROUND = 1;
            const int DWMWCP_ROUND = 2;
            const int DWMWCP_ROUNDSMALL = 3;

            int preference = DWMWCP_DONOTROUND; // force square corners
            DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                ref preference, sizeof(int));
        }

        [DllImport("dwmapi.dll")]
        private static extern int DwmSetWindowAttribute(
            IntPtr hwnd,
            int attr,
            ref int attrValue,
            int attrSize);

       
    }

}