#!/usr/bin/python

import struct
import socket
import hashlib

from py2neo import rel, neo4j
from py2neo import node as neoNode
#from db import *

class node:

    ASset = None
    mask = None
    prefix = None
    origin = None
    revoked = None
    isLeaf = None

    left = None
    right = None


    time = None
    hashval = None
    id_hash = None
    property_dict = None
    node_type = "prefix"

    def __init__(self, pref, msk, orgn, rvkd, ASset, time):
        self.ASset = ASset      #Origin derived from AS-set"
        self.isLeaf = True      #This is a leaf node (until a child is created)
        self.prefix = pref      #Network address 
        self.mask = msk         #Network mask
        self.origin = []         #List of announcements
        self.revoked = []       #List of revokations
        self.time = time        #timestamp from file
        printstr =  "Creating node " + socket.inet_ntoa(pref) + "/" + str(msk) #Helpful message to print

        # Use 0 to indicate unannounced prefixes
        self.origin += orgn
        if self.origin == []:
            self.origin.append(0)
 
        if rvkd is not None:    #If not revoked (it seldom is)
            self.revoked.append(rvkd)
        self.left = None        #No child node 
        self.right = None       #No child node
        #print printstr #Uncomment to print info about created node

        #Create object hash vaue for later comparison.
        self.id_hash = hashlib.sha1(self.toStr()).hexdigest()
        self.property_dict = {}
        self.property_dict['prefix']=socket.inet_ntoa(pref)
        self.property_dict['mask']=msk
        self.property_dict['modified']=time
        self.property_dict['origin']=str(self.origin)
        self.property_dict[str(time)]=str(self.origin)

        self.updateHash() 

    def addProperty(self, name, val):
        self.property_dict[name] = val
        self.updateHash()

    def getProperties(self):
        self.property_dict['origin'] = str(self.origin)
        params = {
            'node_type':self.node_type,
            'node_id':self.id_hash,
            'node_hash':self.hashval,
            }
        params.update(self.property_dict)
        return params

    def updateHash(self):
        hashstr = self.id_hash + str(self.origin) # type, prefix, mask, origin
        self.hashval = hashlib.sha1(hashstr).hexdigest()

    # Construct ID hash of parent node. 
    # Note: if toStr() is changed, change here as well!
    def getParentID(self):
        if self.mask == 0:
            print "Getting parent of ROOT!!"
        parentstring = "prefix: " + self.parentPref() + '/' + str(self.mask - 1)
        pid = hashlib.sha1(parentstring).hexdigest()
        return pid
                 

    #returns string represetatio of relevant data from the node
    def toStr(self):
        string = self.node_type + ": " + socket.inet_ntoa(self.prefix) + '/' + str(self.mask)
        return string

    def insert(self, new, stat):
        self.nodeActivity(new, 'i', stat)

    def revoke(self, new, stat):
        self.nodeActivity(new, 'r', stat)

    def nodeActivity(self, new, action, stat):
        if new.mask <= self.mask:
            print "Trying to modify node with too short mask: " + str(new.mask) 
            return
        elif new.mask == self.mask + 1:
            if self.isLeft(new.prefix, self.mask + 1):
                if self.left is None:
                    self.left = new
                elif action == 'i':
                    if not new.origin[0] in self.left.origin and self.left.origin != []:
                        if 0 in self.left.origin:
                            self.left.origin.remove(0)
                        #MOAS found!
                        self.left.origin += new.origin
                elif action == 'r':
                    self.left.revoked.append(new.revoked[0])
                else: #This should not happen. 
                    print "Unknown action!"
                    return
            else:
                if self.right is None:
                    self.right = new
                elif action == 'i':
                    if not new.origin[0] in self.right.origin and self.right.origin != []:
                        if 0 in self.right.origin:
                            self.right.origin.remove(0)
                        #MOAS found!
                        self.right.origin += new.origin
                elif action == 'r':
                    self.right.revoked.append(new.revoked[0])
                else: #This should not happen
                    print "Unknown action!"
                    return
        else: #Do recursive add
            if self.isLeft(new.prefix, self.mask + 1):
                if self.left is None: #Create intermediate node
                    self.left = node(self.prefix, self.mask + 1, [], None, False, self.time)
                self.left.nodeActivity(new, action, stat)
            else:
                if self.right is None: #Create intermediate node
                    tmp = struct.unpack('!L', self.prefix)[0]
                    tmp = tmp | 2**(32 - (self.mask + 1))
                    self.right = node(struct.pack('!L', tmp), self.mask + 1, [], None, False, self.time)
                self.right.nodeActivity(new, action, stat)
        #At lesat one child exists at this point
        self.isLeaf = False

    #Determine if a node is a 'left' node in the tree, i.e. the last bit in the prefix is a zero. 
    def isLeft(self, pref, k):
        print pref
        print struct.unpack('!L', pref)[0]
        if struct.unpack('!L', pref)[0] & int(2**(32 - k)) == 0:
	    #K-th bit is 0
            return True
	else:
            return False

    #Calculate the prefix of the parent node by setting the last bit in the prefix to zero
    def parentPref(self):
        #Set the last network bit (according to mask) to zero.
        tmp = int(bin(2**(self.mask - 1) - 1)[2:].zfill(32)[::-1], 2)  & struct.unpack('!L', self.prefix)[0]
        tmp = struct.pack('!L', tmp)
        tmp = socket.inet_ntoa(tmp)
        return tmp

