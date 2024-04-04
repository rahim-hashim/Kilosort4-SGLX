@echo off
@title Kilsort 4 - Run Kilo4 Python Script
:: Run kilosort 4
::
:: Author: Rahim Hashim
:: Date: March 2024
::
:: This script runs kilosort4 on a specified path
:: which is passed as an argument to the script.

echo "Activating kilosort environment"
call conda activate kilosort
:: Assign the first argument to the variable %1
:: Assign the second argument to the variable %2
:: Assign the third argument to the variable %3

echo "Running python kilosort4 script"
python kilosort4.py --bin_file=%1 --map_file=%3

call conda deactivate