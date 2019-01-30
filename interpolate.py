#!/bin/python3

import numpy as np
import pandas as pd
import linecache as lc
import os
from scipy import interpolate
import argparse


parser = argparse.ArgumentParser(description = 'Interpolates Chimera data and converts the Luminosity to Fluence')
parser.add_argument('fluxname', type=str, help='Name of flux. \n (eg. chimera)')
parser.add_argument('path', type=str, help='Directory containing the Luminosity files.\n (eg. /lustre/atlas1/stf006/proj-shared/bronson/2D_lumspec)')
parser.add_argument('path1', type=str, help='Directory to output the Fluence files to.\n (eg. /fluxes/td_fluxes/chimera)')

args = parser.parse_args()
fluxname = args.fluxname
path = args.path
path1 = args.path1


#path = '/ccs/home/justinscot/spectob1300'
#path = '/lustre/atlas1/stf006/proj-shared/bronson/2D_lumspec'
#path = '/lustre/atlas1/stf006/proj-shared/bronson/2D_lumspec/oscillated/inverted'

overall_time = []
pb_time = []

i = 0
#10 kpc in cm 
R = 3.086*10**22
#distance modulus
factor = 1/(4*np.pi*pow(R,2))

#Collect the times
fluxfiles = os.listdir(path)
fluxfiles.sort()
for flux in fluxfiles:
        if flux.endswith(".dat"):
                filename = path + '/' +flux
                time = lc.getline(filename, 9).rstrip('\n')
                split_time = time.split()
                overall_time.append(split_time[0])
                pb_time.append(split_time[1])

time_outputfile = "./fluxes/td_fluxes/timesteps/"+ fluxname + "_timesteps.dat"

d = {"Overall Time (s)": overall_time, "Post Bounce Time (s)": pb_time}	
df = pd.DataFrame(data=d, columns = ["Overall Time (s)", "Post Bounce Time (s)"])
txt = df.to_string(index=False)
with open(time_outputfile, 'w') as fo:
	print (txt, file=fo)

pb_time_array = np.array(pb_time, dtype=float)
#print(len(pb_time_array))


for flux in fluxfiles:
    nue_flux = []
    nuebar_flux = []
    nux_flux = []
    nuxbar_flux = []    
    if flux.endswith(".dat"):
	
		#Read in DATA
                filename = path + '/' +flux
                columns = ['Energy', 'Nue.Num.Flux', 'Nuebar.Num.Flux', 'Nux.Num.Flux', 'Nuxbar.Num.Flux']
                df = pd.read_table(filename, sep="\s+", skiprows = 12, nrows = 20, header = None, names = columns)
 #               print(filename)
  #              print(df)
                energy = df['Energy'].values
                nue_numflux = np.abs( df['Nue.Num.Flux'].values)
                nuebar_numflux = np.abs(df['Nuebar.Num.Flux'].values)
                nux_numflux = np.abs(df['Nux.Num.Flux'].values)
                nuxbar_numflux = np.abs(df['Nuxbar.Num.Flux'].values)
		
		#Convert energy to GeV               
                energygev = energy * 0.001
                bins = np.arange(0,.1002,0.0002)
                np.set_printoptions(precision=6)

		#Extrapolate the fluxes for below the first energy
                f=0
                while bins[f] <= energygev[0]:
                    alpha = np.abs(1/(1+(energygev[0]-bins[f])/(bins[f]-0.0001)))
                    nue_flux.append(np.exp(alpha * np.log(nue_numflux[0])))
                    nuebar_flux.append(np.exp(alpha * np.log(nuebar_numflux[0])))
                    nux_flux.append(np.exp(alpha * np.log(nux_numflux[0])))
                    nuxbar_flux.append(np.exp(alpha * np.log(nuxbar_numflux[0])))
                    f=f+1
                    
		#Populate the rest of the fluxes
                for p in range(0,19):
                    while f<501:
                            if bins[f] <= energygev[p+1]:
                                alpha = np.abs(1/(1+(energygev[p+1]-bins[f])/(bins[f]-energygev[p])))
                                nue_flux.append(np.exp(alpha * np.log(nue_numflux[p+1])+(1-alpha) * np.log(nue_numflux[p])))
                                nuebar_flux.append(np.exp(alpha * np.log(nuebar_numflux[p+1])+(1-alpha) * np.log(nuebar_numflux[p])))
                                nux_flux.append(np.exp(alpha * np.log(nux_numflux[p+1])+(1-alpha)*np.log(nux_numflux[p])))
                                nuxbar_flux.append(np.exp(alpha * np.log(nuxbar_numflux[p+1])+(1-alpha)*np.log(nuxbar_numflux[p])))
                                f=f+1
                                
                            elif bins[f] > energygev[p+1]:
                                p=p+1
    
                nue_flux_array = np.array(nue_flux, dtype=float)
                nuebar_flux_array = np.array(nuebar_flux, dtype=float)
                nux_flux_array = np.array(nux_flux, dtype=float)
                nuxbar_flux_array = np.array(nuxbar_flux, dtype=float)                
		
		#Convert the fluxes into fluences by multiplying by dt
                if i==0 or i==1:
                    nue_num_fluence = nue_flux_array * factor * (pb_time_array[1] - pb_time_array[0])
                    nuebar_num_fluence = nuebar_flux_array * factor * (pb_time_array[1] - pb_time_array[0])
                    nux_num_fluence = nux_flux_array * factor * (pb_time_array[1] - pb_time_array[0])
                    nuxbar_num_fluence = nuxbar_flux_array * factor * (pb_time_array[1] - pb_time_array[0])
                else: 
                    nue_num_fluence = nue_flux_array * factor * (pb_time_array[i] - pb_time_array[i-1])
                    nuebar_num_fluence = nuebar_flux_array * factor * (pb_time_array[i] - pb_time_array[i-1])
                    nux_num_fluence = nux_flux_array * factor * (pb_time_array[i] - pb_time_array[i-1])
                    nuxbar_num_fluence = nuxbar_flux_array * factor * (pb_time_array[i] - pb_time_array[i-1])
                        
		#Prepare data for output
                d_out = {'"Energy (GeV)"':bins, '"Nue Fluence"':nue_num_fluence, '"Numu Fluence"':nux_num_fluence, '"Nutau Fluence"':nux_num_fluence, '"Nuebar Fluence"':nuebar_num_fluence, '"Numubar Fluence"':nuxbar_num_fluence, '"Nutaubar Fluence"':nuxbar_num_fluence}
                df_out = pd.DataFrame(data=d_out, columns = ['"Energy (GeV)"', '"Nue Fluence"', '"Numu Fluence"', '"Nutau Fluence"', '"Nuebar Fluence"', '"Numubar Fluence"', '"Nutaubar Fluence"'])
                outputfile = "." + path1 + "/"  + flux
                #os.makedirs(os.path.dirname(outputfile), exist_ok=True)
                pd.set_option('precision',6)
               #txt = df_out.to_string(index = False, header=False)
                
		#Print to output files
                with open(outputfile, 'w+') as fo:
                    df_out.to_string(fo, index=False, header=False)
                    #print(txt, file=fo)
                i = i + 1
                
