# default imports
import os
import re
import sys
import time
import argparse
import numpy as np
from pathlib import Path
from pprint import pprint
import datetime as datetime
import matplotlib.pyplot as plt
from collections import defaultdict
import warnings
warnings.simplefilter("ignore")
# spikeinterface imports
import spikeinterface.full as si
print(f"SpikeInterface version: {si.__version__}")
# probeinterface imports
import probeinterface as pi
from probeinterface.plotting import plot_probe

def read_recording_folder(root, monkey, date, session_num=0):
	sglx_folder = os.path.join(root, f'{monkey}_{date}_g{session_num}')
	imec_folder_dict = defaultdict(str)
	print(f'SpikeGLX folder: {sglx_folder}')
	# check if it exists
	if not os.path.exists(sglx_folder):
		sys.exit(f'{sglx_folder} does not exist')
	# print all folders that have imec<int> in them
	for root, dirs, files in os.walk(sglx_folder):
		for dir in dirs:
			if re.search('imec\d', dir):
				imec_num = re.search('imec\d', dir).group()
				imec_folder_dict[imec_num] = os.path.join(root, dir)
	if not imec_folder_dict:
		sys.exit(f'No imec folders found in {sglx_folder}')
	return sglx_folder, imec_folder_dict

def extract_recordings(sglx_folder, imec_folder_dict):
	recording_dict = defaultdict(str)
	for imec_id in imec_folder_dict.keys():
		print(f'Probe: {imec_id}')
		recording = si.read_spikeglx(
			sglx_folder, 
			stream_id=f'{imec_id}.ap',
			load_sync_channel=False
		)
		recording_dict[imec_id] = recording
		print(recording)
	return recording_dict

def check_sorters():
	print("Available sorters", si.available_sorters())
	print("Installed sorters", si.installed_sorters())

	if 'kilosort4' not in si.installed_sorters():
		import subprocess
		print("Installing kilosort4")
		subprocess.run(['pip install kilosort==4.0'], shell=True)
		print("Installed sorters", si.installed_sorters())
	else:
		print("Kilosort4 already installed")

	sorter_name = 'kilosort4'
	print(f"Default Paramteres for {sorter_name}")
	pprint(si.get_default_sorter_params(sorter_name), indent=2)
	return sorter_name

def show_probes(recording_dict):
	# get first value from recording_dict
	fig, ax = plt.subplots(1, len(recording_dict.keys()), figsize=(14, 20))
	for idx, imec in enumerate(recording_dict.keys()):
		recording = recording_dict[imec]
		probe = recording.get_probe()
		print(f'{imec}:  {probe}')
		_ = plot_probe(probe, ax=ax[idx])
		ax[idx].set_xlim(-100, 200)
		ax[idx].set_ylim(-350, 4000)
	fig.tight_layout()
	plt.show(block=False)

def preprocess_recordings(
		recording_dict,
		highpass_filter=False, 
		common_reference_avg=False, 
		phase_shift=False, 
		find_bad_channels=False, 
		highpass_spatial_filter=False,
		save_preprocessed=False
	):
	'''
	Preprocesses recordings in a dictionary of recordings.

	Parameters:
	-----------
	recording_dict: dict
		Dictionary of extracted recordings.
	highpass_filter: bool
		Whether to apply a highpass filter to the recordings.
	common_reference_avg: bool
		Whether to apply a common reference averaging to the recordings.
	phase_shift: bool

	'''

	recording_preprocessed_dict = defaultdict(str)
	# find the time it takes to preprocess the recordings
	start_time = time.time()
	for idx, imec in enumerate(recording_dict.keys()): 
		print(f'Probe: {imec}')
		recording = recording_dict[imec]
		if highpass_filter:
			print(f'  Highpass filter n_channel_pad: 60')
			recording = highpass_filter(recording=recording, n_channel_pad=60)
		else:
			print(f'  Skipping highpass filter')
		if common_reference_avg:
			print(f'  Common reference averaging: global median')
			recording = si.common_reference(recording, reference="global", operator="median")
		else:
			print(f'  Skipping common reference')
		if phase_shift:
			print(f'  Computing phase shift')
			recording = si.phase_shift(recording)
		else:
			print(f'  Skipping phase shift')
		if find_bad_channels:
			print(f'  Detecting bad channels') 
			bad_channel_ids, channel_labels = si.detect_bad_channels(recording=recording)
			print(f'    Bad channels: {bad_channel_ids}')
			recording = si.interpolate_bad_channels(recording=recording, bad_channel_ids=bad_channel_ids)
		else:
			print(f'  Skipping bad channel detection')
		# this computes and saves the recording after applying the preprocessing chain
		if save_preprocessed:
			print(f'  Saving preprocessed recording')
			recording_preprocessed = recording.save(folder='clean_trace', format="binary")
			recording = recording_preprocessed
		recording_dict[imec] = recording
	print(f'  Preprocessing done')
	# calculate elapsed time in minutes
	total_time = round((time.time() - start_time) / 60, 2)
	print(f'Total time elapsed: {total_time}')
	return recording_dict

def sort_recordings(imec_folder_dict, 
										recording_dict, 
										sorter_name='kilosort4',
										save_sorted=True):
	sorted_dict = defaultdict(str)
	start_time = time.time()
	for idx, imec in enumerate(recording_dict.keys()):
		probe_start_time = time.time()
		print(f'Probe: {imec}')
		recording = recording_dict[imec]
		print(f'  Running {sorter_name}')

		sorted_folder = os.path.join(imec_folder_dict[imec], f'{imec}_ks_output')
		sorted_recording = si.run_sorter(
			sorter_name=sorter_name, 
			recording=recording,
			output_folder=sorted_folder,
			verbose=True)
		print(f'  {sorted_recording}')
		print(f'  Number of clusters: {len(sorted_recording.get_unit_ids())} units')
		sorted_dict[imec] = sorted_recording
		w_rs = si.plot_rasters(sorted_recording)
		plt.show()
		probe_end_time = round((time.time() - start_time) / 60, 2)
		print(f'  Time elapsed: {probe_start_time} min')
		# save the sorted recording
		if save_sorted:
			print(f'  Saving sorted recording to {sorted_output_folder}')
			sorted_recording.save(folder=sorted_folder)

	total_time = round((time.time() - start_time) / 60, 2)
	print(f'Total time elapsed: {total_time} min')

	return sorted_dict

def extract_waveforms(imec_folder_dict, recording_dict, sorted_recording_dict):
	waveform_dict = defaultdict(str)
	for idx, imec in enumerate(recording_dict.keys()):
		print(f'Probe: {imec}')
		recording = recording_dict[imec]
		sorted_recording = sorted_recording_dict[imec]
		print(f'  Extracting waveforms')
		sorted_folder = os.path.join(imec_folder_dict[imec], f'{imec}_ks_output')
		waveform_folder = os.path.join(sorted_folder, 'waveforms')
		we = si.extract_waveforms(
			recording, 
			sorted_recording, 
			folder=waveform_folder, 
			sparse=False, 
			overwrite=True
			)
		waveforms0 = we.get_waveforms(unit_id=0)
		print(f"Waveforms shape: {waveforms0.shape}")
		template0 = we.get_template(unit_id=0)
		print(f"Template shape: {template0.shape}")
		all_templates = we.get_all_templates()
		print(f"All templates shape: {all_templates.shape}")
		print(we)
		waveform_dict[imec] = we
		si.plot_unit_template(we)
	return waveform_dict

def run_spikeinterface():

	root = 'D:/'
	monkey = 'gandalf'
	date = '20240109'

	# find the sglx folder and the imec folders
	sglx_folder, imec_folder_dict = read_recording_folder(root, monkey, date, session_num=0)

	# make sure kilosort4 is installed
	sorter_name = check_sorters()

	# extract the recordings from the folders and convert to Recording objects
	recording_dict = extract_recordings(sglx_folder, imec_folder_dict)

	# display the number of probes and the layout
	show_probes(recording_dict)

	# preprocess the recordings
	recording_preprocessed_dict = preprocess_recordings(
		recording_dict, 
		highpass_filter=False, 
		common_reference_avg=False, 
		phase_shift=True, 
		find_bad_channels=True, 
		save_preprocessed=False
	)

	# run kilsort!
	sorted_recording_dict = sort_recordings(
		imec_folder_dict,
		recording_preprocessed_dict, 
		sorter_name='kilosort4',
		save_sorted=True
	)
	
	# extract waveforms
	waveform_dict = extract_waveforms(
		imec_folder_dict,
		recording_dict, 
		sorted_recording_dict
	)

if __name__ == "__main__":
	run_spikeinterface()