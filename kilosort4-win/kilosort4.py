import os
import sys
import shutil
import subprocess
import numpy as np
import argparse
from pathlib import Path
sys.path.append('C:/Users/Milner/OneDrive/Desktop/Spatial_Abstraction/code/')
sys.path.append('C:/Users/Penfield/Documents/GitHub/Spatial_Abstraction/code')
# from Spatial_Abstraction
from spike_glx.read_SGLX import read_SGLX
# from kilsort 4
from kilosort_pipeline import run_kilo_pipeline

# Set paths
kilosort_folder = 'C:/Users/Milner/OneDrive/Desktop/Kilosort-3'
config_file_path = os.path.join(kilosort_folder, 'configFiles')
chan_map_file = os.path.join(config_file_path, 'neuropixels_NHP_channel_map_linear_v1.mat')

# Set session identifiers
root = 'D:'
date = '20240115'
monkey = 'gandalf'

# Set Kilosort parameters
probes = []
session_num = [0]

run_kilosort = 1
run_catgt = 0
cat_prb_fld = '0:3'
include_catgt = 0
extract_waveforms = 1
delete_catbin = 0
run_tprime = 1

# Set paths
kwargs = {
	'kilosort_folder': kilosort_folder,
	'config_file_path': config_file_path,
	'chan_map_file': chan_map_file,
	'root': root,
	'date': date,
	'monkey': monkey,
	'probes': probes,
	'session_num': session_num,
	'kilosort_bool': run_kilosort,
	'run_catgt': run_catgt,
	'cat_prb_fld': cat_prb_fld,
	'include_catgt': include_catgt,
	'extract_waveforms': extract_waveforms,
	'delete_catbin': delete_catbin,
	'run_tprime': run_tprime
}

# kwargs
run_kilo_pipeline(**kwargs)

# def create_parser():
# 	parser = argparse.ArgumentParser(description='Run Kilosort 4 on a session')
# 	parser.add_argument('root', type=str, help='Root directory of the data')
# 	parser.add_argument('date', type=str, help='Date of the session')
# 	parser.add_argument('monkey', type=str, help='Monkey name')
# 	parser.add_argument('probes', type=str, help='Probes to run Kilosort on', default=[])
# 	parser.add_argument('session_num', type=str, help='Session number', default=[0])
# 	parser.add_argument('run_kilosort', type=int, help='Run Kilosort', default=1)
# 	parser.add_argument('run_catgt', type=int, help='Run catGT', default=0)
# 	parser.add_argument('cat_prb_fld', type=str, help='catGT probe folder', default='0:3')
# 	parser.add_argument('include_catgt', type=int, help='Include catGT', default=0)
# 	parser.add_argument('extract_waveforms', type=int, help='Extract waveforms', default=1)
# 	parser.add_argument('delete_catbin', type=int, help='Delete catGT binary files', default=0)
# 	parser.add_argument('run_tprime', type=int, help='Run tPrime', default=0)

# def main():
# 	parser = create_parser()
# 	args = parser.parse_args()
# 	kwargs = vars(args)
# 	print(kwargs)
# 	# run_kilo4(**kwargs)

