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
using System.Windows.Shapes;
using Data_Binding.Model;

namespace Data_Binding
{
    /// <summary>
    /// Interaction logic for ListBoxWindow.xaml
    /// </summary>
    public partial class ListBoxWindow : Window
    {

        public List<Person> people = new List<Person>
        {
            new Person { Name = "Alice", Age = 25 },
            new Person { Name = "Bob", Age = 30 },
            new Person { Name = "Charlie", Age = 35 },
            new Person { Name = "Diana", Age = 28 },
            new Person { Name = "Ethan", Age = 22 },
        };

        public ListBoxWindow()
        {
            InitializeComponent();
            PeopleListBox.ItemsSource = people;
        }

        private void AddPersonButton_Click(object sender, RoutedEventArgs e)
        {
            var people = PeopleListBox.SelectedItems;
            foreach (var person in people)
            {
                //var p = (Person)person;
                if (person is Person p) // the is casting of the object to Person type == if the person is the object of Person type
                {
                    MessageBox.Show($"Name: {p.Name}, Age: {p.Age}", "Selected Person",
                                    MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
        }

        //private void PeopleListBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        //{
        //    var person = (Person)PeopleListBox.SelectedItem;
        //    var fullname = person?.Name ?? "No one"; // null-coalescing operator
        //    var age = person?.Age.ToString() ?? "N/A";  

       
        //}
    }
}
