#!/usr/bin/python3

import sys
import numpy as np
import re
import os.path
import subprocess
import argparse

def usage():
    print('\nsupernova.py by J. Scott (2018)')
    print('\nUsage:')
    print('\npython supernova.py <fluxname> <channelname> <experimentname> <weighting> (0 = apply weighting factor)')
    print('\ne.g. python supernova.py livermore argon ar17kt 0 \n')

parser = argparse.ArgumentParser(description = 'SNOwGLoBES: public software for computing interaction rates and distributions of observed quantities for supernova burst neutrinos in common detector materials.')
parser.add_argument('fluxname', type=str, help='Name of flux. \n (eg. livermore)')
parser.add_argument('channelname', type=str, help='Name of channel. \n (eg. argon)')
parser.add_argument('experimentname', type=str, help='Name of experiment. \n (eg. ar17kt)')
parser.add_argument('--weight',action='store_true', help='Apply weighting factor. \n (eg. 0 = Applied, 1 = Not Applied')
args = parser.parse_args()

fluxname = args.fluxname
channame = args.channelname
expt_config = args.experimentname
noweight = args.weight

exename = "bin/supernova"

chanfilename = "channels/channels_" +channame+ ".dat"

#Create the GLOBES file
globesfilename = "supernova.glb"

GLOBESFILE = open(globesfilename, 'w')

#Open the preamble, read contents and print to GLOBES file
with open("glb/preamble.glb") as PREAMBLE:
    preamble_contents = PREAMBLE.read()
    print(preamble_contents, file = GLOBESFILE)


#Create the corresponding flux file name
fluxfilename = "fluxes/" +fluxname+ ".dat"
if not os.path.exists(fluxfilename):
    print("Flux file name " + fluxfilename + " not found")

#add the error message for if the user inputs an invalid Flux fluxfilename

#Open the flux globes file, read contents and replace supernova_flux.dat with the fluxfilename
with open("glb/flux.glb") as FLUX:
    flux_contents = FLUX.read()
    flux_contents1 = re.sub('supernova_flux.dat', fluxfilename, flux_contents)
    print(flux_contents1, end = '', file = GLOBESFILE)

if not os.path.exists(chanfilename):
    print("Flux file name " + chanfilename + " not found")

#Channel data
#start with smearing
#Open the channel file and grab the channel name.
with open(chanfilename) as CHANFILE:
    stuff = [i.split() for i in CHANFILE]
    chan_names = [item[0] for item in stuff]
#Print the smearing data file name for each channel in the channel file to the GLOBES file
    for chan_name in chan_names:
        output_line = "include \"smear/smear_" + chan_name + "_" +expt_config+ ".dat\""
        print(output_line, file = GLOBESFILE)


#Define the detector configurations file name
detfilename = "detector_configurations.dat"

#include error essage if wrong input
if not os.path.exists(detfilename):
    print("Detector file name " + detfilename + " not found")

#Open the detector configurations file
with open(detfilename) as DETFILENAME:
    for line in DETFILENAME:
        #skip any leading comments
        if line.startswith('#'):
            pass
        p = re.compile("\s+")
        formatted_line=p.sub(" ", line)
        #Grab the detector names, masses, and normalization factors
        stuff = [i.split() for i in DETFILENAME]
        detname = [item[0] for item in stuff]
        masses =  [item[1] for item in stuff]
        normfactor = [item[2] for item in stuff]
        index = detname.index(expt_config)
        #Convert the lists into arrays, in order to do math
        masses_array = np.array(masses, dtype = float)
        normfactor_array = np.array(normfactor, dtype = float)

        #Skip any blank lines
        if ((detname == "") or (masses == "") or (normfactor == "")):
            pass

#Calculate the target mass in ktons of free particles
target_mass_raw = masses_array[index]*normfactor_array[index]
#Format the target mass for output. (13 total spaces, with 6 trailing decimals?)
target_mass = '{:13.6f}'.format(target_mass_raw)

#Print the experiment configuration and corresponding mass to the terminal
print("Experiment config: " + expt_config + " Mass: " +masses[index]+ " kton ")

#ADD the background smearing here, for the given detector configuration
#There are not yet background channels for all detectors.

do_bg = 0
bg_chan_name = "bg_chan"

#Determine the background file name
bg_filename = "backgrounds/" + bg_chan_name + "_" + expt_config + ".dat"
#Check whether the file exists
if os.path.exists(bg_filename):
    do_bg = 1
    print("Using background file " + bg_filename)
else:
    print("No background file for this configuration")

#If the file exists, print the background smearing file for each channel to the GLOBES file
if do_bg == 1 :
    output_line = "include \"smear/smear_" + bg_chan_name + "_" + expt_config + ".dat\""
    print(output_line, file = GLOBESFILE)


with open("glb/detector.glb", 'w') as DETECTOR:
    #detector_contents =  DETECTOR.read()
    #detector_contents1 = re.sub('\d[.]\d\d\d\d\d\d', target_mass, detector_contents)
    #print(detector_contents1, file = GLOBESFILE)
#Print the detector settings to the GLOBES file, with the calculated target mass
    output_line = ("\n" + "/* ####### Detector settings ####### */" + "\n" + "\n" + "$target_mass= " +target_mass+ "\n")
    print(output_line, file = GLOBESFILE)


print("\n /******** Cross-sections ********/\n", file = GLOBESFILE)

#Open the channel file and grab the channel names
with open(chanfilename) as CHANFILE:
    stuff = [i.split() for i in CHANFILE]
    chan_names = [item[0] for item in stuff]
    #For each of the channels, print the cross-sections file name to GLOBES file
    for chan in chan_names:
        print("cross(#" +chan+ ")<", file = GLOBESFILE)
        print("      @cross_file= \"xscns/xs_" +chan+ ".dat\"", file = GLOBESFILE)
        print(">", file = GLOBESFILE)

#Add the fake bg channel cross section, if it exists for this configuration
if do_bg == 1 :
    print("cross(#" + bg_chan_name + ")<", file = GLOBESFILE)

    print("     @cross_file= \"xscns/xs_zero.dat\"", file = GLOBESFILE)

    print(">", file = GLOBESFILE)


print("\n /********* Channels ********/\n", file = GLOBESFILE)

#NOW the channel definitions...
#INCLUDE ERROR message
if not os.path.exists(chanfilename):
    print("Channel file name " + chanfilename + " not found")

#Open the channel file and grab the channel names, index, cpstate, and inflav
with open(chanfilename) as CHANFILE:
    stuff = [i.split() for i in CHANFILE]
    chan_name = [item[0] for item in stuff]
    index = [item[1] for item in stuff]
    index = np.array(index, dtype = int)
    cpstate =  [item[2] for item in stuff]
    inflav = [item[3] for item in stuff]

    #Iterating over each channel by using the index, we print the channel name, cpstate, and inflav to GLOBES file
    for i in index:

        print("channel(#" +chan_name[i]+"_signal)<", file = GLOBESFILE)

        print("      @channel= #supernova_flux:  "+cpstate[i]+ ":    "+inflav[i]+":     "+inflav[i]+ ":    #" +chan_name[i]+":    #" +chan_name[i]+ "_smear", file = GLOBESFILE)


        #Get the post-smearing efficiency file names for each channel
        eff_file = "effic/effic_" + chan_name[i] + "_"+ expt_config + ".dat"
        #Now open the efficiency files, read the contents, the print the efficiency matrices to the GLOBES file
        with open(eff_file) as EFF_FILE:
            eff_file_contents = EFF_FILE.read()
            print("       @post_smearing_efficiencies = " + eff_file_contents , file = GLOBESFILE)

        print(">\n", file = GLOBESFILE)

#NOW make a fake channel background... There is only one bgfile for now
if do_bg == 1:

    #this is dummy info... NOT SURE WHAT TO DO WITH THIS
    cpstate = "-"
    inflav = "e"
    output_line = "channel(#" +bg_chan_name+"_signal)<"
    print(output_line, file = GLOBESFILE)

    output_line = "      @channel= #supernova_flux:  "+cpstate+":    "+inflav+":     "+inflav+":    #" + bg_chan_name +":    #"+bg_chan_name+ "_smear"
    print(output_line, file = GLOBESFILE)

    #get the pre smearing backgrounds by channels
    bg_file = "backgrounds/" +bg_chan_name+ "_" +expt_config+ ".dat"
    print(bg_file, "\n")

    #Open the background file and output the file name to the GLOBES file
    with open(bg_file) as BG_FILE:
        bgfilecontents = BG_FILE.read()
        output_line = "       @pre_smearing_background = " + bgfilecontents
        print(output_line, file = GLOBESFILE)

    output_line = "\n>\n"
    print(output_line, file = GLOBESFILE)

#END-MATTER

#Open the postamble, read contents, and print them to the Globes file
with open("glb/postamble.glb") as POSTAMBLE:
    postamble_contents = POSTAMBLE.read()
    print(postamble_contents, end = '', file = GLOBESFILE)

#Close the Globes file
GLOBESFILE.close()

#Now we run the executable
subprocess.run([exename, fluxname, chanfilename, expt_config])

#Define the function that will apply the channel weighting factors
def apply_weights (filename):
    #Open the channel file and grab all the info
    with open(chanfilename) as CHANFILE:
        stuff = [i.split() for i in CHANFILE]
        chan_names = [item[0] for item in stuff]
        index = [item[1] for item in stuff]
        index = np.array(index, dtype = int)
        cpstate =  [item[2] for item in stuff]
        inflav = [item[3] for item in stuff]
        num_target_factor = [item[4] for item in stuff]
        num_target_factor_array = np.array(num_target_factor, dtype = float)


        #OPEN the unweighted output file as input and the weighted file as output
        #essentially we begin with the unweighted file that is made by globes then we weight it
        #and then we weight the smeared one resulting in a total of 3 files per config setup

        #Iterating over the channels by using the index, we create the unweighted and weighted file names for each channel
        for i in index:
            unweightedfilename = "out/" + fluxname + "_" + chan_names[i] + "_" + expt_config + "_events" + filename +"_unweighted.dat"

            weightedfilename = "out/" + fluxname + "_" + chan_names[i] + "_" + expt_config + "_events" + filename + ".dat"

            #Using the index, we select the num_target_factor for the corresponding channel
            num = num_target_factor_array[i]

            #Open both files
            with open(unweightedfilename, 'r') as UNWEIGHTED:
                with open(weightedfilename, 'w') as WEIGHTED:
                    for line in UNWEIGHTED:
                        
			#print(line)
			#Strip any leading whitespace... I THINK??
                        line = line.strip()
                        #Replace any contiguous whitespace with a single space
                        p = re.compile("\s+")
                        formatted_line=p.sub(" ", line)
                        #Skip any blank lines
			#print(formatted_line)
                        if not line:
                            continue
                        #Skip any lines that begin with comments
                        if line.startswith("#"):
                            continue

                        #Match the end of the data, and print the bar
                        if line == "----------------------":
                            print("----------------------", file = WEIGHTED)
                        else:
                            np.set_printoptions(precision=6)
                            #If we're not at the end of the file, save each line into stuff2
                            #Split stuff2 into enbin and evrate
                            stuff2 = formatted_line.split()
                            enbin = stuff2[0]
                            evrate = stuff2[1]
                            #If there is a value for enbin, then we print the weighted info into the weighted file
                            if enbin != "" :
                                #Convert the evrate into an array
                                evrate_array = np.array(evrate, dtype = float)
                                #Calculate the new evrate, by multiplying the evrate with the num_target_factor for the specific channel as given by num
                                new_evrate = np.dot(evrate_array, num)
                                

                                #Print the weighted data to the weighted file
                                output = "{0} {1}".format(enbin, new_evrate)
                                print(output, file = WEIGHTED)

#If the argument noweight is input as '0', then we apply weighting factors
if noweight:
    print("Applying channel weighting factors to output")
    #Call the apply_weights function for both unsmeared and smeared data
    apply_weights("")
    apply_weights("_smeared")
#If noweight is not 0, then we do not apply weighting factors
else:
    print("No weighting factors applied to output")
