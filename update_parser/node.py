#!/usr/bin/python

'''
Data structure for building prefix trees
Author Josef Gustafsson <gustafss@in.tum.de>
Author Johann Schlamp <schlamp@in.tum.de>

'''

import struct
import socket
import hashlib
from parser import *

class node:

    parent = None
    left = None
    right = None

    announce_last = 0		# Latest Timestamp of any announce message
    announce_count = 0
    withdraw_last = 0		# Latest Timestamp of any withdraw message
    withdraw_count = 0

    def __init__(self, parent = None):
	self.parent = parent

    #Print node data in a humanly comprehensive form
    def printNode(self):
        print self.cidr()
        print "Announcements:", self.announce_count, "Last:", self.announce_last
        print "Withdrawals:", self.withdraw_count, "Last:",self.withdraw_last
        print ''

    # Get CIDR notation of node 
    def cidr(self, prefint=0, prefmask=0, tmp=False):
        if self.parent is not None:
	    prefint, prefmask = self.parent.cidr(prefint, prefmask+1, True)
            bit = (self.parent.right == self)
            prefint = (prefint << 1) | bit
        if tmp:
	    return prefint, prefmask
        for i in range(prefmask, 32):
            prefint = (prefint << 1) | False
	return socket.inet_ntoa(struct.pack("!I", prefint)) + "/" + str(prefmask)

    # Get tuple of prefix(INT) and mask(INT)
    def int_tuple(self, prefint=0, prefmask=0, tmp=False):
        if self.parent is not None:
            prefint, prefmask = self.parent.int_tuple(prefint, prefmask+1, True)
            bit = (self.parent.right == self)
	    prefint = (prefint << 1) | bit
        if tmp:
            return prefint, prefmask
        for i in range(prefmask, 32):
            prefint = (prefint << 1) | False
        return prefint, prefmask


    # Update node announcement data
    def announce(self, time):
        self.announce_count += 1
        if time > self.announce_last:
            self.announce_last = time

    # Update node withdrawal data
    def withdraw(self, time):
        self.withdraw_count += 1
        if time > self.withdraw_last:
            self.withdraw_last = time

    # Return total size of tree with root in this node
    def size(self):
	size = 1
	if self.left is not None:
            size += self.left.size()
	if self.right is not None:
	    size += self.right.size()
        return size

    # Recursively print each node in tree with root in this node
    def printTree(self):
	self.printNode()
	if self.left is not None:
            self.left.printTree()
	if self.right is not None:
	    self.right.printTree()
	
    # Recursively print every node that has seen any activity in tree with this node as root
    def printLeafs(self):
	if self.announce_count + self.withdraw_count != 0:
	    self.printNode()
	if self.left is not None:
	    self.left.printLeafs()
	if self.right is not None:
	    self.right.printLeafs()

    # Get node matching a prefix and mask
    # Create node if it does not exist
    def getNode(self, prefix, mask, depth=0):

	# This whould not happen
        if mask < depth:
            print "ERROR: Trying to modify node with too short mask: " + str(new.mask) 
            return None

        # Current node is the requested node
        elif mask == depth:
            return self  

        # Node is child of this node
        elif mask == depth + 1:
            if self.isLeft(prefix, mask):
                if self.left is None:
                    self.left = node(self)
                return self.left
            else:
                if self.right is None:
                    self.right = node(self)
                return self.right

        # Node is further down in the tree, do recursive call
        else:
            if self.isLeft(prefix, depth + 1):
                if self.left is None: 
	            prf, msk = self.int_tuple()
                    self.left = node(self)
                return self.left.getNode(prefix, mask, depth + 1)
            else:
                if self.right is None:
                    tmp, msk = self.int_tuple()
                    tmp = tmp | 2**(32 - (depth + 1))
                    self.right = node(self)
                return self.right.getNode(prefix, mask, depth + 1)


    #Determine if a node is a 'left' node in the tree, i.e. the last bit in the prefix is a zero. 
    def isLeft(self, pref, k):
        if pref & int(2**(32 - k)) == 0:
	    #K-th bit is 0
            return True
	else:
            return False


