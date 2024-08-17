#!/bin/bash

echo "Activating virtual environment..."
source ./venv/bin/activate

echo "Starting the bot..."
python3 main.py --setup 0

echo "Press any key to continue..."
read -n 1 -s
