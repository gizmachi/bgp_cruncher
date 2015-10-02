#!/usr/bin/python

import cPickle as pickle
import sys
from node import *

# AS origins 
origin_as = pickle.load(open("bgp_asorigins.pickle", "rb"))
len_o = len(origin_as)
print origin_as[56357]

# AS paths
path_as = pickle.load(open("bgp_aspaths.pickle", "rb"))
len_p = len(path_as)
#print path_as[56357]

total_as = path_as
total_as.update(origin_as)
len_t = len(total_as)

print "paths:", len_p, float(len_p)/float(len_t), "%"
print "origins:", len_o, float(len_o)/float(len_t), "%"
#print "origins:", len(origin_as)
print "total:", len_t
print "Overlap:", float(len_o + len_p - len_t)/float(len_t)
# prefix tree
#tree = pickle.load(open("pickeled_prefix", "rb"))
#print "Testing to print the leafs..."
#tree.printLeafs()



#print "Prefix tree has", tree.size(), "nodes."
print "Done"
