using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading;
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

namespace Task_WPF
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
        }

        private void Onbtn(object sender, RoutedEventArgs e)
        {
            Debug.WriteLine("Thread number : {0}", Thread.CurrentThread.ManagedThreadId);
            HttpClient httpClient = new HttpClient();
            var task = httpClient.GetStringAsync("https://www.google.com").Result;
            Debug.WriteLine("After GetStringAsync");
            btn.Content = "Done";
        }
    }
}
