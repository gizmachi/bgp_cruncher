#!/usr/bin/python
from optparse import OptionParser
from dpkt import bgp
from node import *
from asnode import *
from statistics import *
from py2neo import rel, neo4j
from py2neo import node as neoNode
import socket
import sys
from parser import *
from db import *

announced_nodes = []
withdrawn_nodes = []

def make_tree(filename="sample.123.321.dump.gz"):
    #Print statistics at the end of the program
    printstat = False 

    stat = statistics(1234)
    #Create binary tree root
    root = node(socket.inet_aton("0.0.0.0"), 0, [], None, False, 0)
    
    dump = Parser(filename)
    loop = True

    #Loop over the input file, reading one line at a time.
    while loop:
        try:
            line = dump.next()
        except:
            print "EOF"
            break
        #Parsing dumps
        if line[0] == 'D': 
            for entry in line[3]:
		fromSet = False
                time = entry[-1]
                act = 'A'     #Action: A|W
		revoked = None
		mask = line[2]
		prefix = int2ip(line[1])
		if act == "W":
		    revoked = 'revoked'
		else:
		    revoked = None
		origin = parseASpath(entry, stat)
		new_node = node(socket.inet_aton(prefix), mask, origin, revoked, fromSet, time)
                addAction(act, root, new_node, stat)
        #Parsing updates
	elif line[0] == 'U':
            for entry in line[3]:
                time = entry[-1]
		fromSet = False
		act = entry[0]     #Action: A|W
		revoked = None
		mask = entry[2]
		prefix = int2ip(entry[1])
		if act == "W":
		    revoked = 0
		else:
		    revoked = None
		origin = parseASpath(entry, stat)
		new_node = node(socket.inet_aton(prefix), mask, origin, revoked, fromSet, time)
                addAction(act,root, new_node, stat)
        #Unknown type (neither dump nor update)
        else:
	    print "Unknown message type " + line[0]

    return root

# Mostly exists for statistics, which are no longer used...
# Consider recycling. Could be performed after tree is built.
def addAction(act,root, new_node, stat):
    #Announcement        
    if act == "A":
	#actually += 1
	try:
	    announced_nodes.append(new_node)
	    stat.addIPv4() #Count announced ipv4 prefixes
	    stat.addMask(new_node.mask) #Count mask lengths
            root.insert(new_node, stat)
	except socket.error:
	    stat.addIPv6() #Cound announced IPv6 prefixes
    # Withdrawal
    elif act == "W":
	#actually += 1
	try:
	    withdrawn_nodes.append(new_node)
	    stat.rmIPv4() #Count removed IPv4 prefixes
            root.revoke(new_node, stat)
	except socket.error:
	    stat.rmIPv6() #Count removed IPv6 prefixes

#Parse an AS path string to either an INT, a list of INTs or "bad origin" if error.
# Return a list of AS numbers or [] 
def parseASpath(p, stat):
    try:
        aspath = p[3].split(" ")
        lastAS = aspath[len(aspath)-1] #AS or AS-set
    except:
        return []
    try:
        origin = [int(lastAS)] #Origin is last AS, error if bad format or AS-set
    except:
        if '}' in lastAS: #Error was due to AS-set, parse it. 
            try:
                tmpstr = p[3].split('{')
                tmpstr = tmpstr[len(tmpstr)-1].replace('}', '')
                tmpstr = tmpstr.replace(',', ' ') #sometimes separated by comma
                tmpstr = tmpstr.split(' ') # set origin to a list of all ASes in set
                origin = []
                for AS in tmpstr:
                    origin.append(int(AS)) #Convert to integers
                fromSet = True
                stat.addASset()
                stat.addMoas()
                #stat.addMoas() #Consider all AS-sets as MOAS
            except:
                print "AS-set parser failed to parse " + p[3]
                return []
        else:
            print "AS parser failed to parse " + p[3]
            return []
    return origin


def getNodes(node):
    as_nums = []          # AS numbers
    as_nodes = []         # Corresponding AS nodes
    ann_nodes = []        # announced nodes
    ann_id_list = []      # announced node IDs
    pref_nodes = getNodesRecursive(node, as_nums, ann_nodes, ann_id_list) 
    
    # Create asnodes for all as numbers 
    for AS in as_nums:
        as_nodes.append(asnode(AS))
    #as_nodes = as_nums
    
    return pref_nodes, as_nodes, ann_nodes, ann_id_list

def getNodesRecursive(node, asn, ann, ann_id):
    # Return lists of announced nodes 
    pref_nodes = []
    as_nodes = []
    # Recursive call
    if node.left is not None:
        pref_nodes += getNodesRecursive(node.left,asn,ann,ann_id)
    if node.right is not None:
        pref_nodes  += getNodesRecursive(node.right,asn,ann,ann_id)

    pref_nodes.append(node)

    # Add unique AS numbers to as_nodes
    # Node may have multiple origins
    if node.origin != [0]:
        ann.append(node)
        ann_id.append(node.id_hash)
        for AS in node.origin:
            if AS not in asn:
                asn.append(AS)

    return pref_nodes

# Update databade according to file
def addFileToNeo(filename):
    #Create Database
    db = DB()

    ########## Create binary tree in memory#########
    # Set global lists of modified nodes
    print "building tree from file"
    tree = make_tree(filename)
    pref_nodes, as_nodes, announced_nodes, announced_id = getNodes(tree)
    #print "Nr of announced nodes:", len(announced_nodes)

    #Delete tree to save memory, not needed any more
    tree = None
    print "Reading existing prefixes from database"
    db_pref_dict = db.getNodes('prefix')
    print "Redaing announced prefixes from database"
    db_announced_pref = db.getAnnouncedNodes()
    print "Reading existing AS nodes from database"
    db_as_dict = db.getNodes('as_number')

    ##### Compare db and dump prefix nodes##########
    new_nodes = []
    updated_nodes = []

    #print pref_nodes[0]
    for n in pref_nodes:                              # Check all nodes 
        if n.id_hash in db_pref_dict:                 # Exists in DB
            if n.hashval != db_pref_dict[n.id_hash]:  # Modified
                updated_nodes.append(n)               # Update node
        else:                                         # New node
            new_nodes.append(n)			      # List of new nodes

    # Create new nodes
    created_nodes = []
    for n in new_nodes:
        res = db.createIndexed(n)
        created_nodes.append(res)
    print "Writing new prefixes to database..."
    db.finnish('node')

    ####Update modified nodes
    # Get references to originals
    print "Reading obsolete nodes..."
    for n in updated_nodes:
        db.getIndexed('prefix',n.id_hash)
    refs = db.finnish('read')
    # Add changes
    for i in range(0, len(updated_nodes)):
        db.update(updated_nodes[i], refs[i][0])
    # Write changes to DB
    print "Writing updated nodes to database..."
    db.finnish('node')


    unannounced_node_id = []
    #print db_announced_pref
    for n in db_announced_pref:
        if not n in announced_id:
            db.getIndexed('prefix', n)
            unannounced_node_id.append(n)
    print "Reading unannounced node references..."
    refs = db.finnish('read')

    for i in range(len(refs) -1):
        db.updateUnannounced(unannounced_node_id[i], refs[i][0])
    # Write changes to DB
    print "Writing unannounced node updates to database..."
    db.finnish('node')
    



    # Create child relations
    for i in range(0, len(new_nodes)):
        if new_nodes[i].mask != 0:
            db.getIndexed('prefix', new_nodes[i].id_hash)
            db.getIndexed('prefix', new_nodes[i].getParentID())
    print "Reading relation referenes for created nodes..."
    refs = db.finnish('read')          

    #  Write relations to database
    for i in range(0,len(new_nodes) - 1):
        db.createRel(refs[2*i + 1][0], "child", refs[2*i][0])
    print "Writing relations for created nodes..."
    db.finnish('rel')



    ##### Create AS nodes and relations##############################
    new_nodes = []         # REUSED, pref nodes no longer needed
    #updated_nodes = []     # REUSED, pref nodes no longer needed

    # Classify nodes
    for n in as_nodes:
        if not n.id_hash in db_as_dict:                   # Exists in DB
	    new_nodes.append(n)			      # List of new nodes

    # Create new nodes
    created_nodes = []
    for n in new_nodes:
        res = db.createIndexed(n)
        created_nodes.append(res)
    print "Writing new AS nodes to database..."
    db.finnish('node')

    ##### Update modified nodes
    # AS NODES DO NOT GET MODIFIED, no update required
    # Delete all old announce relations
    # Consider optimizing this to just removing unused announcements
    db.delAllRels('announce')

    ###### Create announced relations
    #rel_hashes = db.getRelations('announce')
    #print "RELATION HASHES",rel_hashes
    ctr = 1
    for i in range(len(announced_nodes)):
        for AS in announced_nodes[i].origin:
	    db.getIndexed('prefix', announced_nodes[i].id_hash)
	    db.getIndexed('as_number', asnode(AS).id_hash)
            ctr += 1
        
    print "Reading relation referenes for announced nodes..."
    refs = db.finnish('read')        

    #local_announce_rels = []    
    # Write relations to database
    for i in range(0,len(announced_nodes) - 1):
        if db.relHash(refs[2*i + 1][0], "announce", refs[2*i][0]) not in rel_hashes:
	    db.createRel(refs[2*i + 1][0], "announce", refs[2*i][0])
    print "Writing relations for created nodes..."
    db.finnish('rel')

    db.setMOAS()

        #h = db.relHash(refs[2*i + 1][0], "announce", refs[2*i][0])
        #if h not in rel_hashes:
	#db.createRel(refs[2*i + 1][0], "announce", refs[2*i][0])
        #else: 
        #   local_announce_rels.append(h) 
    print "Writing announce relations..."
    db.finnish('rel')
    db.setMOAS()

    print "...exiting..."


if __name__ == '__main__':

    # Filename as first arg, otherwise use default
    print "Parsing file"
    if len(sys.argv) != 2:
        filename = "sample.123.321.dump.gz"
    else:
        filename = sys.argv[1]
    addFileToNeo(filename)


