#!/bin/bash

# 1. Navigation
pwd                  # Show current directory
ls                   # List files
ls -l                # List files with details
cd ~                 # Go to home directory
cd ..                # Go up one directory

# 2. File Operations
touch file.txt       # Create empty file
echo "Hello" > file.txt  # Write to file
cat file.txt         # View file contents
cp file.txt copy.txt # Copy file
mv copy.txt moved.txt # Rename/move file
rm moved.txt         # Remove file

# 3. Directory Operations
mkdir test_dir       # Create directory
cd test_dir          # Enter directory
touch test_file      # Create file in new directory
cd ..                # Go back
rmdir test_dir       # Remove EMPTY directory
rm -r test_dir       # Remove directory and contents (if not empty)

# 4. System Info
date                 # Show current date/time
whoami               # Show current user
df -h                # Show disk space
free -h              # Show memory usage

# 5. Help
man ls               # View manual (press 'q' to quit)
ls --help            # Brief command help
