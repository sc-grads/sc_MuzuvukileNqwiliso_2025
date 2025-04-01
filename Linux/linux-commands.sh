#!/bin/bash
# This script demonstrates the use of various Linux commands.

echo "Hello, World!"  # Print a message to the console
echo "Current date and time:"
date  # Display the current date and time
echo "Current working directory:"
pwd  # Print the current working directory
echo "List of files in the current directory:"
ls  # List files in the current directory
ls -l  # List files with detailed information
chmod +x linux-commands.sh  # Make the script executable
echo "File permissions for this script:"
ls -l linux-commands.sh  # Show file permissions
echo "Creating a new directory named 'test_dir':"   
mkdir test_dir  # Create a new directory
echo "Changing into 'test_dir' directory:"
cd test_dir  # Change into the new directory
echo "Current working directory after changing:"
pwd  # Print the current working directory again
echo "Creating a new file named 'test_file.txt':"
touch test_file.txt  # Create a new file
echo "Listing files in 'test_dir':"
ls  # List files in the current directory
echo "Writing 'Hello, Linux!' to 'test_file.txt':"
echo "Hello, Linux!" > test_file.txt  # Write to the file

if [ -f test_file.txt ]; then  # Check if the file exists
    echo "'test_file.txt' exists."
else
    echo "'test_file.txt' does not exist."
fi
echo "Reading contents of 'test_file.txt':"
cat test_file.txt  # Display the contents of the file
echo "Copying 'test_file.txt' to 'copy_test_file.txt':"
cp test_file.txt copy_test_file.txt  # Copy the file
echo "Listing files after copying:"
ls  # List files again
echo "Moving 'copy_test_file.txt' to 'moved_test_file.txt':"