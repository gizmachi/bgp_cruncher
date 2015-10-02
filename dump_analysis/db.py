#!/usr/bin/python

import hashlib
import socket
from py2neo import rel, neo4j
from py2neo import node as neoNode

# neo4j server specifications
NEO4J_PROTOCOL = "http://"         # Protocol 
NEO4J_HOST = 'localhost'           # Server address
NEO4J_PORT = '7474'                # Server port
NEO4J_DATA_PATH = '/db/data/'      # Data path

MAX_BATCH_SIZE = 30000

class DB:
    
    relBC = 0
    wBC = 0
    rBC = 0

    graph_db = neo4j.GraphDatabaseService(NEO4J_PROTOCOL + NEO4J_HOST + ":" + NEO4J_PORT + NEO4J_DATA_PATH )
   
 
    relBatch = neo4j.WriteBatch(graph_db)   # Create relations batch
    wBatch = neo4j.WriteBatch(graph_db)     # Write batch for creates
    rBatch = neo4j.ReadBatch(graph_db)      # Read batch
    time = None


    def __init__(self):
        #self.time = str(time)
        self.time = "4321"
        self.graph_db.get_or_create_index(neo4j.Node, "prefix")
        self.graph_db.get_or_create_index(neo4j.Node, "as_number")
        self.graph_db.get_or_create_index(neo4j.Node, "announce")

    # Execute batch
    # Default batch is node creation
    def finnish(self, batch='node'):
        if batch == 'node':
	    self.wBatch.run()
	    self.wBatch.clear() 
	    print "Successfully wrote " + str(self.wBC) + " nodes to Database"
	    self.wBC = 0
        elif batch == 'rel':
            self.relBatch.run()
            self.relBatch.clear()
	    print "Successfully wrote " + str(self.relBC) + " relation to Database"
	    self.relBC = 0
        elif batch == 'read':
	    res = self.rBatch.submit()
	    self.rBatch.clear()
	    print "Successfully read " + str(self.rBC) + " entries from Database"
	    self.rBC = 0
	    return res
        else:
            print "Unknown batch " + batch


    # Create in index
    # Replaces Create!
    def createIndexed(self, n):
        val = n.id_hash
	res = self.wBatch.create_in_index_or_fail(neo4j.Node,n.node_type, 'key',  val, neoNode(n.getProperties()))
        self.incBC('node')
        return res

    # Get indexed node
    # Replaces getRef
    def getIndexed(self,index, ID):
        self.rBatch.get_indexed_nodes(index, 'key', ID)
        self.incBC('read')

    # Create relationship
    def createRel(self, n1, relation, n2):
        rel_hash = self.relHash(n1, relation, n2)
        r = rel(n1, relation, n2, {'rel_type':relation,'id_hash':rel_hash})
        self.relBatch.create(r)
        self.incBC('rel')
        tmp = self.relBatch.create(r)
        self.relBatch.add_to_index(neo4j.Relationship, 'announce', 'key', rel_hash, tmp)
        self.incBC('rel')


    # Delete all relations of a given type
    def delAllRels(self, ty):
        query = neo4j.CypherQuery(self.graph_db, "match ()-[r:" + ty + "]-() delete r;")
        res = query.execute()
        print "Deleted ALL " + ty + " relations."
        

    def relHash(self, n1, relation, n2):
        rel_hash = hashlib.sha1(str(n1) + relation + str(n2)).hexdigest()
        return rel_hash

    #Update an existing node with new attributes
    def update(self, n, ref):
	#self.wBatch.set_properties(ref, n.getProperties())
	self.wBatch.set_property(ref, 'node_hash', n.hashval)
	self.wBatch.set_property(ref, 'modified', n.property_dict['modified'])
	self.wBatch.set_property(ref, n.property_dict['modified'], n.property_dict['origin'])
	self.incBC('node', 3)

    # Get number of updates for a node 
    # NOT suitable for large quantities, consider creating batch version
    # EXPERIMENTAL
    def getActivity(self, id_hash):
        static_fields = 7      # Number of attrubutes that are not state updates
	query = neo4j.CypherQuery(self.graph_db, 'START n=node(*) WHERE (n.node_id="' + id_hash + '") RETURN n')
	returned_nodes = query.execute()
        # print returned_nodes[0][0]
	return len(returned_nodes[0][0]) - static_field
        


    #Update an unannounced node
    # here we must contruct properties since we dont have any local node
    def updateUnannounced(self, ID, ref):
        time = 23232323 #TODO
        node_hash = hashlib.sha1(ID + '"[0]"').hexdigest()
	self.wBatch.set_property(ref, 'node_hash', node_hash)
	self.wBatch.set_property(ref, 'modified', str(time))
	self.wBatch.set_property(ref, str(time), '"[0]"')
	self.incBC('node', 3)



    # Query neo database for ID and hash of all nodes of a type
    # returns a dictionary with ID as key, hash as value
    def getNodes(self, ty):
	query = neo4j.CypherQuery(self.graph_db, 'START n=node(*) WHERE (n.node_type="' + ty + '") RETURN n.node_id, n.node_hash')
	returned_nodes = query.execute()
	ret_dict = {}
        for entry in returned_nodes:
            ret_dict[entry[0]]=entry[1]
        print "Read " + str(len(returned_nodes)) + " entried from database"
        return ret_dict

    def getAnnouncedNodes(self):
	query = neo4j.CypherQuery(self.graph_db, 'START n=node(*) WHERE (n.node_type="prefix") AND NOT n.origin="[0]" RETURN n.node_id')
	returned_nodes = query.execute()
	ret_list = []
        for entry in returned_nodes:
            ret_list.append(entry[0])
        print "Read " + str(len(returned_nodes)) + " entried from database"
        return ret_list


    # Query neo database for ID and hash of all relations of a type
    # returns a dictionary with ID as key, hash as value
    def getRelations(self, ty):
	query = neo4j.CypherQuery(self.graph_db, 'START r=rel(*) WHERE (r.rel_type="' + ty + '") RETURN r.id_hash')
	returned_rels = query.execute()
	ret_hashes = []
        for entry in returned_rels:
            ret_hashes.append(entry[0])
        print "Read " + str(len(returned_rels)) + " entried from database"
        return ret_hashes

    #Drop entire database
    def clear(self):
        self.graph_db.clear()


    def setMOAS(self):
        print "Updating MOAS tagging in database"
        query = neo4j.CypherQuery(self.graph_db, "match (n)-[r:announce]-(b) with n, count(r) as nr where n.node_type='prefix' and nr>1 set n.moas=true return count(*);")
        res = query.execute()
        print "Database contains " + str(res[0][0]) + " MOASes."

    # Count entrries in current batch and write to database when exceeding max size
    def incBC(self, batch, n=1):
        if batch == 'node':
            self.wBC += n
	    if self.wBC >= MAX_BATCH_SIZE:
		self.finnish(batch)
		self.wBC = 0
        elif batch == 'rel':
            self.relBC += n
	    if self.relBC >= MAX_BATCH_SIZE:
		self.finnish(batch)
		self.relBC = 0
        elif batch == 'read':
            self.rBC += n
            # don't chop up read batches
	    #if self.rBC >= MAX_BATCH_SIZE:
	    #	print "Chopping up read batch, may mess up references!!!"
	    #	self.finnish(batch)
	    #	self.rBC = 0
        else:
            print "Unknown batch", batch
        



