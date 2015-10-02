----------------------------------------------------------
Using unified_parser.py for parsing BGP updates and dumps:
----------------------------------------------------------

unified_parser.py
	usage: ./update_parser.py -i <inputfile> -o <output directory> [-t nr_of_parallel_processes]
	
	inputfile can be either bgp dump/update or a directory containing such files

	reads updates specified in inputfile and inserts into node tree. 
	create dictionaries for origin/path ASes in the format:
        {as_nr -- [nr_of_times_seen, largest_timestamp]}

	makes save points every 15 000 files, saved as:


merger.py
	Merge pickled prefix trees and save as a new pickled prefixtree and dictionaries

node.py
	data type for prefix trees.
	contains methods for getting/creating and printing nodes. See code for more details.

parser.py
	parser for BGP files
	Author: Johan Schlamp

unpickler.py
	(Experimental) Reading pickled output files for testing purposes.
