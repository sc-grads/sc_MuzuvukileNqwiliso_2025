using System;
using System.ComponentModel;
using System.Windows;

namespace Data_Binding.Model
{
    public class Person : INotifyPropertyChanged
    {
        private string _name;
        private int _age;

        public delegate void ErrorHandler(string message);
        public event ErrorHandler? OnErrorOccurred;

        public event PropertyChangedEventHandler? PropertyChanged;


        private void OnPropertyChanged(string propertyName) =>
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));

        public void RaiseError(string message)
        {
            OnErrorOccurred?.Invoke(message);
        }

        // --- Validation methods ---
        public string? ValidateName()
        {
            return string.IsNullOrWhiteSpace(Name) ? "Invalid Name" : null;
        }

        public string? ValidateAge()
        {
            return Age < 0 ? "Invalid Age" : null;
        }

        // --- Properties ---
        public string Name
        {
            get => _name;
            set
            {
                if (_name != value)
                {
                    _name = value ?? throw new ArgumentNullException(nameof(value), "Name cannot be null");
                    OnPropertyChanged(nameof(Name));
                }
            }
        }

        public int Age
        {
            get => _age;
            set
            {
                if (_age != value)
                {
                    _age = value;
                    OnPropertyChanged(nameof(Age));
                }
            }
        }

        // Constructor
        public Person()
        {
            _name = "";
            _age = 0;
        }
    }

    // Example subclass using the error event
    public class PersonWithValidation : Person
    {
        public PersonWithValidation()
        {
            OnErrorOccurred += (message) =>
                MessageBox.Show($"Error: {message}", "Validation Error");
        }
    }
}
