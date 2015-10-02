#!/usr/bin/python

'''
Parse multiple BGP dumps or updates and create pickles of prefix tree, path ASes and Origin ASes. 
Author Josef Gustafsson <gustafss@in.tum.de>

'''

import os
import sys
import threading
import argparse
import socket
import cPickle as pickle
import shutil
from multiprocessing import Process
from time import gmtime, strftime
from node import *
from parser import *
from merger import merge_dir

DEFAULT_NR_OF_THREADS =1
SAVE_INTERVAL = 10000     # Create backup of working data after reading SAVE_INTERVAL files

# Read a dump or update file and add data to provided data structures
def read_file(filename, tree, origin_as, path_as):

    update_file = MRTParser(filename)   # Works for dumps as well

    #Loop over the update file
    loop = True
    while loop:
        try:
            entry = update_file.next()
	except:
	    break

	time = entry[0]
	mask = entry[2]
	prefix = entry[1]

	# No AS path specified == withdrawal
	# Increade counters and update timestamps to latest
	if entry[3] is None:
	    tree.getNode(prefix,mask).withdraw(time)
	else:
	    tree.getNode(prefix,mask).announce(time)
	    path, origin = parsePath(entry[3])

	    # Update path_as data structure
	    for AS in path:
		if AS not in path_as:
		    path_as[AS] = [1, time]
		else:
		    path_as[AS][0] += 1
		    if path_as[AS][1] < time:
			path_as[AS][1] = time

            # Update origin_as data structure
	    for AS in origin:
		if AS not in origin_as:
		    origin_as[AS] = [1, time]
		else:
		    origin_as[AS][0] += 1
		    if origin_as[AS][1] < time:
			origin_as[AS][1] = time
    return tree											



# Parse an AS path string into two lists of INTs, one for transit ASes and one for origins.
def parsePath(p):
    path = []
    origin = []
    try:
        # Split path, if last char is } origin is a set
        if p[-1] == '}':
	    # Use entire set as origin
 	    aspath = p.split("{")
        else:
	    aspath = p.split(" ")
        origin = parseAS(aspath[-1]) #AS or AS-set

        # Don't include origin AS in path.
	for string in aspath[:-1]:
	    for AS in parseAS(string):
		if AS not in path:
		    path.append(AS)						
        return path, origin
    except:
	print "Unable to parse path!", p
	return [], []

# Due to inconsistent formatting in BGP messages, some paths need additional parsing
# Parse sets and other complicated notations to a list
def parseAS(string):
    try:
	parsed = [int(string)] #Origin is last AS, error if bad format or AS-set
    except:
	try:
	    tmpstr = string.replace('}', '')
	    tmpstr = tmpstr.replace('{', '')
	    tmpstr = tmpstr.replace(',', ' ') #sometimes separated by comma
	    tmpstr = tmpstr.split(' ') # set origin to a list of all ASes in set
	    parsed = []
	    for AS in tmpstr:
		if AS is not '':
		    parsed.append(int(AS)) #Convert to integers
	except:
	    print "AS-set parser failed to parse " + string + " Returning []"
	    return []
    return parsed



# Build prefix tree and AS dictionaries from a list of input files
# Save at defined intervals to aviod loosing data (precaution for long runs)

def make_tree(input_list, out_dir):
    save_dir = out_dir + "/"
    origin_as = {}
    path_as = {}
    tree = node()

    count = 0
    save_nr = 1
    i = 0

    for filename in input_list:
	print i + 1, filename
	i += 1
	read_file(filename, tree, origin_as, path_as)
	count += 1
	if count == SAVE_INTERVAL:
	    #### SAVING FILES ####
	    filename_tree = "pickled_prefix_" + str(save_nr)
	    filename_path = "pickled_path_" + str(save_nr)
	    filename_origin = "pickled_origin_" + str(save_nr)

            print "saving prefix tree as", save_dir + filename_tree
	    pickle.dump(tree, open(save_dir + filename_tree, "wb"))

	    print "saving AS origins as", save_dir + filename_origin
	    pickle.dump(origin_as, open(save_dir + filename_origin, "wb"))

	    print "saving AS paths as", save_ddir + filename_path
	    pickle.dump(path_as, open(save_dir + filename_path, "wb"))

            count = 0
	    save_nr += 1

    #### SAVING FILES ####
    filename_tree = "PrefixTree.pickle"
    filename_path = "ASpaths.pickle"
    filename_origin = "ASorigins.pickle"

    print "saving prefix tree as", save_dir + filename_tree
    pickle.dump(tree, open(save_dir + filename_tree, "wb"))

    print "saving AS origins as", save_dir + filename_origin
    pickle.dump(origin_as, open(save_dir + filename_origin, "wb"))

    print "saving AS paths as", save_dir + filename_path
    pickle.dump(path_as, open(save_dir + filename_path, "wb"))


# Run make_tree for each thread
def tree_thread(arg1, arg2):
    make_tree(arg1, arg2)


def parse(updates, pickles, out_dir, threads):

    # Create time string
    timestr = strftime("%Y%m%d%H%M%S", gmtime())


    # Ensure at least one input source specified
    if updates is None and pickles is None:
	print "No input specified! Exiting..."
	exit()

    # Create output directory
    if os.path.exists(out_dir):
	if os.listdir(out_dir) != "":
	    print "WARNING: output directory is not empty, may overwrite data!"
    else:
	print "Creating directory", out_dir
        os.makedirs(out_dir)


    # Make list of input files
    files = []
    if updates is not None:
	if not os.path.isfile(updates):
	    for root, dirs, filenames in os.walk(updates):
		for f in filenames:
		    files.append(os.path.join(root,f))
	else:
	    files.append(updates)

	# Set number of threads
	try:
	    nr_of_threads = threads
	except:
	    nr_of_threads = DEFAULT_NR_OF_THREADS


	# Cannot use more than one process per input file
	if len(files) < nr_of_threads:
	    nr_of_threads = len(files)

	# Need at least one thread and on input file
	if nr_of_threads == 0:
	    print "0 threads or 0 files specified, exiting..."
	    exit()
	else:
	    print "Running parser on", nr_of_threads, "thread(s)"


	# Create input lists for each process
	thread_files = []
	for n in range(nr_of_threads):
	    thread_files.append([])
	count = 0
	for line in files:
	    thread_files[count].append(line)
	    count += 1
	    if count >= nr_of_threads:
		count = 0

	# Start processes
	processes = []
	for i in range(nr_of_threads):

	    # Create temporary directories for storing the output of each process
	    output_dir = out_dir + "/thread_"  + str(i)
	    if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	    p = Process(target=tree_thread, args = (thread_files[i], output_dir))
	    p.start()
	    processes.append(p)

	# Wait for all processes to finnish
	for proc in processes:
	    proc.join()


	# All threads done
	print "All threads done."

    else:
	nr_of_threads = 0

    # Use separate merger to merge the results
    if nr_of_threads > 1 or pickles is not None:
	merge_dir(out_dir, os.path.join(out_dir, timestr), pickles)
    else:

	filename_tree = "PrefixTree.pickle"
	filename_path = "ASpaths.pickle"
	filename_origin = "ASorigins.pickle"
	os.mkdir(os.path.join(out_dir, timestr))
	os.rename(out_dir + "thread_0/" + filename_tree, out_dir + "/" + timestr + "/" + filename_tree)
	os.rename(out_dir + "thread_0/" + filename_path, out_dir + "/" + timestr + "/" + filename_path)
	os.rename(outdir + "thread_0/" + filename_origin, out_dir + "/" + timestr + "/" + filename_origin)

    if updates is not None:
	# Removing temporary directories
	for subdir, dirs, files in os.walk(out_dir):
	    for sd in dirs:
		if sd[:7] == 'thread_':
		    shutil.rmtree(os.path.join(subdir,sd))


# Build data structures from all files in input and save as pickles.
# Defauls to running on one thread, but parallellization is possible. 
if __name__ == '__main__':

    argparser = argparse.ArgumentParser("parser_description")
    argparser.add_argument("-i","--input",help="input file or directory containting bgp updates or dumps", required=False, default=None)
    argparser.add_argument("-p","--pickles",help="pickles directory containting pickles to use as a base", required=False, default=None)
    argparser.add_argument("-o","--output",help="output directory for pickled files. Created if does not exist", required=True)
    argparser.add_argument("-t","--threads",help="number of threads used", required=False)
    args = vars(argparser.parse_args())

    parse(args['input'], args['pickles'], args['output'], args['threads'])




