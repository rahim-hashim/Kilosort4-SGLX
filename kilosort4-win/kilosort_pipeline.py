import os
import sys
import time
import shutil
import argparse
import subprocess
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import gridspec, rcParams
# from Spatial_Abstraction
sys.path.append('C:/Users/Milner/OneDrive/Desktop/Spatial_Abstraction/code/')
from spike_glx.read_SGLX import read_SGLX
# from kilosort
from kilosort import run_kilosort
# download channel maps for probes
from kilosort.utils import download_probes

def plot_results(settings):

	# outputs saved to results_dir
	results_dir = Path(settings['results_dir'])
	ops = np.load(results_dir / 'ops.npy', allow_pickle=True).item()
	camps = pd.read_csv(results_dir / 'cluster_Amplitude.tsv', sep='\t')['Amplitude'].values
	contam_pct = pd.read_csv(results_dir / 'cluster_ContamPct.tsv', sep='\t')['ContamPct'].values
	chan_map =  np.load(results_dir / 'channel_map.npy')
	templates =  np.load(results_dir / 'templates.npy')
	chan_best = (templates**2).sum(axis=1).argmax(axis=-1)
	chan_best = chan_map[chan_best]
	amplitudes = np.load(results_dir / 'amplitudes.npy')
	st = np.load(results_dir / 'spike_times.npy')
	clu = np.load(results_dir / 'spike_clusters.npy')
	firing_rates = np.unique(clu, return_counts=True)[1] * 30000 / st.max()
	dshift = ops['dshift']

	rcParams['axes.spines.top'] = False
	rcParams['axes.spines.right'] = False
	gray = .5 * np.ones(3)

	fig = plt.figure(figsize=(10,10), dpi=100)
	grid = gridspec.GridSpec(3, 3, figure=fig, hspace=0.5, wspace=0.5)

	ax = fig.add_subplot(grid[0,0])
	ax.plot(np.arange(0, ops['Nbatches'])*2, dshift)
	ax.set_xlabel('time (sec.)')
	ax.set_ylabel('drift (um)')

	ax = fig.add_subplot(grid[0,1:])
	t0 = 0 
	t1 = np.nonzero(st > ops['fs']*5)[0][0]
	ax.scatter(st[t0:t1]/30000., chan_best[clu[t0:t1]], s=0.5, color='k', alpha=0.25)
	ax.set_xlim([0, 5])
	ax.set_ylim([chan_map.max(), 0])
	ax.set_xlabel('time (sec.)')
	ax.set_ylabel('channel')
	ax.set_title('spikes from units')

	ax = fig.add_subplot(grid[1,0])
	nb=ax.hist(firing_rates, 20, color=gray)
	ax.set_xlabel('firing rate (Hz)')
	ax.set_ylabel('# of units')

	ax = fig.add_subplot(grid[1,1])
	nb=ax.hist(camps, 20, color=gray)
	ax.set_xlabel('amplitude')
	ax.set_ylabel('# of units')

	ax = fig.add_subplot(grid[1,2])
	nb=ax.hist(np.minimum(100, contam_pct), np.arange(0,105,5), color=gray)
	ax.plot([10, 10], [0, nb[0].max()], 'k--')
	ax.set_xlabel('% contamination')
	ax.set_ylabel('# of units')
	ax.set_title('< 10% = good units')

	for k in range(2):
			ax = fig.add_subplot(grid[2,k])
			is_ref = contam_pct<10.
			ax.scatter(firing_rates[~is_ref], camps[~is_ref], s=3, color='r', label='mua', alpha=0.25)
			ax.scatter(firing_rates[is_ref], camps[is_ref], s=3, color='b', label='good', alpha=0.25)
			ax.set_ylabel('amplitude (a.u.)')
			ax.set_xlabel('firing rate (Hz)')
			ax.legend()
			if k==1:
					ax.set_xscale('log')
					ax.set_yscale('log')
					ax.set_title('loglog')

	# 
	probe = ops['probe']
	# x and y position of probe sites
	xc, yc = probe['xc'], probe['yc']
	nc = 16 # number of channels to show
	good_units = np.nonzero(contam_pct <= 0.1)[0]
	mua_units = np.nonzero(contam_pct > 0.1)[0]

	gstr = ['good', 'mua']
	for j in range(2):
			print(f'~~~~~~~~~~~~~~ {gstr[j]} units ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
			print('title = number of spikes from each unit')
			units = good_units if j==0 else mua_units 
			fig = plt.figure(figsize=(12,3), dpi=150)
			grid = gridspec.GridSpec(2,20, figure=fig, hspace=0.25, wspace=0.5)

			for k in range(40):
					wi = units[np.random.randint(len(units))]
					wv = templates[wi].copy()  
					cb = chan_best[wi]
					nsp = (clu==wi).sum()
					
					ax = fig.add_subplot(grid[k//20, k%20])
					n_chan = wv.shape[-1]
					ic0 = max(0, cb-nc//2)
					ic1 = min(n_chan, cb+nc//2)
					wv = wv[:, ic0:ic1]
					x0, y0 = xc[ic0:ic1], yc[ic0:ic1]

					amp = 4
					for ii, (xi,yi) in enumerate(zip(x0,y0)):
							t = np.arange(-wv.shape[0]//2,wv.shape[0]//2,1,'float32')
							t /= wv.shape[0] / 20
							ax.plot(xi + t, yi + wv[:,ii]*amp, lw=0.5, color='k')

					ax.set_title(f'{nsp}', fontsize='small')
					ax.axis('off')
			plt.show()

def run_kilosort4(bin_file=None, 
									results_dir=None,
									n_channels=385,
									probe_path='neuropixels_NHP_channel_map_linear_v1.mat'):
	data_dir = os.path.dirname(bin_file)
	settings = {'filename': bin_file, 
							'data_dir': data_dir, 
							'results_dir': results_dir, 
							'n_chan_bin': n_channels, 
							'probe_path': probe_path}

	ops, st, clu, tF, Wall, similar_templates, is_ref, est_contam_rate = \
			run_kilosort(settings=settings)
	print('Plotting ks4 results...') 
	plot_results(settings)
	print('  Done!')


def run_kilo_pipeline(kilosort_folder, 
							config_file_path,
							chan_map_file,
							root,
							date,
							monkey,
							probes,
							session_num,
							kilosort_bool,
							run_catgt,
							cat_prb_fld,
							include_catgt,
							extract_waveforms,
							delete_catbin,
							run_tprime):
	'''
	Run Kilsort preprocessing steps and Kilosort4 on a dataset
	
	Args
	----
	kilosort_folder : str
		Path to the Kilosort folder
	config_file_path : str
		Path to the config files
	chan_map_file : str
		Path to the channel map file
	root : str
		Path to the root directory
	date : str
		Date of the session
	monkey : str
		Name of the monkey
	probes : list
		List of probes to process
	session_num : list
		List of session numbers to process
	kilosort_bool : bool
		Run Kilosort
	run_catgt : bool
		Run CatGT
	cat_prb_fld : str
		CatGT probe field
	include_catgt : int
		Include CatGT output
	extract_waveforms : bool
		Extract waveforms
	delete_catbin : bool
		Delete CatGT binary file
	run_tprime : bool
		Run TPrime
		
	Returns
	-------
	None
	'''
	# Find session directory
	root_files = os.listdir(root)
	session_folders = []
	for folder_name in root_files:
			if os.path.isdir(os.path.join(root, folder_name)) and folder_name.startswith(f"{monkey}_{date}_g"):
					session_folders.append(folder_name)

	if not session_folders:
			print(f"No SpikeGLX session folder found for {monkey}_{date}")
			exit()

	# Run CatGT / KS
	for session_folder in session_folders:
		g_num = session_folder.split('_')[-1]

		if session_num and g_num != f"g{session_num[0]}":
			print(f"Session not specified in sessionNum field: {session_folder}")
			continue

		session_path = os.path.join(root, session_folder)
		imec_dirs = [d for d in os.listdir(session_path) if os.path.isdir(os.path.join(session_path, d)) and 'imec' in d]
		print(f'  imec directories: {imec_dirs}')
		# Run CatGT
		if run_catgt:
			print(f"Running CatGT on {session_folder}")
			# time how long it takes
			start_time = time.time()
			catgt_command = f"runit.bat -dir={root} -run={monkey}_{date} -prb_fld -g={g_num[1:]} -t=0 -ni -prb={cat_prb_fld} -ap -gblcar"
			print(f"  Bash command: {catgt_command}")
			subprocess.run(catgt_command, cwd=os.path.join(kilosort_folder, "CatGT-win/"), shell=True)
			print(f"  CatGT complete. Time elapsed: {time.time() - start_time:.2f} seconds")

		# Loop through all subdirectories and run Kilosort
		for imec_folder_name in imec_dirs:
			print(f"Processing {imec_folder_name}...")
			imec_num = imec_folder_name[4:]
			if probes and imec_num not in [str(p) for p in probes]:
				print(f"Skipping Probe not specified in probe field: {imec_folder_name}")
				continue

			root_z = os.path.join(session_path, imec_folder_name)
			root_h = root_z
			dest_folder_path = os.path.join(root_h, f"{imec_folder_name}_ks4_cat")
			os.makedirs(dest_folder_path, exist_ok=True)

			fig_path = os.path.join(root_h, 'KS4_figures')
			os.makedirs(fig_path, exist_ok=True)

			binary_files = [f for f in os.listdir(root_z) if f.endswith('.bin') and '.ap' in f]
			meta_files = [f for f in os.listdir(root_z) if f.endswith('.meta')]

			if not binary_files:
				print(f"  No binary files found in {root_z}")
				continue
			if include_catgt == 0:
				binary_file = [f for f in binary_files if 'tcat' not in f]
				meta_files = [f for f in meta_files if 'tcat' not in f]
			elif include_catgt == 2:
				print("  Including only CatGT .bin files...")
				binary_files = [f for f in binary_files if 'tcat' in f]
				meta_files = [f for f in meta_files if 'tcat' in f]

			for b_index, binary_file in enumerate(binary_files):
				print(f"  Binary file: {binary_file}")
				meta_file = meta_files[b_index]
				print(f"    Meta file: {meta_file}")

				if kilosort_bool:
					print("    Running Kilosort4...")
					binary_file_path = os.path.join(root_z, binary_file)
					run_kilosort4(bin_file = binary_file_path,
									 			results_dir = dest_folder_path,
												n_channels=385,
												probe_path=chan_map_file)
					print(f"    Kilosort4 complete.")

				print(f"\tDestination Folder: {dest_folder_path}")

				if delete_catbin:
					catgt_output = f"{session_folder}_tcat.{imec_num}.ap.bin"
					catgt_path = os.path.join(root_z, catgt_output)
					if os.path.exists(catgt_path):
							os.remove(catgt_path)
							print("\tDeleting CatGT output...")

				if extract_waveforms:
					extract_command = f"extract_waveforms.bat {dest_folder_path}/params.py"
					print(f"\tExtracting waveforms...")
					subprocess.run(extract_command, cwd=kilosort_folder, shell=True)

				if run_tprime:
					print("\tConverting spike times to seconds...")
					sample_rate = float(meta_file['imSampRate'])
					print(f"\tSampling rate: {sample_rate:.2f}")
					spike_times = np.load(os.path.join(dest_folder_path, 'spike_times.npy'))
					# keep full precision
					spike_times_sec = spike_times / sample_rate
					spike_times_sec_file = os.path.join(dest_folder_path, "spike_times_sec.txt")
					with open(spike_times_sec_file, 'w') as f:
							for spike_time in spike_times_sec:
									f.write(f"{spike_time}\n")
					print(f"\t\tGenerating {spike_times_sec_file}")
					print("\t\tDone.")

			if run_tprime:
				print(f"Running TPrime on {session_folder}")
				# find file that 
				tprime_command = f"runit.bat -syncperiod=1.0 -tostream={os.path.join(session_path, 'tcat.nidq.xd.txt')}"
				for imec_dir in imec_dirs:
					imec_num = imec_dir[4:]
					spike_times_sec_file = os.path.join(session_path, imec_dir, f"{imec_dir}_ks_cat", "spike_times_sec.txt")
					spike_times_sec_adj_file = os.path.join(session_path, imec_dir, f"{imec_dir}_ks_cat", "spike_times_sec_adj.txt")
					tprime_command += f" -fromstream={imec_num},{os.path.join(root_z, f'tcat.{imec_num}.ap.xd.txt')}"
					tprime_command += f" -events={imec_num},{spike_times_sec_file},{spike_times_sec_adj_file}"

				print(f"  Bash command: {tprime_command}")
				subprocess.run(tprime_command, cwd=os.path.join(kilosort_folder, "TPrime-win/"), shell=True)

				for imec_dir in imec_dirs:
					imec_num = imec_dir[4:]
					spike_times_sec_adj_file = os.path.join(session_path, imec_dir, f"{imec_dir}_ks_cat", "spike_times_sec_adj.txt")
					npy_file = os.path.join(session_path, imec_dir, f"{imec_dir}_ks_cat", "spike_times_adj.npy")

					with open(spike_times_sec_adj_file, 'r') as f:
							spike_times_adj = [float(line.strip()) * sample_rate for line in f.readlines()]

					spike_times_adj = [int(spike_time) for spike_time in spike_times_adj]
					np.save(spike_times_adj, npy_file)
					print(f"  Generating adjusted spiketime files for: {spike_times_sec_adj_file}")