#!/usr/bin/python
#program for running a few tests on various aspects of make_tree and node

from node import *
from py2neo import rel
from py2neo import node as neoNode
from make_tree import *
from parser import *
from datetime import datetime
import hashlib
from ripe2neo import *
import time
from db import *
from node import *

passed = 0
failed = 0
print "Running tests...."

NEO4J_PROTOCOL = "http://"                          # Protocol to be used
NEO4J_HOST = 'localhost'
NEO4J_PORT = '7474' 
NEO4J_DATA_PATH = '/db/data/'

if False:
    root = node(socket.inet_aton("0.0.0.0"), 0, [], None, False, 0)
    neo = DB()
    neo.clear()
    nodes = []
    nodes.append(node(socket.inet_aton("0.0.0.0"), 0, [], None, False, 1234))
    nodes.append(node(socket.inet_aton("0.0.0.0"), 1, [], None, False, 1234))
    nodes.append(node(socket.inet_aton("128.0.0.0"), 1, [], None, False, 1234))

    
    print "Creating node"
    neo.createIndexed(nodes[0])
    neo.createIndexed(nodes[1])
    neo.createIndexed(nodes[2])
    
    neo.finnish('node')

    print "getting node"
    neo.getIndexed(nodes[0].id_hash)
    res = neo.finnish('read')
    print res

if False:
    neo = DB()

if True:
    neo = DB()
    #neo = neo4j.GraphDatabaseService(NEO4J_PROTOCOL + NEO4J_HOST + ":" + NEO4J_PORT + NEO4J_DATA_PATH )

    nodes = []
    AS1 = [1111]
    AS2 = [2222]
    AS3 = []

    nodes.append(node(socket.inet_aton("0.0.0.0"), 0, AS1, None, False, 1234))
    nodes.append(node(socket.inet_aton("0.0.0.0"), 1, AS2, None, False, 1234))
    nodes.append(node(socket.inet_aton("128.0.0.0"), 1, AS3, None, False, 1234))
    

    neo.clear()
    
    #nodes[0].addProperty('testprop', 'testval') 

    returned_nodes = neo.getNodes("prefix")
    updateNodes = []
    newNodes = []
    createdNodes = []
    #root.addProperty('testprop', 'testval') 
    for node in nodes:
	if node.id_hash not in returned_nodes:
	    #res = neo.create(node)
            newNodes.append(node)
	    print "Created node"
            #createdNodes.append(res)
	elif node.hashval != returned_nodes[node.id_hash]:
	    updateNodes.append(node)
	    print "Node updated"
	else:
	    print "Nothing to do"
    
    #Create new nodes
    for n in newNodes:
        res = neo.createIndexed(n)
        #print res
        createdNodes.append(res)
    neo.finnish('node')
   
    # Get referece for node and parent 
    # IMPORTANT: start at 1 to exclude root node
    for i in range(0, len(newNodes)):
        if newNodes[i].mask != 0:
	    neo.getIndexed('prefix',newNodes[i].id_hash)
	    neo.getIndexed('prefix',newNodes[i].getParentID())
    refs = neo.finnish('read')
    #print refs
    # Every other ref is child, next is parent
    for i in range(0,len(newNodes) - 1):
        neo.createRel(refs[2*i][0], "child", refs[2*i + 1][0])

    neo.finnish('rel')


    #updated nodes
    for n in updateNodes:
        neo.getIndexed('prefix',n.id_hash)
    refs = neo.finnish('read')

    for i in range(0,len(updateNodes)):
        neo.update(updateNodes[i], refs[i][0])
    neo.finnish('node')

    rels = neo.getRelations('child')
    print rels
    for n in rels:
        print n

    print "Getting node activity"
    active = neo.getActivity(nodes[0].id_hash)
    print active



