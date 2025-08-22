using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace TodoList_App
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

        private void AddButton_Click(object sender, RoutedEventArgs e)
        {
            string item = TodoTextInput.Text.Trim();

            if (!string.IsNullOrEmpty(item))
            {
                TaskList.Children.Add(new TextBlock
                {
                    Text = item,
                    Margin = new Thickness(5),
                    FontSize = 16,
                    Foreground = new SolidColorBrush(Color.FromRgb(255,255,255)),
                    
                });

                // Fix: Clear the TextBox input instead of attempting to call Clear on a TextBlock
                TodoTextInput.Text = string.Empty;
            }
            else
            {
                MessageBox.Show("Please enter a valid todo item.", "Input Error", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }
    }
}