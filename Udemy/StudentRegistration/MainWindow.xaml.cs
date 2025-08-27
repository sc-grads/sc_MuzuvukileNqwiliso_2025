using System;
using System.Data;
using System.Data.SqlClient;
using System.Windows;

namespace StudentRegistration
{
    public partial class MainWindow : Window
    {
        private readonly ConnectionDB _db;

        public MainWindow()
        {
            InitializeComponent();
            _db = new ConnectionDB();
        }

        private void RegisterButton_Click(object sender, RoutedEventArgs e)
        {
            if (!int.TryParse(txtStudentId.Text, out int id))
            {
                MessageBox.Show("Student ID must be numeric.");
                return;
            }

            if (string.IsNullOrWhiteSpace(txtName.Text) ||
                string.IsNullOrWhiteSpace(txtSurname.Text) ||
                string.IsNullOrWhiteSpace(txtAddress.Text) ||
                string.IsNullOrWhiteSpace(txtCity.Text) ||
                string.IsNullOrWhiteSpace(txtCellphone.Text))
            {
                MessageBox.Show("Please fill in all fields.");
                return;
            }

            try
            {
                _db.RegisterStudent(id, txtName.Text, txtSurname.Text, txtAddress.Text, txtCity.Text, txtCellphone.Text);
                MessageBox.Show("Student registered successfully!");
                ClearInputs();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error: {ex.Message}");
            }
        }

        private void DeleteButton_Click(object sender, RoutedEventArgs e)
        {
            if (!int.TryParse(txtStudentId.Text, out int id))
            {
                MessageBox.Show("Enter a valid numeric Student ID.");
                return;
            }

            try
            {
                _db.DeleteStudent(id);
                MessageBox.Show("Student deleted successfully!");
                ClearInputs();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error: {ex.Message}");
            }
        }

        private void ClearInputs()
        {
            txtStudentId.Clear();
            txtName.Clear();
            txtSurname.Clear();
            txtAddress.Clear();
            txtCity.Clear();
            txtCellphone.Clear();
        }

        private void UpdateButton_Click(object sender, RoutedEventArgs e)
        {
            if (!int.TryParse(txtStudentId.Text, out int id))
            {
                MessageBox.Show("Student ID must be numeric.");
                return;
            }

            if (string.IsNullOrWhiteSpace(txtName.Text) ||
                string.IsNullOrWhiteSpace(txtSurname.Text) ||
                string.IsNullOrWhiteSpace(txtAddress.Text) ||
                string.IsNullOrWhiteSpace(txtCity.Text) ||
                string.IsNullOrWhiteSpace(txtCellphone.Text))
            {
                MessageBox.Show("Please fill in all fields before updating.");
                return;
            }

            try
            {
                _db.UpdateStudent(id, txtName.Text, txtSurname.Text,
                                  txtAddress.Text, txtCity.Text, txtCellphone.Text);

                MessageBox.Show("Student updated successfully!");
                ClearInputs();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error updating student: {ex.Message}");
            }
        }

        private void ReadButton_Click(object sender, RoutedEventArgs e)
        {
            StudentData studentData = new StudentData();
            studentData.Show();
        }
    }

    public class ConnectionDB
    {
        private readonly SqlConnection _connection;
        private const string ConnStr = @"Data Source=.;Initial Catalog=StudentRegSambedb;Integrated Security=True;TrustServerCertificate=True";

        public ConnectionDB()
        {
            _connection = new SqlConnection(ConnStr);
        }

        public void OpenConnection()
        {
            if (_connection.State != ConnectionState.Open)
                _connection.Open();
        }

        public void CloseConnection()
        {
            if (_connection.State == ConnectionState.Open)
                _connection.Close();
        }

        public void RegisterStudent(int id, string name, string surname, string address, string city, string cellphone)
        {
            string query = @"INSERT INTO StudentRegs (StudentId, Name, Surname, Address, City, Cellphone)
                             VALUES (@Id, @Name, @Surname, @Address, @City, @Cellphone)";

            var cmd = new SqlCommand(query, _connection);
            cmd.Parameters.AddWithValue("@Id", id);
            cmd.Parameters.AddWithValue("@Name", name);
            cmd.Parameters.AddWithValue("@Surname", surname);
            cmd.Parameters.AddWithValue("@Address", address);
            cmd.Parameters.AddWithValue("@City", city);
            cmd.Parameters.AddWithValue("@Cellphone", cellphone);

            OpenConnection();
            cmd.ExecuteNonQuery();
            CloseConnection();
        }

        public void DeleteStudent(int id)
        {
            string query = "DELETE FROM StudentRegs WHERE StudentId = @Id";

            var cmd = new SqlCommand(query, _connection);
            cmd.Parameters.AddWithValue("@Id", id);

            OpenConnection();
            int rows = cmd.ExecuteNonQuery();
            CloseConnection();

            if (rows == 0)
                throw new Exception("No student found with that ID.");
        }

        public void UpdateStudent(int id, string name, string surname, string address, string city, string cellphone)
        {
            string query = @"UPDATE StudentRegs
                             SET Name=@Name, Surname=@Surname, Address=@Address, City=@City, Cellphone=@Cellphone
                             WHERE StudentId=@Id";

            var cmd = new SqlCommand(query, _connection);
            cmd.Parameters.AddWithValue("@Id", id);
            cmd.Parameters.AddWithValue("@Name", name);
            cmd.Parameters.AddWithValue("@Surname", surname);
            cmd.Parameters.AddWithValue("@Address", address);
            cmd.Parameters.AddWithValue("@City", city);
            cmd.Parameters.AddWithValue("@Cellphone", cellphone);

            OpenConnection();
            int rows = cmd.ExecuteNonQuery();
            CloseConnection();

            if (rows == 0)
                throw new Exception("No student found to update.");
        }

        public void DisplayStudentData()
        {
            string query = @"SELECT * FROM StudentRegs";

            var cmd = new SqlCommand(query, _connection);
            
        }
    }
}
