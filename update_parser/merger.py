#!/usr/bin/python

import cPickle as pickle
import os
import sys
from node import *

OUT_DIR = "/mnt/rir2neo_data/final_pickle/out/"
DATA_DIR = "/mnt/rir2neo_data/final_pickle/data/"

TREE_NAME = "PrefixTree.pickle"
AS_ORIGIN_NAME = "ASorigins.pickle"
AS_PATH_NAME = "ASpaths.pickle"

TRAVERSED = 0

def add_tree(root, tree, size):

   # get current node
   t = tree.int_tuple()
   node = root.getNode(t[0], t[1])

   # update counters
   node.announce_count += tree.announce_count
   node.withdraw_count += tree.withdraw_count

   # update timestamps
   if tree.announce_last > node.announce_last:
      node.announce_last = tree.announce_last
   if tree.withdraw_last > node.withdraw_last:
      node.withdraw_last = tree.withdraw_last

   # print stats
   global TRAVERSED
   TRAVERSED += 1
   if TRAVERSED % (size/10) == 0:
      print "...%2i%% added." % (TRAVERSED / (size/10) * 10)

   # recurse
   if tree.left is not None:
      add_tree(root, tree.left, size)
   if tree.right is not None:
      add_tree(root, tree.right, size)


def add_dict(root, data):
   for AS in data:
      if AS in root:
         root[AS][0] += data[AS][0]
         if data[AS][1] > root[AS][1]:
            root[AS][1] = data[AS][1]
      else:
         root[AS] = data[AS]
   return root


def merge_dir(data_dir, out_dir, base_dir=None):
   global TRAVERSED

   ###############################
   print "\n## MERGING TREES ##"
   print "###################\n"
   ###############################

   # create empty tree
   root = node()

   TRAVERSED = 0
   paths = set()

   # Add base pickles directory to build upon
   if base_dir is not None:
       for subdir, dirs, files in os.walk(base_dir):
	  for f in files:
	     paths.add(subdir)


   # Add tmp files for merge
   for subdir, dirs, files in os.walk(data_dir):
      for f in files:
         paths.add(subdir)

   count = 0
   for path in sorted(paths):
      try:
	 TRAVERSED = 0
	 count += 1
	 file_path = os.path.join(path, TREE_NAME)
         update_tree = pickle.load(open(file_path, 'rb'))
	 size = update_tree.size()
	 print "UPDATE tree " + str(count) + "/" + str(len(paths)) + " '" + os.path.join(path, TREE_NAME) + "' loaded (size=" + str(size) + ")."
	 add_tree(root, update_tree, size)
	 print "...new root size=" + str(root.size()) + ".\n"
	 #os.remove(file_path)
      except:
	 print "Could not read file:",file_path

   # save final tree
   os.mkdir(out_dir)
   root_file = os.path.join(out_dir, 'PrefixTree.pickle')
   print "Saving root tree to '" + root_file + "'."
   pickle.dump(root, open(root_file, "wb"))
   print "...ok!"
   root = None
   update_tree = None



   ######################################
   print "\n\n## MERGING AS ORIGINS ##"
   print "########################\n"
   ######################################

   # create empty dict
   asorigins = dict()

   count = 0
   for path in sorted(paths):
      try:
	 count += 1
	 file_path = os.path.join(path, AS_ORIGIN_NAME)
         update_dict = pickle.load(open(file_path, 'rb'))
	 print "adding UPDATE dict " + str(count) + "/" + str(len(paths)) + " from " + os.path.basename(os.path.dirname(path)) + " (size=" + str(len(update_dict)) + ")."
	 asorigins = add_dict(asorigins, update_dict)
	 print "...new dict size=" + str(len(asorigins)) + ".\n"
	 #os.remove(file_path)
      except:
	 print "Could not read file:",file_path

   # save final dict
   dict_file = os.path.join(out_dir, 'ASorigins.pickle')
   print "Saving AS origins dict to '" + dict_file + "'."
   pickle.dump(asorigins, open(dict_file, "wb"))
   print "...ok!"



   ####################################
   print "\n\n## MERGING AS PATHS ##"
   print "######################\n"
   ####################################

   # create empty dict
   aspaths = dict()

   count = 0
   for path in sorted(paths):
      try:
	 count += 1
	 file_path = os.path.join(path, AS_PATH_NAME)
         update_dict = pickle.load(open(file_path, 'rb'))
	 print "adding UPDATE dict " + str(count) + "/" + str(len(paths)) + " from " + os.path.basename(os.path.dirname(path)) + " (size=" + str(len(update_dict)) + ")."
	 aspaths = add_dict(aspaths, update_dict)
	 print "...new dict size=" + str(len(aspaths)) + ".\n"
	 #os.remove(file_path)
      except:
	 print "Could not read file:",file_path

   # save final dict
   dict_file = os.path.join(out_dir, 'ASpaths.pickle')
   print "Saving AS paths dict to '" + dict_file + "'."
   pickle.dump(aspaths, open(dict_file, "wb"))
   print "...ok!\n"


#if __name__ == '__main__':
#    merge_dir(DATA_DIR, OUT_DIR)

