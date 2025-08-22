using Data_Binding.Model;
using System.Windows;

namespace Data_Binding
{
    public partial class MainWindow : Window
    {
        private readonly Person person = new();
       

        public MainWindow()
        {
            InitializeComponent();
            this.DataContext = person; // Bind UI directly to Person
        }

        private void Button_Click(object sender, RoutedEventArgs e)
        {
            var nameError = person.ValidateName();
            var ageError = person.ValidateAge();

            if (!string.IsNullOrEmpty(nameError))
            {
                person.RaiseError(nameError);
                MessageBox.Show(nameError, "Invalid Name", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (!string.IsNullOrEmpty(ageError))
            {
                person.RaiseError(ageError);
                MessageBox.Show(ageError, "Invalid Age", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            MessageBox.Show($"Name: {person.Name}, Age: {person.Age}", "Person Info",
                            MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void ShowListBoxWindow_Click(object sender, RoutedEventArgs e)
        {
            this.Hide(); // Hide MainWindow
            var listBoxWindow = new ListBoxWindow();
            listBoxWindow.ShowDialog(); // Show ListBoxWindow modally
            this.Show(); // Show MainWindow again after ListBoxWindow is closed
        }
    }
}
