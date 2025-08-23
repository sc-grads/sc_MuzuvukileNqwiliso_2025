using System;
using System.Data;
using System.Data.SqlClient;
using System.Configuration;
using System.Windows;
using System.Windows.Controls;

namespace Zoo
{
    public partial class MainWindow : Window
    {
        SqlConnection con;
        public MainWindow()
        {
            InitializeComponent();
            string connectionString = ConfigurationManager.ConnectionStrings["Zoo.Properties.Settings.ZooDBConnectionString"].ConnectionString;
            con = new SqlConnection(connectionString);
            if (con.State == ConnectionState.Closed)
            {
                con.Open();
            }
            ShowZoos();
            ShowAnimals();
        }

        private void ShowZoos()
        {
            try
            {
                string query = "SELECT * FROM Zoo";
                SqlDataAdapter adapter = new SqlDataAdapter(query, con);
                DataTable zooTable = new DataTable();
                adapter.Fill(zooTable);
                ZoosListBox.ItemsSource = zooTable.DefaultView;
                ZoosListBox.SelectedValuePath = "Id";
                ZoosListBox.DisplayMemberPath = "Location";
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        private void ShowAnimals()
        {
            try
            {
                string query = "SELECT * FROM Animal";
                SqlDataAdapter adapter = new SqlDataAdapter(query, con);
                DataTable animalTable = new DataTable();
                adapter.Fill(animalTable);
                AnimalsListBox.ItemsSource = animalTable.DefaultView;
                AnimalsListBox.SelectedValuePath = "Id";
                AnimalsListBox.DisplayMemberPath = "Name";
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        private void ShowAssociatedAnimals()
        {
            try
            {
                if (ZoosListBox.SelectedValue == null) return;

                string query = @"SELECT a.Id, a.Name 
                                 FROM Animal a 
                                 INNER JOIN ZooAnimal za ON a.Id = za.AnimalId 
                                 WHERE za.ZooId = @ZooId";
                SqlCommand cmd = new SqlCommand(query, con);
                cmd.Parameters.AddWithValue("@ZooId", ZoosListBox.SelectedValue);
                SqlDataAdapter adapter = new SqlDataAdapter(cmd);
                DataTable zooAnimals = new DataTable();
                adapter.Fill(zooAnimals);
                ZoosWithAnimalsListBox.ItemsSource = zooAnimals.DefaultView;
                ZoosWithAnimalsListBox.SelectedValuePath = "Id";
                ZoosWithAnimalsListBox.DisplayMemberPath = "Name";
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        private void onSelectedZoo(object sender, SelectionChangedEventArgs e)
        {
            ShowAssociatedAnimals();
        }

        private void onAddZoo(object sender, RoutedEventArgs e)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(SharedNameTextBox.Text))
                {
                    MessageBox.Show("Enter a Zoo Name.");
                    return;
                }

                string query = "INSERT INTO Zoo (Location) VALUES (@Location)";
                SqlCommand cmd = new SqlCommand(query, con);
                cmd.Parameters.AddWithValue("@Location", SharedNameTextBox.Text.Trim());
                cmd.ExecuteNonQuery();

                SharedNameTextBox.Clear();
                ShowZoos();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        private void onDeleteZoo(object sender, RoutedEventArgs e)
        {
            try
            {
                if (ZoosListBox.SelectedValue == null)
                {
                    MessageBox.Show("Select a Zoo to delete.");
                    return;
                }

                string query = "DELETE FROM Zoo WHERE Id=@Id";
                SqlCommand cmd = new SqlCommand(query, con);
                cmd.Parameters.AddWithValue("@Id", ZoosListBox.SelectedValue);
                cmd.ExecuteNonQuery();

                ShowZoos();
                ZoosWithAnimalsListBox.ItemsSource = null;
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        private void onAddAnimal(object sender, RoutedEventArgs e)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(SharedNameTextBox.Text))
                {
                    MessageBox.Show("Enter an Animal Name.");
                    return;
                }

                string query = "INSERT INTO Animal (Name) VALUES (@Name)";
                SqlCommand cmd = new SqlCommand(query, con);
                cmd.Parameters.AddWithValue("@Name", SharedNameTextBox.Text.Trim());
                cmd.ExecuteNonQuery();

                SharedNameTextBox.Clear();
                ShowAnimals();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        private void onDeleteAnimal(object sender, RoutedEventArgs e)
        {
            try
            {
                if (AnimalsListBox.SelectedValue == null)
                {
                    MessageBox.Show("Select an Animal to delete.");
                    return;
                }

                string query = "DELETE FROM Animal WHERE Id=@Id";
                SqlCommand cmd = new SqlCommand(query, con);
                cmd.Parameters.AddWithValue("@Id", AnimalsListBox.SelectedValue);
                cmd.ExecuteNonQuery();

                ShowAnimals();
                ShowAssociatedAnimals();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        private void onAddAnimalToZoo(object sender, RoutedEventArgs e)
        {
            try
            {
                if (ZoosListBox.SelectedValue == null || AnimalsListBox.SelectedValue == null)
                {
                    MessageBox.Show("Select both a Zoo and an Animal.");
                    return;
                }

                string query = "INSERT INTO ZooAnimal (ZooId, AnimalId) VALUES (@ZooId, @AnimalId)";
                SqlCommand cmd = new SqlCommand(query, con);
                cmd.Parameters.AddWithValue("@ZooId", ZoosListBox.SelectedValue);
                cmd.Parameters.AddWithValue("@AnimalId", AnimalsListBox.SelectedValue);
                cmd.ExecuteNonQuery();

                ShowAssociatedAnimals();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        private void onUpdateZoo(object sender, RoutedEventArgs e)
        {
            try
            {
                if (ZoosListBox.SelectedValue == null || string.IsNullOrWhiteSpace(SharedNameTextBox.Text))
                {
                    MessageBox.Show("Select a Zoo and enter a new name.");
                    return;
                }

                string query = "UPDATE Zoo SET Location=@Location WHERE Id=@Id";
                SqlCommand cmd = new SqlCommand(query, con);
                cmd.Parameters.AddWithValue("@Location", SharedNameTextBox.Text.Trim());
                cmd.Parameters.AddWithValue("@Id", ZoosListBox.SelectedValue);
                cmd.ExecuteNonQuery();

                SharedNameTextBox.Clear();
                ShowZoos();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        private void onUpdateAnimal(object sender, RoutedEventArgs e)
        {
            try
            {
                if (AnimalsListBox.SelectedValue == null || string.IsNullOrWhiteSpace(SharedNameTextBox.Text))
                {
                    MessageBox.Show("Select an Animal and enter a new name.");
                    return;
                }

                string query = "UPDATE Animal SET Name=@Name WHERE Id=@Id";
                SqlCommand cmd = new SqlCommand(query, con);
                cmd.Parameters.AddWithValue("@Name", SharedNameTextBox.Text.Trim());
                cmd.Parameters.AddWithValue("@Id", AnimalsListBox.SelectedValue);
                cmd.ExecuteNonQuery();

                SharedNameTextBox.Clear();
                ShowAnimals();
                ShowAssociatedAnimals();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }
    }
}
