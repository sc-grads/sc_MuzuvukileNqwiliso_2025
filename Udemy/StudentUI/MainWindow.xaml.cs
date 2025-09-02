using System.Windows;
using System.Data.SqlClient;
using System.Data;
using System;

namespace StudentUI
{
    public partial class MainWindow : Window
    {
        private readonly SqlConnection _sqlConnection;
        private readonly LinqToSqlDataContext _dataContext;

        public MainWindow()
        {
            InitializeComponent();

            string connectionString = Properties.Settings.Default.ZooDBConnectionString;

            if (string.IsNullOrEmpty(connectionString))
            {
                MessageBox.Show("Connection string is not set in application settings.");
                return;
            }

            try
            {
                _sqlConnection = new SqlConnection(connectionString);
                _dataContext = new LinqToSqlDataContext(_sqlConnection);
                _sqlConnection.Open();

            }
            catch (SqlException ex)
            {
                MessageBox.Show($"Failed to connect to database: {ex.Message}");
            }
        }

        public void InsertStudent(int studentid , string name, int age, string gender, int uniid)
        {
            if (_dataContext == null)
            {
                MessageBox.Show("Database connection is not initialized.");
                return;
            }
            try
            {
                Student newStudent = new Student
                {
                    StudentId = studentid, // Assuming StudentId is auto-generated
                    Name = name,
                    Age = age,
                    Gender = gender,
                    UniId = uniid
                };
                _dataContext.Student.InsertOnSubmit(newStudent);
                MessageBox.Show("Student inserted successfully.");
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error inserting student: {ex.Message}");
            }
        }
    }
}
