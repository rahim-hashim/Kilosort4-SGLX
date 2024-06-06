import os
import re
import sys
import time
import warnings
import argparse
import subprocess
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from collections import defaultdict
from matplotlib import gridspec, rcParams
warnings.simplefilter("ignore")

def read_recording_folder(root, monkey, date, session_num=0, probe_specified=[]):
	sglx_folder = os.path.join(root, f'{monkey}_{date}_g{session_num}')
	imec_folder_dict = defaultdict(str)
	print(f'SpikeGLX folder: {sglx_folder}')
	# check if it exists
	if not os.path.exists(sglx_folder):
		sys.exit(f'{sglx_folder} does not exist')
	# print all folders that have imec<int> in them
	for root, dirs, files in os.walk(sglx_folder):
		for folder in dirs:
			# only if the directory ends with imec<int>
			if re.search('imec\d$', folder):
				imec_num = re.search('imec\d$', folder).group()
				imec_folder_dict[imec_num] = os.path.join(root, folder)
	if not imec_folder_dict:
		try:
			print(os.listdir(root))
		except:
			print(f'{root} missing')
		sys.exit(f'No imec folders found in {sglx_folder}')
	# order the dictionary
	imec_folder_dict = dict(sorted(imec_folder_dict.items(), key=lambda item: item[1]))
	# specify the probes to run
	if probe_specified:
		print(f'Probes specified: {probe_specified}')
		imec_folder_dict = {k: v for k, v in imec_folder_dict.items() if k in probe_specified}
	return sglx_folder, imec_folder_dict