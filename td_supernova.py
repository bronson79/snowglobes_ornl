#/usr/bin/python3

import subprocess
import sys
import os
import linecache as lc
import pandas as pd
import argparse
import numpy as np


parser = argparse.ArgumentParser(description = 'Loops time-dependent fluence files through SNOwGLoBES')
parser.add_argument('channelname', type=str, help='Name of channel. \n (eg. argon)')
parser.add_argument('experimentname', type=str, help='Name of experiment. \n (eg. ar17kt)')
parser.add_argument('fluxname', type=str, help='Name of flux. \n (eg. chimera)')
parser.add_argument('fluxpath', type=str, help='Directory containing flux files. \n (eg. /lustre/atlas1/stf006/proj-shared/bronson/2D_lumspec/)')
parser.add_argument('--interpolate', action='store_true', help='option to interpolate raw data')

args = parser.parse_args()

	
channame = args.channelname
expt_config = args.experimentname
fluxname = args.fluxname
fluxpath = args.fluxpath
interpolate = args.interpolate


if interpolate:
    interpcmd = "python interpolate.py " + fluxname + " " + fluxpath + " /fluxes/td_fluxes/" + fluxname 
    subprocess.run(interpcmd, shell=True)

path1 = "./fluxes/td_fluxes/" + fluxname
path2 = sys.argv[4]

files = [os.path.splitext(filename)[0] for filename in os.listdir(path1)]
files.sort()


overall_time = []
pb_time = []

for fluxes in files:
	if "00" in fluxes:
		fluxfile = "td_fluxes/" + fluxname + "/"+ fluxes
		cmd = "python supernova.py " + fluxfile + " " + channame + " " + expt_config + " " + "--weight"
		subprocess.run(cmd, shell=True)

	"""	fluxfilename = fluxpath + fluxes + ".dat"
		times = lc.getline(fluxfilename, 9)
		split_times = times.split()
		overall_time.append(split_times[0])
		pb_time.append(split_times[1])

time_outputfile = "./fluxes/td_fluxes/timesteps/"+ fluxname + "_timesteps.dat"

d = {"Overall Time (s)": overall_time, "Post Bounce Time (s)": pb_time}	
df = pd.DataFrame(data=d, columns = ["Overall Time (s)", "Post Bounce Time (s)"])
txt = df.to_string(index=False)
with open(time_outputfile, 'w') as fo:
	print (txt, file=fo)



def usage():
	print('\ntd_supernova.py by J. Scott (2018)')
	print('\nUsage:')
	print('\npython td_supernova.py <channelname> <experimentname> <fluxname> <path/to/raw/fluxfiles>' )
	print('\ne.g. python td_supernova.py argon ar17kt chimera  /lustre/atlas1/stf006/proj-shared/bronson/2D_lumspec/ \n')
"""
