#!/bin/bash

# Function to run Python tests
run_tests() {
    echo "Running tests..."
    python -m unittest discover -p '*_test.py' tests/
    return $?
}

# Install dependencies using pip
echo "Installing dependencies..."
pip install -r requirements.txt

# Run tests
run_tests
exit_code=$?

# Check if tests passed
if [ $exit_code -ne 0 ]; then
    read -p "Tests failed. Aborting..."
    exit $exit_code
else
    echo "Tests passed. Proceeding with installation."
fi

# Execute server.py script
echo "Running server.py script..."
python server.py
