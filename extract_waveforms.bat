@echo off
@title Kilsort 3 - Waveform Extraction
:: Run phy waveform extraction
::
:: Author: Rahim Hashim
:: Date: January 2024
::
:: This script runs phy waveform extraction on a specified path
:: which is passed as an argument to the script. The script is required
:: because Kilosort3 does not run it by default, and when performing 
:: manual curation, it is helpful to have the waveforms for each cluster

call activate phy2
phy extract-waveforms %1
echo "Waveform extraction complete"
call deactivate