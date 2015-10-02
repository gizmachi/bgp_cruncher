#!/usr/bin/env python
# -*- coding: latin-1 -*-

import sys
import cPickle as pickle                # to output objects to file (cPickle as it is faster than pickle)
import gzip                             # to read the extracted file
import re                               # regular expressions to 
import hashlib                          # to calculate hashes of the objects
import time                             # for performance testing
import os                               # to remove and rename files
import socket                           # to make ip conversion to binary
import struct                           # to make ip conversion to binary
import logging                          # always helpful for debugging ;-)
import subprocess                       # used to secure copy (scp) dumps to local path
import collections                      # need in convert function
from netaddr import IPRange, IPNetwork  # to transfer IP ranges to CIDRs (as fallback)
from dictdiffer import DictDiffer      # used to calculate the difference of two dictionaries
from binarytree import BinTree         # used to store objects in a binary tree
from py2neo import neo4j, node, rel, cypher, exceptions # needed to work with py2neo



PATH_TO_RIPE_DB = '/home/christian/ripe_dumps/'     # Path to the dump files
#PATH_TO_RIPE_DB = 'leavenworth:/srv/ftp/rir-db/ripe/'
PICKLE_FILE = 'inet_ranges_to_cidrs.p'              # Name of the pickle file mapping from inetranges to CIDR notations
LOCAL_PATH = './'                                   # path for temporary storing the files
TEMP_FILE_NAME = "temp"                             # Name of a temporary converted file
CLEAR_GRAPH_DB = False                              # TODO: REMOVE AFTER TESTING!
SPECIAL_MODE = False                                # Should only be used for special dumps (e.g. 2013-01-25) where tons of node properties have changed
                                                    # If set to TRUE: avoids that each changed node get's a copy node, consider carefully when using this mode
                                                    
## Variables specific to neo4j
NEO4J_PROTOCOL = "http://"                          # Protocol to be used
NEO4J_HOST = 'localhost'                            # Host name of the webserver
NEO4J_PORT = '7474'                                 # Port to the webserver
NEO4J_DATA_PATH = '/db/data/'                       # Path of the web interface 
NEO4J_USERNAME = 'neo4j-db'     # User with write access to neo4j-graph
NEO4J_PASSWORD = 'neo4jEWS#1'   # Password of the user
ASN_INDEX = None
ROOT_INDEX = None
STATISTIC_ROOT = None
GRAPH_DB = None
NEO4J_VERSION = None

## Configuration settings and statistics
SCRIPT_START_TIME = None        # To measure the runtime of the script
SOME_FUTURE_TIME = 99999999     # Wildcard needed to specify replaced time in nodes and relations <yyyymmdd>
BATCH_SIZE_LIMIT = 30000        # Maximum amount of items in a batch
CHUNK_SIZE_LIMIT = 30000        # Limit of items in lists at which lists are split into chunks
DATE_OF_FILE = None             # Holds the date extracted from the dump file name
CREATION_TIME = None            # Holds a dictionary containing creation and replaced time

SET_OF_RELEVANT_OBJECTS = set(['aut-num', 'inetnum', 'inet6num', 'route', 'route6', 'domain', 'mntner', 'organisation', 'as-set', 'role', 'person', 'irt'])
# Different types of relations
MAINTAINER_RELATIONS = set(['mnt_by', 'mnt_lower', 'mnt_ref', 'mnt_routes', 'mbrs_by_ref', 'mnt_domains', 'mnt_irt'])
IMPORT_EXPORT_RELATIONS = set(['import', 'mp_import', 'export', 'mp_export', 'default', 'mp_default'])
OTHER_RELATIONS = set(['origin', 'org', 'nic_hdl', 'abuse_c', 'tech_c', 'admin_c', 'members', 'maps_to'])
DOMAIN_NAME_RELATIONS = set(['abuse_mailbox', 'notify'])
RELATIONSHIP_PROPERTIES = IMPORT_EXPORT_RELATIONS | MAINTAINER_RELATIONS | DOMAIN_NAME_RELATIONS | OTHER_RELATIONS

# dummy entries that are ignored when parsing the dump
SET_OF_DUMMY_ENTRIES =set(['DUMY-RIPE', 'RIPE', 'UNSPECIFIED', 'unread@ripe.net 20000101',
            'unread@ripe.net', 'ripe-dbm@ripe.net', 'ripe-dbm@ripe.net 20090724', 'ROLE-RIPE',
            'RIPE-NCC-LOCKED-MNT', 'RIPE-DBM-MNT', 'RIPE-ERX-MNT', 'RIPE-GII-MNT',
            'RIPE-NCC-AN-MNT', 'RIPE-NCC-AS-MNT', 'RIPE-NCC-END-MNT', 'RIPE-NCC-ENd-MNT',
            'RIPE-NCC-HM-MNT', 'RIPE-NCC-HM-PI-MNT', 'RIPE-NCC-LOCKED-MNT', 'RIPE-NCC-MNT',
            'RIPE-NCC-REVERSE-MNT', 'RIPE-NCC-RIS-MNT', 'RIPE-NCC-RPSL-MNT', ''])
# dummy nodes that have to be ignored when creating relationships
SET_OF_DUMMY_NODES = set(['AS-ANY', 'AS-ANYCAST', 'ANY-MNT', 'ANY', 'ROLE-RIPE'])    




################################################################################
def ip2int(addr):    
    ''' 
    convert ip address to integer
    '''                                                    
    return struct.unpack("!I", socket.inet_aton(addr))[0]                       

################################################################################
def int2ip(addr):    
    '''
    convert integer to ip address
    '''                                                        
    return socket.inet_ntoa(struct.pack("!I", addr))    
    
################################################################################
def create_new_nodes(lst_of_new_nodes, dict_objs_from_dump, mapping_node_key_to_node_reference):
    '''
    Create all nodes that are new in the dump
    Params:
        lst_of_new_nodes: A list of unique objects names that need to be created
        dict_objs_from_dump: Dictionary holding all objects from the dump
        mapping_node_key_to_node_reference: Dictionary that maps from the node key to it's internal neo4j id
    '''
    
    batch_counter = 0
    counter_created_nodes = 0
    list_of_created_nodes = []
    batch_create_new_nodes = neo4j.WriteBatch(GRAPH_DB)
    
    # iterate over the set and create the new nodes using batches
    for new_node in lst_of_new_nodes:
    
        list_with_node_details = dict_objs_from_dump.get(new_node)
        
        list_with_node_details[1].update(CREATION_TIME)
        list_with_node_details[1].update({"name": list_with_node_details[0].get("index_value")})
        list_with_node_details[1].update({"unique_key": list_with_node_details[0].get("unique_key")})
        
        if list_with_node_details[0].get("index"):
            # object has an index, so additionally index it    
            batch_create_new_nodes.create_in_index_or_fail(neo4j.Node, list_with_node_details[0].get("index"),
                                                            list_with_node_details[0].get("index_key"),
                                                            list_with_node_details[0].get("index_value"),
                                                            abstract=list_with_node_details[1])
            
        else:
            # object has no index, so just create it
            batch_create_new_nodes.create(node(**list_with_node_details[1]))      
        batch_counter +=1

        # submit the batch for every BATCH_SIZE_LIMIT iteration 
        batch_counter, result = execute_batch(batch_create_new_nodes, "submit", batch_counter)
        if result:
            counter_created_nodes += BATCH_SIZE_LIMIT
            print "\tCurrent number of created nodes ({}), extending the result..".format(counter_created_nodes)
            # append the IDs of the created nodes to the list
            list_of_created_nodes[len(list_of_created_nodes):] = [item._id for item in result]
 
    # If batch is not empty, execute it one last time
    if batch_create_new_nodes:
        batch_counter, result = execute_batch(batch_create_new_nodes, "submit", batch_counter, bool_last_run = True)
        # append the IDs of the created nodes to the list
        list_of_created_nodes[len(list_of_created_nodes):] = [item._id for item in result]
    
    # For all the new nodes we created, we need to update the mapping dictionary
    # such that relations to and from these new nodes can be created!
    # As we know for sure, that both lists are in the same order, we can do this by iterating over one of the lists
    print "\tAdd all the new nodes to the mapping dictionary.."
    if len(list_of_created_nodes) == len(lst_of_new_nodes):
        for i in xrange(0, len(list_of_created_nodes)):
            mapping_node_key_to_node_reference.update({lst_of_new_nodes[i]: list_of_created_nodes[i]})

    else:
        print "\tLISTS ARE NOT OF EQUAL LENGTH! SHOULD NOT HAPPEN!"
        print "\tlen(list_of_created_nodes):", len(list_of_created_nodes)
        print "\tlen(lst_of_new_nodes)        :", len(lst_of_new_nodes)
        sys.exit(1)
        
        
    return 0

  
################################################################################
def create_relationships_of_new_nodes(lst_of_new_nodes, dict_objs_from_dump, mapping_node_key_to_node_reference):
    '''
    Create the relationships of all new nodes in the dump. This function is seperated
    from the function create_new_nodes to make sure that all meanwhile exist
    such that the relationships to and from these nodes can be created
    
    Params:
        lst_of_new_nodes: A list of unique objects names that need to be created
        dict_objs_from_dump: Dictionary holding all objects from the dump
        mapping_node_key_to_node_reference: Dictionary that maps from the node key to it's internal neo4j id
    Return:
        Number of new relationships that were created
    '''
    
    list_of_rel_tuples = []
    batch_counter = 0
    counter_created_rels = 0
    batch_create_new_relationships = neo4j.WriteBatch(GRAPH_DB)
    # Iterate over the new nodes and parse all the relationships
    print "\tParse the relationships of all new nodes..."
    for start_node in lst_of_new_nodes:
        list_with_node_details = dict_objs_from_dump.get(start_node)
        
        # parse the relationships, if there are any and add them to the list
        if list_with_node_details[2]:
            list_of_rel_tuples.extend(parse_relationships(list_with_node_details[2], mapping_node_key_to_node_reference.get(start_node), mapping_node_key_to_node_reference))
    
    # Create all the relationships in the list
    print "\nA total number of {} new relationships found; Start to create them (if any) ...".format(len(list_of_rel_tuples))
    for (start_node, rel_type, end_node), property_dict in list_of_rel_tuples:
        property_dict.update(CREATION_TIME) #set the creation and replaced property of the relation

        batch_create_new_relationships.create(rel(GRAPH_DB.node(start_node), rel_type, GRAPH_DB.node(end_node), **(property_dict))) #somehow this is rather slow, but I can't think of another way to do this
        batch_counter +=1

        
        # submit the batch for every BATCH_SIZE_LIMIT iteration
        batch_counter, result = execute_batch(batch_create_new_relationships, "run", batch_counter)
        if batch_counter == 0: # batch has been executed
            counter_created_rels += BATCH_SIZE_LIMIT
            print "\tCurrent number of created relationships ({}).".format(counter_created_rels)

        
    # If batch is not empty, execute it one last time
    if batch_create_new_relationships:
        batch_counter, result = execute_batch(batch_create_new_relationships, "run", batch_counter, bool_last_run = True)


    return len(list_of_rel_tuples)


################################################################################
def mark_nodes_and_rels_as_replaced(lst_of_nodes_to_mark, mapping_node_key_to_node_reference):
    '''
    Handles all nodes that do not occur in the dump anymore
        --> change node property 'replaced' to <DATE_OF_FILE>
        --> add property 'missed in dump' to <DATE_OF_FILE>
        --> remove node from corresponding index (if it was indexed)
        --> add node to corresponding index with key 'OBSOLETE' (if indexed before)
        --> mark all outgoing relations (set 'replaced' to <DATE_OF_FILE>   
    '''
    
    batch_counter = 0
    ref_to_node_ids = []
    dict_with_node_params = {}
    nodes_and_rels_to_mark = [] # contains all nodes and relationships that need to be marked
    batch_mark_removed_nodes = neo4j.WriteBatch(GRAPH_DB)
    
    # get the reference to each node
    ref_to_node_ids = [(mapping_node_key_to_node_reference.get(node_key)) for node_key in lst_of_nodes_to_mark]
    
    # query the graph and return node ids, node name, node type and a collection of it's unreplaced outgoing relationships
    if NEO4J_VERSION == 2:
        query = neo4j.CypherQuery(GRAPH_DB, "START n=node({node_list}) MATCH n-[r]->() WITH n, COLLECT(r) as relas RETURN ID(n), n.name, n.obj_type, filter(rel IN relas WHERE rel.replaced = {replaced_time})")
    else:
        query = neo4j.CypherQuery(GRAPH_DB, "START n=node({node_list}) MATCH n-[r?]->() WITH n, COLLECT(r) as relas RETURN ID(n), n.name, n.obj_type, filter(rel IN relas WHERE rel.replaced = {replaced_time})")
    
    # split the list of node_ids into chunks to avoid huge DB queries and assmble the results afterwards 
    for chunk_of_node_ids in chunker(ref_to_node_ids, CHUNK_SIZE_LIMIT):
        #params = {"node_list": ref_to_node_ids, "replaced_time" : SOME_FUTURE_TIME}
        params = {"node_list" : chunk_of_node_ids, "replaced_time" : SOME_FUTURE_TIME}   
        query_result = query.execute(**params)
        query_result = [[GRAPH_DB.node(entry[0]), entry[1], entry[2], entry[3]] for entry in query_result] 
        nodes_and_rels_to_mark.extend(query_result)         
    
    # Iterate over the list of nodes and for each node
    #   set the replaced property to the current date
    #   set all outgoing rels to replaced
    #   remove it from the current index (if it was indexed)
    #   and add it as obsolete to the index (if it was indexed) 
    for ref_to_node, node_name, node_type, node_relations in nodes_and_rels_to_mark:   
        # set the replaced property of the node and a notification that it missed in dump
        batch_mark_removed_nodes.set_property(ref_to_node, "replaced", DATE_OF_FILE)
        batch_counter +=1        
        batch_mark_removed_nodes.set_property(ref_to_node, "missed_in_dump", DATE_OF_FILE)
        batch_counter +=1        
        
        # set all outgoing relations of the node to replaced
        for rel in node_relations:
            batch_mark_removed_nodes.set_property(rel, "replaced", DATE_OF_FILE)
            batch_counter +=1
              
        # if it is an indexed node (=aut_num) then add it with a different key to the index
        if node_type == 'AUT_NUM':
            # using check_obj_type to get the index, index key and index value of the node
            dict_with_node_params = check_object_type({"aut_num": node_name})
            
            # remove node from current index
            batch_mark_removed_nodes.remove_from_index(neo4j.Node, dict_with_node_params.get("index"),
                                                key=dict_with_node_params.get("index_key"),
                                                value=dict_with_node_params.get("index_value"),
                                                entity=ref_to_node)
            batch_counter +=1            
            # add node to index with key "OBSOLETE"
            batch_mark_removed_nodes.add_to_index(neo4j.Node, dict_with_node_params.get("index"),
                                                "OBSOLETE",
                                                dict_with_node_params.get("index_value"),
                                                ref_to_node)
            batch_counter +=1    
               
        # submit the batch for every BATCH_SIZE_LIMIT iteration
        batch_counter, result = execute_batch(batch_mark_removed_nodes, "run", batch_counter)
          
    # force a last batch execution  
    if batch_mark_removed_nodes:
        batch_counter, result = execute_batch(batch_mark_removed_nodes, "run", batch_counter, bool_last_run = True)


    return 0


################################################################################
def update_node_properties(lst_of_changed_nodes, dict_objs_from_dump, mapping_node_key_to_node_reference):
    '''
    Update the properties of all nodes whose properties have changed. To keep the relationships untouched,
    a copy of each node is created and the the property 'replaced' is set to the current date of file. The
    actual node is then updated with the new properties and a new creation time is set in order to be able
    to track that some properties have changed.
    
    Params:
        lst_of_changed_nodes: A list of unique objects names that have changed
        dict_objs_from_dump: Dictionary holding all objects from the dump
        mapping_node_key_to_node_reference: Dictionary that maps from the node key to it's internal neo4j id
    '''
    batch_counter = 0
    batch_update_node_props = neo4j.WriteBatch(GRAPH_DB)
    list_with_nodes_properties = []     # contains a list with dictionaries of the propeties of each update node
    
    # split the list into chunks if is to large to avoid to big graph queries and assemble results afterwards
    for chunk_of_changed_nodes in chunker(lst_of_changed_nodes, CHUNK_SIZE_LIMIT):
        # get all properties of the changed nodes from the graph-db
        # we need the props to equip the copies of those nodes (=the obsolete nodes) with it        
        results = GRAPH_DB.get_properties(*[GRAPH_DB.node(mapping_node_key_to_node_reference.get(chunk_of_changed_nodes[j])) for j in range(0, len(chunk_of_changed_nodes))])
        list_with_nodes_properties.extend(results)
   

    # Iterate over the changed nodes and update the properties accordingly     
    # Note: both lists (list_with_nodes_properties) and lst_of_changed_nodes will have the same length
    #       and are also in the same order, as <get_properties> and <chunker> returned in same order
    #       which allows us to iterate over <i> and access them at position <i>
    for i in xrange(0, len(lst_of_changed_nodes)):
        list_details_of_current_ripe_obj = dict_objs_from_dump.get(lst_of_changed_nodes[i])
        # first make a copy of this node and add it to the same index, but with key obsolete
        # Note: Here we would have to use the function create_in_index instead of create_in_index_or_fail
        #       Reason: Multiple obsolete nodes can exist under the same key value pair
        #       However: create_in_index is not working correctly in py2neo 1.6 -> see Mails with Nigel Small
        #       Solution: Use two commands ("create" and "add_to_index") as workaround 
        copy_node = batch_update_node_props.create(list_with_nodes_properties[i])
                               
        # only index the copy of the node, if the node was indexed before
        if list_details_of_current_ripe_obj[0].get("index"):
            batch_update_node_props.add_to_index(neo4j.Node,
                                              list_details_of_current_ripe_obj[0].get("index"),
                                              "OBSOLETE",
                                              list_details_of_current_ripe_obj[0].get("index_value"),
                                              copy_node)                                                        
        batch_counter +=1  
                                                      
        # set the replaced property of the copy (obsolete) node                                          
        batch_update_node_props.set_property(copy_node, "replaced", DATE_OF_FILE)
        batch_counter +=1
        
        # Update the properties and set them to the (changed) node
        list_details_of_current_ripe_obj[1].update(CREATION_TIME)
        list_details_of_current_ripe_obj[1].update({"name": list_details_of_current_ripe_obj[0].get("index_value")})
        list_details_of_current_ripe_obj[1].update({"unique_key": list_details_of_current_ripe_obj[0].get("unique_key")})
        batch_update_node_props.set_properties(GRAPH_DB.node(mapping_node_key_to_node_reference.get(lst_of_changed_nodes[i])), list_details_of_current_ripe_obj[1])
        batch_counter +=1
        
        # submit the batch for every BATCH_SIZE_LIMIT iteration 
        batch_counter, result = execute_batch(batch_update_node_props, "run", batch_counter)
            
    # If batch is not empty, execute it one last time
    if batch_update_node_props:
        batch_counter, result = execute_batch(batch_update_node_props, "run", batch_counter, bool_last_run = True)
    

    return 0

################################################################################
def update_node_properties_special_mode(lst_of_changed_nodes, dict_objs_from_dump, mapping_node_key_to_node_reference):
    '''
    IMPORTANT: 
        Using the special version of update_node_properties should only be used in very rare situation
        The code is mainly duplicated from the "normal" mode (=update_node_properties) but to decrease the amount
        of 'if-statements' on for the normal dumps, we decided to seperate those two methods.
    When to use this special mode: 
        Only use this mode if a really huge amount of nodes have changed in the RIPE dump due to
        some modification of the dump. This mode prevents that of every altered node a copy node
        is created. An example to use this mode is dump 2013-01-25 where all "changed" properties have been reset,
        maintainer descrictions have been added from dumy to real ones and organisation names "org_name" was set
        from dumy-value to real one
    For all objects where exeptionally the <ignore_keys> have changed, no copy node will be created but only
    the obj_hash and obj_properties_hash will be updated
    All other objects (at least one other key except <ignore_keys> has changed) are treated as usual
    (see the normal mode of this function "update_node_properties"
   
    Params:
        lst_of_changed_nodes: A list of unique objects names that have changed
        dict_objs_from_dump: Dictionary holding all objects from the dump
        mapping_node_key_to_node_reference: Dictionary that maps from the node key to it's internal neo4j id
    '''
    batch_counter = 0
    batch_update_node_props = neo4j.WriteBatch(GRAPH_DB)
    list_with_nodes_properties = []     # contains a list with dictionaries of the propeties of each update node
    artificial_keys = set(['name', 'unique_key', 'created', 'replaced', 'obj_hash', 'obj_properties_hash', 'obj_relationships_hash']) # set of keys that definitly differ
    ignore_keys = set(['changed', 'org_name',])
    really_changed_objects = 0  # objects that have really changed
    pseudo_changed_objects = 0  # objects where only the <ignore_keys> have changed
    
    # split the list into chunks if is to large to avoid to big graph queries and assemble results afterwards
    for chunk_of_changed_nodes in chunker(lst_of_changed_nodes, CHUNK_SIZE_LIMIT):
        # get all properties of the changed nodes from the graph-db
        # we need the props to equip the copies of those nodes (=the obsolete nodes) with it        
        results = GRAPH_DB.get_properties(*[GRAPH_DB.node(mapping_node_key_to_node_reference.get(chunk_of_changed_nodes[j])) for j in range(0, len(chunk_of_changed_nodes))])
        list_with_nodes_properties.extend(results)
   
    
    print "\n\nNOTE: Using special mode!"
    # for all nodes where exclusivley the 'changed' property was modified, 
    #   --> set the new 'changed' property / or remove property of now empty
    #   --> update the obj_hash and obj_property_hash
    # for all other nodes proceed as in normal mode
    #   --> create (indexed) copy node, set replaced property to copy node, update props of the changed node   
    for i in xrange(0, len(lst_of_changed_nodes)):
        list_details_of_current_ripe_obj = dict_objs_from_dump.get(lst_of_changed_nodes[i])
        # check for added keys that are new in dump compared to db
        added_keys = DictDiffer(list_details_of_current_ripe_obj[1], list_with_nodes_properties[i]).added()
        # check for removed keys that do not exist in dump but in db, but ignore <artificial_keys> and <ignore_keys>
        # Note: artificial keys have been modified after reading dumps so they can not be compared
        removed_keys = DictDiffer(list_details_of_current_ripe_obj[1], list_with_nodes_properties[i]).removed() - artificial_keys - ignore_keys
        # check for keys that have changed but ignore <artificial_keys>
        changed_keys = DictDiffer(list_details_of_current_ripe_obj[1], convert(list_with_nodes_properties[i])).changed() - artificial_keys - ignore_keys
        if ((not added_keys and not changed_keys and not removed_keys) or (len(changed_keys) == 1 and "descr" in changed_keys and list_details_of_current_ripe_obj[0].get('obj_type') == 'MNTNER')):
            # Object only changed due to ripe DB modification--> update obj_hash and obj_properties_hash 
            pseudo_changed_objects +=1
            if 'changed' in list_details_of_current_ripe_obj[1] and 'changed' in list_with_nodes_properties[i]:
                # 'changed' was modified so set new property
                batch_update_node_props.set_property(GRAPH_DB.node(mapping_node_key_to_node_reference.get(lst_of_changed_nodes[i])), 'changed', unicode(list_details_of_current_ripe_obj[1].get('changed'), errors='ignore'))
                batch_counter +=1
            elif 'changed' in list_details_of_current_ripe_obj[1] and 'changed' not in list_with_nodes_properties[i]:
                # 'changed' was added so set new property
                batch_update_node_props.set_property(GRAPH_DB.node(mapping_node_key_to_node_reference.get(lst_of_changed_nodes[i])), 'changed', unicode(list_details_of_current_ripe_obj[1].get('changed'), errors='ignore'))
                batch_counter +=1
            elif 'changed' not in list_details_of_current_ripe_obj[1] and 'changed' in list_with_nodes_properties[i]:
                # 'changed' was completly removed but existed before
                batch_update_node_props.delete_property(GRAPH_DB.node(mapping_node_key_to_node_reference.get(lst_of_changed_nodes[i])), 'changed')
                batch_counter +=1
                
            if 'org_name' in list_details_of_current_ripe_obj[1]:
                batch_update_node_props.set_property(GRAPH_DB.node(mapping_node_key_to_node_reference.get(lst_of_changed_nodes[i])), 'org_name', unicode(list_details_of_current_ripe_obj[1].get('org_name'), errors='ignore'))
                batch_counter +=1
            if (len(changed_keys) == 1 and "descr" in changed_keys and list_details_of_current_ripe_obj[0].get('obj_type') == 'MNTNER'):
                #batch_update_node_props.set_property(GRAPH_DB.node(mapping_node_key_to_node_reference.get(lst_of_changed_nodes[i])), 'descr', list_details_of_current_ripe_obj[1].get('descr'))
                batch_update_node_props.set_property(GRAPH_DB.node(mapping_node_key_to_node_reference.get(lst_of_changed_nodes[i])), 'descr', unicode(list_details_of_current_ripe_obj[1].get('descr'), errors='ignore'))
                batch_counter +=1
                
            # update hashes for all objects
            batch_update_node_props.set_property(GRAPH_DB.node(mapping_node_key_to_node_reference.get(lst_of_changed_nodes[i])), 'obj_hash', list_details_of_current_ripe_obj[1].get('obj_hash'))
            batch_update_node_props.set_property(GRAPH_DB.node(mapping_node_key_to_node_reference.get(lst_of_changed_nodes[i])), 'obj_properties_hash', list_details_of_current_ripe_obj[1].get('obj_properties_hash'))
            batch_counter +=2           
             
        else:
            # Object really changed --> proceed as in normal mode
            really_changed_objects +=1            
            print "$-$ THIS OBJECT REALLY CHANGED:", list_with_nodes_properties[i].get("name")
            print "\t$$ added keys:", added_keys
            print "\t$$ removed keys:", removed_keys
            print "\t$$ changed keys:", changed_keys
            
            # continue with exactly the same procedure as on "normal mode"
            copy_node = batch_update_node_props.create(list_with_nodes_properties[i])
                                   
            # only index the copy of the node, if the node was indexed before
            if list_details_of_current_ripe_obj[0].get("index"):
                batch_update_node_props.add_to_index(neo4j.Node,
                                                  list_details_of_current_ripe_obj[0].get("index"),
                                                  "OBSOLETE",
                                                  list_details_of_current_ripe_obj[0].get("index_value"),
                                                  copy_node)                                                        
            batch_counter +=1  
                                                          
            # set the replaced property of the copy (obsolete) node                                          
            batch_update_node_props.set_property(copy_node, "replaced", DATE_OF_FILE)
            batch_counter +=1
            
            # Update the properties and set them to the (changed) node
            list_details_of_current_ripe_obj[1].update(CREATION_TIME)
            list_details_of_current_ripe_obj[1].update({"name": list_details_of_current_ripe_obj[0].get("index_value")})
            list_details_of_current_ripe_obj[1].update({"unique_key": list_details_of_current_ripe_obj[0].get("unique_key")})
            batch_update_node_props.set_properties(GRAPH_DB.node(mapping_node_key_to_node_reference.get(lst_of_changed_nodes[i])), list_details_of_current_ripe_obj[1])
            batch_counter +=1
            
        # submit the batch for every BATCH_SIZE_LIMIT iteration 
        batch_counter, result = execute_batch(batch_update_node_props, "run", batch_counter)
    

    print "\n\n\tReally changed objects:", really_changed_objects
    print "\tPseudo changed objects:", pseudo_changed_objects
     
            
    # If batch is not empty, execute it one last time
    if batch_update_node_props:
        batch_counter, result = execute_batch(batch_update_node_props, "run", batch_counter, bool_last_run = True)
    

    return 0


################################################################################
def update_node_relationships(lst_nodes_with_changed_rels, dict_objs_from_dump, mapping_node_key_to_node_reference):
    '''
    Update the relationships of nodes whose relationships have changed. This involves
    new relationships, removed relationships and changed relationships. Each relationship
    is identified by a 3-tuple consisting of (start_node, relationship_type, end_node). For
    relationships of type 'import', 'export' and 'default' additionally the 'statement' is
    considered while comparing. Changed and removed relationships are marked with the
    'replaced' property which is set to the date of the dump file. Finally, for all nodes
    in the list the relationships hashes will be updated.
    
    Params:
        lst_nodes_with_changed_rels: A list of unique objects names whose relationships have changed
        dict_objs_from_dump: Dictionary holding all objects from the dump
        mapping_node_key_to_node_reference: Dictionary that maps from the node key to it's internal neo4j id        
    Return:
        Number of new, removed and updated relationships
    '''
    
    batch_counter = 0
    batch_update_rels = neo4j.WriteBatch(GRAPH_DB)
    
    mapping_rel_tuple_to_relation_and_statement = {} # maps from a relation tuple to a list containing the reference of the relation and the statement
    set_of_dump_4_tuples = set([]) # holds all rel tuples + statement parsed from the dump
    set_of_dump_3_tuples = set([]) # holds all rel tuples (w/o statement) parsed from the dump
    set_of_db_4_tuples = set([]) # holds all rel tuples + statement queried from graph-db
    set_of_db_3_tuples = set([]) # holds all rel tuples (w/o statement) queried from graph-db
    
    rels_to_update = set([])    # contains all relations, where the statement property has changed
    rels_to_create = set([])    # contains all relations, that are completely new in dump compared to db
    rels_to_remove = set([])    # contains all relations, that did not occur in the dump anymore, but where still in db
    list_of_db_rels = []        # contains the all results from the db query(ies)
    dict_rel_properties = {}    # contains the properties of a relation, when a new one needs to be created
       
    list_of_node_ids = [mapping_node_key_to_node_reference.get(lst_nodes_with_changed_rels[i]) for i in range(0, len(lst_nodes_with_changed_rels))]
    
    
    
    # query the graph with all nodes with changed relationships as start point,
    # and return all of the outgoing rels, start_node, type, end_node and "statement" if it has one
    if NEO4J_VERSION == 2:
        query_nodes_rels = neo4j.CypherQuery(GRAPH_DB, "START n=node({node_id_list}) MATCH (n)-[r]->() WHERE HAS(r.replaced) AND r.replaced = {replaced_time} RETURN r, r.statement")
    else:
        query_nodes_rels = neo4j.CypherQuery(GRAPH_DB, "START n=node({node_id_list}) MATCH (n)-[r]->() WHERE HAS(r.replaced) AND r.replaced = {replaced_time} RETURN r, r.statement?")
    
    # split the list of node_ids into chunks to avoid huge DB queries and assmble the results afterwards 
    for chunk_of_node_ids in chunker(list_of_node_ids, CHUNK_SIZE_LIMIT):  
        params = {"node_id_list" : chunk_of_node_ids, "replaced_time" : SOME_FUTURE_TIME}   
        list_of_db_rels.extend(query_nodes_rels.execute(**params))
    
    
    # transform the query to a list of 4-tuples (relation tuples + statement) and to a dictionary that maps from each rel tuple to the corresponding relation
    for item in list_of_db_rels:
        start_node_id = item[0].start_node._id
        relation_type = item[0].type
        end_node_id = item[0].end_node._id
        set_of_db_4_tuples.update([(start_node_id, relation_type, end_node_id, item[1])])
        set_of_db_3_tuples.update([(start_node_id, relation_type, end_node_id)])
        mapping_rel_tuple_to_relation_and_statement[(start_node_id, relation_type, end_node_id)] = [item[0], item[1]]
        
    for start_node in lst_nodes_with_changed_rels:
        list_with_node_details = dict_objs_from_dump.get(start_node)
        dict_of_relationships = list_with_node_details[2]
        
        # parse the relationships, if there are any
        if dict_of_relationships:
            list_of_dump_rels = parse_relationships(dict_of_relationships, mapping_node_key_to_node_reference.get(start_node), mapping_node_key_to_node_reference)
            
            # add the relationships (from dump) to a list of tuples
            set_of_dump_4_tuples.update([(item[0][0], item[0][1], item[0][2], item[1].get("statement")) for item in list_of_dump_rels])
            set_of_dump_3_tuples.update([(item[0][0], item[0][1], item[0][2]) for item in list_of_dump_rels])
            
    # get all relations that have changed in any kind, using the symmetric difference operation of set
    # these are nodes that are either completly new, have been removed, or the statement changed
    changed_rels = set_of_dump_4_tuples ^ set_of_db_4_tuples # symmetric difference of both 4-tuple sets
    common_rels = set_of_dump_3_tuples & set_of_db_3_tuples         # intersection of both sets of 3 tuples
    rels_only_in_dump = set_of_dump_3_tuples - set_of_db_3_tuples   # difference: dump - db
    rels_only_in_db = set_of_db_3_tuples - set_of_dump_3_tuples     # difference: db - dump
    

    
    for start_node, rel_type, end_node, statement in changed_rels:
        if (start_node, rel_type, end_node) in common_rels:
            # --> relation exists in both lists, but statements have changed 
            #Note: The var <changed_rels> conains two 4-tuples for each changed relation:
            #      the 4 tuple with the changed statement (=from dump),
            #      and the 4-tuple with the old statement (=from db)
            #      However, we store both of them and afterwards when updating the relation statement,
            #      we check which was the old and which was the new one using the mapping dictionary
            rels_to_update.update([(start_node, rel_type, end_node, statement)])
        elif (start_node, rel_type, end_node) in rels_only_in_dump:
            #--> relationship is completely new, so create it
            rels_to_create.update([(start_node, rel_type, end_node, statement)])
            pass
        elif (start_node, rel_type, end_node) in rels_only_in_db:
            #--> relationship has been removed (does not exist in dump anymore)
            #    so set the replaced property
            rels_to_remove.update([(start_node, rel_type, end_node, statement)])
            pass
        else:
            print "Should not happen!", start_node, rel_type, end_node
            sys.exit(1)
    
    
    # create the completely new relations
    print "\n###############################"
    print "\tTotal number of completely new relations:", len(rels_to_create)
    if rels_to_create:
        print "\t\tStarting to create the new relations..."
        for start_node, rel_type, end_node, statement_prop in rels_to_create:
            dict_rel_properties.clear()
            dict_rel_properties.update(CREATION_TIME)           
            if statement_prop:
                # If this relation has a statement property, update the dictionary
                dict_rel_properties.update({"statement": statement_prop})              
            # Add the relation to the batch    
            batch_update_rels.create(rel(GRAPH_DB.node(start_node), rel_type, GRAPH_DB.node(end_node), **dict_rel_properties))
            batch_counter +=1
                
            # submit the batch
            batch_counter, res = execute_batch(batch_update_rels, "run", batch_counter)
    
    
    # set the replaced property of all removed rels
    print "\n###############################"
    print "\tTotal number of removed relations:", len(rels_to_remove)
    if rels_to_remove:
        print "\t\tStarting to set the replaced property of all removed relations..."
        for start_node, rel_type, end_node, statement_prop in rels_to_remove:
            ref_to_relation = mapping_rel_tuple_to_relation_and_statement.get((start_node, rel_type, end_node))[0]
            if ref_to_relation:
                #print "\t\tRef to relation:", ref_to_relation
                batch_update_rels.set_property(ref_to_relation, "replaced", DATE_OF_FILE)
                batch_counter +=1              
            else:
                # no reference to relation found (never happens)
                pass   
            batch_counter, res = execute_batch(batch_update_rels, "run", batch_counter)  
    
    
    # update all changed rels (=create a new one) and set the replaced property of the old relation
    print "\n###############################"
    #print "rels_to_update:", rels_to_update
    print "\tTotal number of updated relations, (might be misleading):", len(rels_to_update), "/2=", len(rels_to_update)/2
    if rels_to_update:
        print "\t\tStarting to create updated relations and set the replaced property of the old relations..." 
        for start_node, rel_type, end_node, statement_prop in rels_to_update:
            dict_rel_properties.clear()
            dict_rel_properties.update(CREATION_TIME)
            ref_to_relation = mapping_rel_tuple_to_relation_and_statement.get((start_node, rel_type, end_node))[0]
            if ref_to_relation:
                #print "\t\tRef to relation:", ref_to_relation, type(ref_to_relation)
                obsolete_rel_statement = mapping_rel_tuple_to_relation_and_statement.get((start_node, rel_type, end_node))[1]
                if statement_prop == obsolete_rel_statement:
                    # This is the old relation, so set replaced property
                    batch_update_rels.set_property(ref_to_relation, "replaced", DATE_OF_FILE)
                    batch_counter +=1
                else:
                    # This is the new (changed) relation, so apply it to the node
                    dict_rel_properties.update({"statement": statement_prop})
                    batch_update_rels.create(rel(GRAPH_DB.node(start_node), rel_type, GRAPH_DB.node(end_node), **dict_rel_properties))
                    batch_counter +=1
            else:
                # no reference to relation found (never happens)
                pass   
            batch_counter, res = execute_batch(batch_update_rels, "run", batch_counter)
    
    
    
    ### Update the relationship_hashes and the obj_hashes of all nodes
    #   Note: This holds for all obj_names (-->node_ids) we passed to this function,
    #         as we know that at least any kind of relation change occured. As the obj_hash
    #         is calculated over both, relationships and properties, we also need to update the obj_hash
    print "\n###############################"
    print "Updating the relationship hashes of the nodes..."   
    for node_key in lst_nodes_with_changed_rels:
        ref_to_node = GRAPH_DB.node(mapping_node_key_to_node_reference.get(node_key))
        obj_rel_hash = dict_objs_from_dump.get(node_key)[1].get("obj_relationships_hash")
        obj_hash = dict_objs_from_dump.get(node_key)[1].get("obj_hash")
        
        # update the node with the new relationship hash and obj hash
        batch_update_rels.set_property(ref_to_node, "obj_relationships_hash", obj_rel_hash)
        batch_update_rels.set_property(ref_to_node, "obj_hash", obj_hash)
        batch_counter +=2
       
        # submit the batch if batch_counter >= BATCH_SIZE_LIMIT
        batch_counter, res = execute_batch(batch_update_rels, "run", batch_counter)
         
    # Force to execute the batch a finale time, as it is the last run
    batch_counter, res = execute_batch(batch_update_rels, "run", batch_counter, bool_last_run = True)

    return len(rels_to_create), len(rels_to_remove), len(rels_to_update)/2

################################################################################
def update_obj_hash(lst_pseudo_changed_nodes, dict_objs_from_dump, mapping_node_key_to_node_reference):
    '''
    Update the nodes in the list with the real (new calculated) object hash.
    The list of pseudo changed nodes contains nodes, whose obj_hash has changed, but neither
    the property hash nor the relationship_hash have altered
    
    Params:
        lst_pseudo_changed_nodes: A list of unique objects names where the obj hash has changed
        dict_objs_from_dump: Dictionary holding all objects from the dump
        mapping_node_key_to_node_reference: Dictionary that maps from the node key to it's internal neo4j id
    '''
    batch_counter = 0
    batch_update_node_hash = neo4j.WriteBatch(GRAPH_DB)
    
    # iterate over the list of pseudo changed nodes and update the obj hash
    for i in xrange(0, len(lst_pseudo_changed_nodes)):
        list_details_of_current_ripe_obj = dict_objs_from_dump.get(lst_pseudo_changed_nodes[i])
        
        print "-#-Dump Obj:", list_details_of_current_ripe_obj[1]
                                                     
        # Update the obj_hash
        batch_update_node_hash.set_property(GRAPH_DB.node(mapping_node_key_to_node_reference.get(lst_pseudo_changed_nodes[i])), "obj_hash", list_details_of_current_ripe_obj[1].get("obj_hash"))
        batch_counter +=1
        # submit the batch for every BATCH_SIZE_LIMIT iteration 
        batch_counter, result = execute_batch(batch_update_node_hash, "run", batch_counter)
            
    # If batch is not empty, execute it one last time
    if batch_update_node_hash:
        batch_counter, result = execute_batch(batch_update_node_hash, "run", batch_counter, bool_last_run = True)

    return 0



################################################################################
def execute_batch(batch_obj, str_execution_type, counter, bool_last_run = False):
    '''
    Execute the bath if it exceeds the BATCH_SIZE_LIMIT or if the bool_last_run is set to true.
    Depending on the execution type, either .run is used which does return no results or
    the batch is submitted which returns it's results to the corresponding variable
    
    Params:
        batch_obj: A list of unique objects names whose relationships have changed
        str_execution_type: Either "run" or "submit"
        counter: Number of items in the batch
        bool_last_run: Forces execution of batch if set to true
    Return:
        The counter set to 0 and the results of the batch.
    '''
    batch_results = None
    additional_msg = ""
    if bool_last_run:
        additional_msg = "(last run)"
    if (counter >= BATCH_SIZE_LIMIT or bool_last_run == True):     
        if str_execution_type == "run":
            tmp = batch_obj.run()
            
        elif str_execution_type == "submit":
            batch_results = batch_obj.submit()
            
        else:
            print "Unknown execution type!", str_execution_type
            sys.exit(1)
        batch_obj.clear()
        counter = 0       
    else:
        # No need to execute the batch yet
        pass
    
    return counter, batch_results


################################################################################
def parse_relationships(dict_of_relationships, ref_to_start_node, mapping_node_key_to_node_reference):
    '''
    For a given start node, iterates over all its relationship keys, determines the type
    of the relationship and extracts the end node of the relationship.
    
    Params:
        dict_of_relationships: A dictionary holding all relationships of a single node
        ref_to_start_node: A reference (ID) of the given start node
        mapping_node_key_to_node_reference: Dictionary that maps from the node key to it's internal neo4j id
    Return:
        A list of all relationship 4-tuples consisting of start node, rel type, end node and statement
    '''
    
    list_of_rel_tuples = []  # contains all data of relationships of a single node [[(start_node, type, end_node), dict_of_rel],...]
    set_of_tuples = set([])  # contains the different relations (start_node, type, end_node) (uniquely!)
    end_node_obj_type = None
    for key, value in dict_of_relationships.iteritems():
        dict_of_rel_properties = {}       # contains the properties of the relationship, e.g. "accept ANY" in an import relation    
            
        # handle (mp-)import and (mp-)export and (mp-)default relationships   
        if key in IMPORT_EXPORT_RELATIONS:
            if "import" in key:     #(mp-)import
                seperator_regex = "from\s"    #"from " with at least one whitespace character at the end
                seperator_key = "from "
                rel_type = "import"
            elif "export" in key:   #(mp-)export
                seperator_regex = "to\s"    #"to " with at least one whitespace character at the end
                seperator_key = "to "
                rel_type = "export"
            elif "default" in key:  #(mp-)default
                seperator_regex = "to\s"    #"to " with at least one whitespace character at the end
                seperator_key = "to "
                rel_type = "default"
         
            for splitted_line in value.split(" || "):
                entries = []
                leading_string = '' # often used in mp-imports for specifications of adress familiy, e.g. afi ipv4.unicast 

                # check if the string contains a "refine" statement and ignorecase by using lower()
                # if so, split at every refine and add the splits to the entries
                if " refine " in splitted_line.lower():
                    refine_splits = re.split("(refine)(?i)", splitted_line)
                    for refine_split in refine_splits:
                        splits = re.split(seperator_regex, refine_split, flags=re.IGNORECASE)
                        entries.extend(splits)
           
                else:
                    entries = re.split(seperator_regex, splitted_line, flags=re.IGNORECASE)
                
                # check if the first split is some kind of leading string, e.g. afi ipv4.unicast    
                if entries[0].replace('{','').strip():
                    leading_string = entries[0].replace('{','').strip() + ' '
                    entries[:] = entries[1:] # replace the first entry
                    
                for entry in entries:
                    if entry.strip() != "":
                        s = seperator_key+entry.strip()
                        
                        end_node = s.split()[1].upper()  # the AS to which the relation exists
                        # check if the end_node is some kind of AS or AS-Set and it is not a dummy node
                        if re.match(r"AS([0-9]+$)", end_node, flags=re.IGNORECASE) and end_node not in SET_OF_DUMMY_NODES:
                            end_node_obj_type = "AUT_NUM"
                        elif re.match(r"AS([0-9]*|:|-)", end_node, flags=re.IGNORECASE) and end_node not in SET_OF_DUMMY_NODES:
                            end_node_obj_type = "AS_SET"

                        else:
                            # Object was not valid, this can always happen due to parsing, e.g. entry = '{'
                            # Those cases can be ignored without disregarding relationship information
                            continue

                        ref_to_end_node = mapping_node_key_to_node_reference.get(end_node_obj_type + "_" + end_node) # get the reference to the end node
                            
                                
                        # check if valid end_node exists
                        if ref_to_end_node:
                            dict_of_rel_properties = {"statement" : leading_string+s}    # the whole statement
                            relation_tuple = (ref_to_start_node, rel_type, ref_to_end_node)    # store all these information in a tuple   
                            
                            # check if the list already contains exactly this relation_tuple
                            # if so, then update the statement of the tuple by appending the new statement
                            # else, add this relation_tuple to the list
                            rel_tuple_already_in_list = False
                            for entry in list_of_rel_tuples:
                                if entry[0] == relation_tuple:
                                    # Tuple already exists, so upate the dictionary by appending the new statement
                                    entry[1].update({"statement" : entry[1]["statement"] + " || " + dict_of_rel_properties["statement"]})
                                    rel_tuple_already_in_list = True
                                    break

                            if not rel_tuple_already_in_list:
                                # This tuple was not in the list before, so add this relation A-[type]->B to the list
                                list_of_rel_tuples.append([relation_tuple, dict_of_rel_properties])
                        else:
                            # The relation refers to an as-block or dummy object we don't handle
                            pass
                           
            
        # handle maintainer relationships              
        elif key in MAINTAINER_RELATIONS:
            rel_type = "maintained_by"
            end_node_obj_type = "MNTNER"
            if key == "mnt_irt":
                end_node_obj_type = "IRT"
            else:
                end_node_obj_type = "MNTNER"

            for splitted_line in value.split(" || "):
                splits = splitted_line.split(',')    #they might be seperated by comma, so split them
                for entry in splits:
                    # split the entry again and use the first part of it, also strip it and convert to upper case (if there is some content at all)
                    if entry.strip(): 
                        end_node = entry.split()[0].strip().upper() 
                        ref_to_end_node = mapping_node_key_to_node_reference.get(end_node_obj_type + "_" + end_node)
                        
                        if ref_to_end_node:
                            # add the relation to the set of tuples if a valid end node was found
                            relation_tuple = (ref_to_start_node, rel_type, ref_to_end_node)
                            set_of_tuples.add(relation_tuple)
                            
                        else:
                            # The relation refers to a mntner which we don't handle (e.g dummy object)
                            pass
                    else:
                        # entry was empty
                        pass
          
        # handle all other relationships         
        elif key in OTHER_RELATIONS:      
            ##################################----NOTE----######################################################## 
            ##  Relationships of type "tech_c" and "admin_c" are not in the obj_dictionary,                      #
            ##  as long as we use anonymized ripe-dumps                                                          #
            ##  Reason: in <parse_ripe_dump> keys with dummy values (e.g. DUMY-RIPE) are ignored                 #
            ##  However, as soon as we get full ripe dumps without anonymizations, it should automatically work  #
            ######################################################################################################
            
            rel_type = key            
            if key == "origin" or key == "members":
                end_node_obj_type = "AUT_NUM"
            elif key == "org":
                end_node_obj_type = "ORGANISATION"
            elif key == "abuse_c" or key == "tech_c" or key == "admin_c" or key == "nic_hdl" or key == "maps_to":
                end_node_obj_type = ""  # No object type here, as these either refer to a nic_hdl which can be persons or roles
                                        # and these kind of objects are anyway unique without "obj_type"
                                        # or it refers to a inetnum ('maps_to') where the end_node_type is already stored in the relation
            else:
                print "Could not map relation key to type of end node"
                print "key:", key
                sys.exit(1)
            
            for splitted_line in value.split(" || "):
                splits = splitted_line.split(',')    #they might be seperated by comma, so split them
                for entry in splits:
                    # split the entry again and use the first part of it, also strip it and convert to upper case (if there is some content at all)
                    if entry.strip():
                        end_node = entry.split()[0].strip().upper() 
                        if end_node_obj_type:
                            ref_to_end_node = mapping_node_key_to_node_reference.get(end_node_obj_type + "_" + end_node)
                        else:
                            ref_to_end_node = mapping_node_key_to_node_reference.get(end_node)
                        
                        if ref_to_end_node:
                            # add the relation to the set of tuples if a valid end node was found
                            relation_tuple = (ref_to_start_node, rel_type, ref_to_end_node)
                            set_of_tuples.add(relation_tuple)
                        else:
                            # The relation most likely refers to an as-block which we don't handle
                            pass
                    else:
                        # entry was empty
                        pass
             
        # handle domain_Name relationships extracted from e-mail         
        elif key in DOMAIN_NAME_RELATIONS:
            end_node_obj_type = "DOMAIN_NAME"
            rel_type = "domain_name"
            domain_names = extract_domain_names(value)
            
            for dom_name in domain_names:            
                end_node = dom_name.upper()
                ref_to_end_node = mapping_node_key_to_node_reference.get(end_node_obj_type + "_" + end_node)                    
                if ref_to_end_node:                   
                    relation_tuple = (ref_to_start_node, rel_type, ref_to_end_node)
                    set_of_tuples.add(relation_tuple)
                else:
                    # The relation refers to a domain_name we don't handle (actually never happens)
                    pass           
                       
    # add all the tuples (without statement) to the list of relationship tuples (with statement)
    for rel_tuple in set_of_tuples:
        list_of_rel_tuples.append([rel_tuple, {}])

    return list_of_rel_tuples


################################################################################
def extract_domain_names(mail_adresses):
    '''
    Extracts the domain name out (multiple) mail address(es). Tries to figure out only
    the relevant part of the domain name, i.e 
        name@net.in.tum.de   --> tum.de
        name@bbc.co.uk       --> bbc.co.uk    
    Params:
        mail_adresses: String with mail addresses, each seperated by ||
    Return:
        Returns a set of extracted domain name(s)
    '''
    domain_names = set([])
    suffixes = set(['ac', 'ad', 'ae', 'aero', 'af', 'ag', 'ai', 'al', 'am', 'an', 'ao', 'aq', 'ar', 'arpa', 'as', 'asia', 'at', 'au', 'aw', 'ax', 'az', 'ba', 'bb', 'bd', 'be', 'bf', 'bg', 'bh', 'bi', 'biz', 'bj', 'bm', 'bn', 'bo', 'br', 'bs', 'bt', 'bv', 'bw', 'by', 'bz', 'ca', 'cat', 'cc', 'cd', 'cf', 'cg', 'ch', 'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'com', 'coop', 'cr', 'cu', 'cv', 'cx', 'cy', 'cz', 'de', 'dj', 'dk', 'dm', 'do', 'dz', 'ec', 'edu', 'ee', 'eg', 'er', 'es', 'et', 'eu', 'fi', 'fj', 'fk', 'fm', 'fo', 'fr', 'ga', 'gb', 'gd', 'ge', 'gf', 'gg', 'gh', 'gi', 'gl', 'gm', 'gn', 'gov', 'gp', 'gq', 'gr', 'gs', 'gt', 'gu', 'gw', 'gy', 'hk', 'hm', 'hn', 'hr', 'ht', 'hu', 'id', 'ie', 'il', 'im', 'in', 'info', 'int', 'io', 'iq', 'ir', 'is', 'it', 'je', 'jm', 'jo', 'jobs', 'jp', 'ke', 'kg', 'kh', 'ki', 'km', 'kn', 'kp', 'kr', 'kw', 'ky', 'kz', 'la', 'lb', 'lc', 'li', 'lk', 'lr', 'ls', 'lt', 'lu', 'lv', 'ly', 'ma', 'mc', 'md', 'me', 'mg', 'mh', 'mil', 'mk', 'ml', 'mm', 'mn', 'mo', 'mobi', 'mp', 'mq', 'mr', 'ms', 'mt', 'mu', 'mv', 'mw', 'mx', 'my', 'mz', 'na', 'name', 'nc', 'ne', 'net', 'nf', 'ng', 'ni', 'nl', 'no', 'np', 'nr', 'nu', 'nz', 'om', 'org', 'pa', 'pe', 'pf', 'pg', 'ph', 'pk', 'pl', 'pm', 'pn', 'pr', 'pro', 'ps', 'pt', 'pw', 'py', 'qa', 're', 'ro', 'rs', 'ru', 'rw', 'sa', 'sb', 'sc', 'sd', 'se', 'sg', 'sh', 'si', 'sj', 'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'st', 'su', 'sv', 'sy', 'sz', 'tc', 'td', 'tel', 'tf', 'tg', 'th', 'tj', 'tk', 'tl', 'tm', 'tn', 'to', 'tp', 'tr', 'tt', 'tv', 'tw', 'tz', 'ua', 'ug', 'uk', 'us', 'uy', 'uz', 'va', 'vc', 've', 'vg', 'vi', 'vn', 'vu', 'wf', 'ws', 'xn', 'ye', 'yt', 'za', 'zm', 'zw'])
      
    for mail_address in mail_adresses.split(" || "):
        # substitute everything before the '@' sign
        domain_long_name = re.sub('^.*@', '', mail_address).split('/')[0].lower()
        domain = []
        # there are many "mail-adresses" with @as[0-9]+ which don't really exit, so filter them out
        if not re.match('^as[0-9]+', domain_long_name):
            # figure out which part belongs to  the domain name and which not
            # e.g.: net.in.tum.de   --> tum.de
            # but bbc.co.uk         --> bbc.co.uk #Reason: co AND uk are suffixes
            for section in domain_long_name.split('.'):
                if section in suffixes:
                    domain.append(section)
                else:
                    domain = [section]
            domain = '.'.join(domain).strip()
            # add the domain to the domain names
            domain_names.update([domain])
            
    return domain_names


################################################################################
def open_and_convert_input_file(in_file):
    '''
    Copies (scp) the input  file to a local path and opens it if the file type is either
    .db or .gz. Due to performance, it also converts the file from latin-1 to utf-8. This
    process consumes some extra time, but it definitely pays off when iterating over the
    file while parsing it.
    Params:
        in_file: A string of the file name
    Return:
        A handle of the file to parse
    '''
    global DATE_OF_FILE, CREATION_TIME
    
    path_to_file = PATH_TO_RIPE_DB + in_file
    temp_file = LOCAL_PATH + TEMP_FILE_NAME
    BLOCKSIZE = 1024*1024
    file_name, file_extension = os.path.splitext(path_to_file)
    
    # copy the dump to local path
    subprocess.call(['scp', path_to_file, LOCAL_PATH])
    try:
        if file_extension == '.gz':
            with gzip.open(LOCAL_PATH + in_file, 'rb') as inf:
                with open(temp_file, 'wb') as ouf:
                    while True:
                        data = inf.read(BLOCKSIZE)
                        if not data: break
                        converted = data.decode('latin1').encode('utf-8')
                        ouf.write(converted)
        elif file_extension == '.db':
            with open(LOCAL_PATH + in_file, 'rb') as inf:
                with open(temp_file, 'wb') as ouf:
                    while True:
                        data = inf.read(BLOCKSIZE)
                        if not data: break
                        converted = data.decode('latin1').encode('utf-8')
                        ouf.write(converted)
        else:
            print "File has a unsupported file format, only .gz and .db are supported!"
            sys.exit(1)
    except IOError:
        print 'File does not exist, or output file can not be written!'
        print 'Input File:', path_to_file
        print 'Output File:', LOCAL_PATH
        sys.exit(1)
  
    # extract the date of the dump from the file name
    try:
        DATE_OF_FILE = (int)(re.findall(r'\d{4}-\d{2}-\d{2}', in_file)[-1].replace('-', '')) # print the last match found, remove hyphens and convert from string to int
        CREATION_TIME = {"created" : DATE_OF_FILE, "replaced" : SOME_FUTURE_TIME}
    except IndexError:
        print "\tNote: Could not detect the date from the file"
        DATE_OF_FILE = 20123456    # <yyyymmdd>
        CREATION_TIME = {"created" : DATE_OF_FILE, "replaced" : SOME_FUTURE_TIME}
        #TODO: In final version, stop programm and leave default date away
        #print "Stopping script."
        #sys.exit(1)

    # try to open the file and exit if some IOError occurs
    try:
        input_file = open(temp_file, 'r') # much faster than reading latin-1 but needs conversion to uft-8 before
    except Exception:
        print "Could not open the file, going to exit!"
        print "File:", path_to_file, temp_file
        sys.exit(1)
    
    return input_file


################################################################################
def parse_ripe_dump(input_file):
    '''
    Iterates over the complete file and extracts all interesting objects. Each object
    is stored in a dictionary and all of them are stored in a list.
    Params:
        input_file: A handle to the already opend file
    Return:
        A list of all objects in the dump
    '''
    #print "Start parsing the ripe dump..."
    list_of_dump_objects = []   # a list holding all dump objects
    dict_object = {}            # dictionary containing the keys and values of one object
    dict_obj_type = {}          # dictionary holding the type of a object
    line_number = 0
    set_of_all_domain_names = set([])   # a set holding all extracted domain names
    
    for line in input_file:
        if line.split(':', 1)[0] in SET_OF_RELEVANT_OBJECTS:
            # object is interesting for us, so parse its keys and values
            while line.strip():
                # as long as there is no empty line, all data belongs to the same object
                try:
                    key, value = line.split(':', 1)   
                except ValueError:
                    # key could not be extracted so break (actually never happens)
                    print "Could not extract the key --> break"
                    break            
                       
                if key != "remarks":
                    key = key.strip().replace("-","_")  # modify the key to the desired format ('_' instead of '-') 
                    value = value.strip().split('#')[0] # only take the part up to the '#' of the value (everything else are only comments)
                    #print "Key:", key
                    #print "value:", value 
                    if value in SET_OF_DUMMY_ENTRIES:
                        value = ''
                    try:
                        line = input_file.next()
                    except StopIteration:
                        # reached last line
                        break

                    
                    while (line.strip()) and (line[0].isspace() or line[0] == '+'):
                        # line is not completely empty but the value belongs to the previous key
                        appended_value = line[1:].strip().split('#')[0]
                        if appended_value not in SET_OF_DUMMY_ENTRIES:
                            value = value + " " + appended_value                                  
                        try:
                            line = input_file.next()
                        except StopIteration:
                            # reached last line
                            break
                            
                    if value:
                        # looks a new key is coming (or end of file), so add the current key + value to the dictionary if it has a value at all
                        if dict_object.has_key(key):
                            # key already exists, so append the additional value seperated by "||",..
                            dict_object.update({key : dict_object[key] + " || " + ' '.join(value.split())}) #Note: ' '.join(value.split()) is used to remove all duplicate whitespaces
                        else:
                            dict_object.update({key : ' '.join(value.split())})                             #Note: ' '.join(value.split()) is used to remove all duplicate whitespaces
                           
                    continue
                    
                else:
                    # do not process remarks, so get the next line
                    try:
                        line = input_file.next()
                    except StopIteration:
                        # reached last line
                        break
                        
                    while (line.strip()) and (line[0].isspace() or line[0] == '+'):
                        #as long as no empty line or no new key appears, skip the additional lines of this remark
                        try:
                            line = input_file.next()
                        except StopIteration:
                            # reached last line
                            break
                                                  
                    continue # key 'remarks' is over
            
            # There has been an empty line (or end of file) so add the object to the list
            # determine the object type and add it if it was no placeholder object
            dict_obj_type = check_object_type(dict_object)
            if dict_obj_type:                           
                # extract the domain names from the object
                for key in dict_object.iterkeys():
                    if key in DOMAIN_NAME_RELATIONS:                        
                        set_of_all_domain_names.update(extract_domain_names(dict_object.get(key)))                  
                        #print "dom_names:", set_of_all_domain_names                    
                dict_object.update({'obj_type': dict_obj_type.get('obj_type')})
                list_of_dump_objects.append([dict_obj_type, dict_object])
                #list_of_dump_objects.append([dict_obj_props, dict_obj_relationships, dict_obj_type])
                
            else:
                # the object ist not interesting for us, so just ignore it
                pass
                    
            # always clear all dictionaries after every object
            dict_object = {} 
            dict_obj_type = {}
                               
        else:
            # this kind of object is definitely not relevant for us, so skip it until the next blank line
            while line.strip():
                try:
                    line = input_file.next()
                except StopIteration:
                    # reached last line
                    break    
                
                
    # parsing of file finished, so close the input_file       
    input_file.close()
      
    # At the very end of the ripe-dump we need to check if we need to add the very last object
    # This is neccessary, because the ripe-dump might not end with an empty line, but directly after remarks
    # So we need to append the last object to the list
    # Also the last value needs to be added, as the "break" is before adding the value    
    if dict_object:
        if value:
            if dict_object.has_key(key):
                # key already exists, so append the additional value seperated by "||",..
                dict_object.update({key : dict_object[key] + " || " + ' '.join(value.split())}) #Note: ' '.join(value.split()) is used to remove all duplicate whitespaces
            else:
                dict_object.update({key : ' '.join(value.split())})                             #Note: ' '.join(value.split()) is used to remove all duplicate whitespaces
                
        dict_obj_type = check_object_type(dict_object)
        if dict_obj_type:
            # extract the domain names from the object
            for key in dict_object.iterkeys():
                if key in DOMAIN_NAME_RELATIONS:
                    set_of_all_domain_names.update(extract_domain_names(dict_object.get(key)))
                            
            dict_object.update({'obj_type': dict_obj_type.get('obj_type')})
            list_of_dump_objects.append([dict_obj_type, dict_object])
            
    
    # Finally, add all domain_names that were extracted from the mails to the list of objects
    for domain_name in set_of_all_domain_names:
        dict_object = {'domain_name': domain_name}
        # even though we already know the object type, we still use this function here due to consistency
        dict_obj_type = check_object_type(dict_object)
        dict_object.update({'obj_type': dict_obj_type.get('obj_type')})   
        list_of_dump_objects.append([dict_obj_type, dict_object])

    
    #print "\tFinished."
    return list_of_dump_objects


################################################################################
def check_object_type(dict_obj):
    '''
    Determines the type of an object and allocates the corresponding index and
    unique key to it. 
    Params:
        dict_obj: A dictionary holding all keys of a single object
    Return:
        A dictionary that holds information about the object tpye, indexes and keys
    '''
    dict_with_parameter = {}
    obj_type = ""
    index = None
    index_value = ""
    index_key = ""

    #check if dict_obj contains aut_num as a key
    if "aut_num" in dict_obj:    
        obj_type = "AUT_NUM"
        index = ASN_INDEX
        index_value = dict_obj.get("aut_num")
        index_key = "CURRENT"      
        unique_key = obj_type + "_" + dict_obj.get("aut_num")
    #check if dict_obj contains inetnum as a key
    elif "inetnum" in dict_obj:
        obj_type = "INETNUM"
        index_value = dict_obj.get("inetnum")
        unique_key = obj_type + "_" + dict_obj.get("inetnum")
    #check if dict_obj contains inetnum6 as a key
    elif "inet6num" in dict_obj:
        obj_type = "INET6NUM"
        index_value = dict_obj.get("inet6num")
        unique_key = obj_type + "_" + dict_obj.get("inet6num")
    #check if dict_obj contains route as a key
    elif "route" in dict_obj:
        obj_type = "ROUTE"
        if not dict_obj.get("origin"):
            print dict_obj
        index_value = dict_obj.get("route")
        try:    # try except currently only needed because of the TAB issue detected in old ripe dumps, can be removed later
            unique_key = obj_type + "_" + dict_obj.get("route")+ "_" + dict_obj.get("origin")
        except:
            print "Somehow this failed!"
            print dict_obj
            sys.exit(1)
    #check if dict_obj contains route6 as a key
    elif "route6" in dict_obj:
        obj_type = "ROUTE6"
        index_value = dict_obj.get("route6")
        unique_key = obj_type + "_" + dict_obj.get("route6")+ "_" +dict_obj.get("origin")
    #check if dict_obj contains domain as a key
    elif "domain" in dict_obj:
        obj_type = "DOMAIN"
        index_value = dict_obj.get("domain")
        unique_key = obj_type + "_" + dict_obj.get("domain")
    #check if dict_obj contains mntner as a key
    elif "mntner" in dict_obj:
        obj_type = "MNTNER"
        index_value = dict_obj.get("mntner")
        unique_key = obj_type + "_" + dict_obj.get("mntner")
    #check if dict_obj contains organisation as a key
    elif "organisation" in dict_obj:
        obj_type = "ORGANISATION"
        index_value = dict_obj.get("organisation")
        unique_key = obj_type + "_" + dict_obj.get("organisation")
    #check if dict_obj contains as-set as a key
    elif "as_set" in dict_obj:
        obj_type = "AS_SET"
        index_value = dict_obj.get("as_set")
        unique_key = obj_type + "_" + dict_obj.get("as_set")
    elif "role" in dict_obj:
        obj_type = "ROLE"
        index_value = dict_obj.get("nic_hdl") # for role objects the nic_hdl has to be used as unique key
        unique_key = dict_obj.get("nic_hdl") # for role objects the nic_hdl has to be used as unique key
    elif "person" in dict_obj:
        obj_type = "PERSON"
        index_value = dict_obj.get("nic_hdl") # for person objects the nic_hdl has to be used as unique key
        unique_key = dict_obj.get("nic_hdl") # for person objects the nic_hdl has to be used as unique key
    elif "domain_name" in dict_obj:
        obj_type = "DOMAIN_NAME"
        index_value = dict_obj.get("domain_name")
        unique_key = obj_type + "_" + dict_obj.get("domain_name")
    elif "irt" in dict_obj:
        obj_type = "IRT"
        index_value = dict_obj.get("irt")
        unique_key = obj_type + "_" + dict_obj.get("irt")


    else:
        # unknown / unhandeld object
        return 0 # do not process this object
        
    if not unique_key or unique_key == obj_type + "_":
        # Looks like a placeholder object whose value was filtered out
        # do not procress this object
        return 0 
                
    # Due to consistency, store the keys in upper letters    
    index_key = index_key.upper()
    index_value = index_value.upper()          
    unique_key = unique_key.replace(" ","").upper() 

    dict_with_parameter = {"obj_type": obj_type, "index": index, "index_key": index_key, "index_value" : index_value, "unique_key": unique_key}
    return dict_with_parameter



################################################################################
def add_inetnum_to_binary_tree(BTree, root_node, inetnum_obj, inetnum_unique_key, dict_cidr_lookup):
    '''
    Maps the IP range of a single inetnum object to the binary tree. First inetnum is converted
    to one or multiple CIDR notations (/XY). For each CIDR the binary inetnum tree is extended by
    the corresponding leafs, where each leaf holds the unique key of the inetnum
    Params:
        BTree: A reference to the BinTree class
        root_node: Starting point of the binary tree
        inetnum_obj: Dictionary of all keys of the inetnum
        inetnum_unique_key: Unique key of the corresponding inetnum object
        dict_cidr_lookup: Dictionary read from pickle file that maps from IP range to CIDR(s)        
    Return:
        The mapping from inetnum to CIDR if it hasn't been found in the pickle file
        This dictionary will later be added to the pickle file to improve performance
        of subsequent dump files
    '''
    list_of_subnets = []
    dict_new_inetnums = {} # contains mappings of new inetnums (=ip-range) to cidrs   
    ip_range = inetnum_obj.get("inetnum")   
    
    # convert the ip range to a start and and ip
    inet_converted = ip_range.replace(' ','').split('-')
    int_start_ip = ip2int(inet_converted[0])
    int_end_ip = ip2int(inet_converted[1])
    inetnum_obj.update({'start_ip': int_start_ip, 'end_ip': int_end_ip})
    
    # lookup or convert the ip-range of the inetnum to (multiple) CIDR notations (=subnets)    
    if ip_range in dict_cidr_lookup:
        # the IP range was found in the pickle file
        list_of_subnets.extend(dict_cidr_lookup.get(ip_range))
            
    else:
        # otherwise convert the range to cidr notation
        # if the range fits into one subnet, use own code (fast)         
        inet_converted = ip_range.replace(' ','').split('-')
    
        bin_start_ip = bin(int_start_ip)[2:].zfill(32) # remove the '0b' and fill string with zero's at the front
        bin_end_ip = bin(int_end_ip)[2:].zfill(32) # remove the '0b' and fill string with zero's at the front
        number_of_hosts = 1 + int_end_ip  - int_start_ip  # there is one more host than the difference of end - start

        possible_subnet = 0
        # compare the binary start and end ip starting from the least significant bit
        for i in xrange(31, -1, -1):
            if bin_start_ip[i] == '0' and bin_end_ip[i] == '1':
                pass
            else:
                possible_subnet = i + 1
                break
        
        if 2**(32-possible_subnet) == number_of_hosts:
            # if the subnet we found equals the number of hosts in the range, this is our valid subnet
            list_of_subnets.append((bin_start_ip, possible_subnet))  
        else:
            # otherwise use the IPRange function of the netaddr module to get the cidrs (slow)             
            cidrs = IPRange(inet_converted[0], inet_converted[1]).cidrs()      
                 
            for cidr in cidrs:
                list_of_subnets.append((cidr.ip.bits().replace('.',''), cidr.prefixlen))
                
        dict_new_inetnums.update({ip_range: list_of_subnets})
    
    # add each subnet to the binary tree and mark it as a leaf    
    for bin_host_address, subnet_size in list_of_subnets:
        if subnet_size >= 0 and subnet_size <=32 and len(bin_host_address) == 32:
            inetnum_data = [bin_host_address, subnet_size, set([inetnum_unique_key]), False] # data contains: binary host address, subnet size, key of inetnum, is_leaf=false
            BTree.insert(root_node, inetnum_data)
           
        else:
            # Subnet or hostaddress are out of range (actually never happens)
            print "Somethin seems to be wrong. Subnet or Host-Address is out of range"
            print "inetnum data:", inetnum_data
            sys.exit(1)
    
    return dict_new_inetnums


################################################################################
def map_routes_to_inetnum(list_of_route_objects, BTree, root_node):
    '''
    Maps each node in the list to a leaf in the binary inetnum tree. Then update the 
    relationships of each route object and calculate it's hash values. The routes are mapped
    to the IP range of the inetnum they fit in. If routes fit into several inetnums (quite likely)
    the route is mapped to the inetnum with the smallest IP range (= the lowest leaf in the tree)
    Params:
        list_of_route_objects: A list containing all route objects 
        BTree: A reference to the BinTree class
        root_node: Starting point of the binary tree   
    Return:
        A dictionary that maps from the unique_key of each route object to it's properties and relationships
        A dictionary that maps from the unique_key of each route object to it's object hash value
    '''
    
    route_objs_from_dump = {} # maps from the route_unique_key to a list of route_type, route_props and route_rels 
    mapping_route_key_to_route_hash = {} # dictionary that maps from route_unique_key to the route_hash
    
    # for each Route object, check to which leaf (=inetnum) the route maps and store the relation
    for route_type, route_obj in list_of_route_objects:
        dict_obj_relationships = {} # clear dict before each iteration
        dict_obj_props = {}         # clear dict before each iteration      
        route = IPNetwork(route_obj.get("route"))
        route_address_bin = route.ip.bits().replace('.','')
        prefix_length = route.prefixlen # length of the mask   
        route_data = [route_address_bin, prefix_length]
        # find the lowest inetnum leaf in the tree        
        inetnums = BTree.find_inetnum_leaf(root_node, route_data)
                      
        # update the relations of the route depending on the inetnum it mapped to
        for inetnum in inetnums:
            if route_obj.has_key("maps_to"):    #if key already exists, append the additional value seperated by "||",..
                route_obj.update({"maps_to": route_obj["maps_to"] + " || " + inetnum}) 
            else:
                route_obj.update({"maps_to": inetnum})
        
        # add the object type to the object
        route_obj.update({'obj_type':  route_type.get('obj_type'), 'start_ip': int(route.network), 'end_ip': int(route.broadcast)})
        
        # seperate each object into object properties and relationship properties
        for key in route_obj:
            if key in RELATIONSHIP_PROPERTIES:
                dict_obj_relationships.update({key : route_obj[key]})
            else:
                dict_obj_props.update({key : route_obj[key]})
                                         
        #calculate the hashes and update the route property dictionary with them
        obj_hash = hashlib.sha1((str)(route_obj)).hexdigest() 
        obj_properties_hash = hashlib.sha1((str)(dict_obj_props)).hexdigest()
        obj_relationships_hash = hashlib.sha1((str)(dict_obj_relationships)).hexdigest()   
        hash_dict = {'obj_hash' : obj_hash, 'obj_properties_hash' : obj_properties_hash, 'obj_relationships_hash' : obj_relationships_hash}
        dict_obj_props.update(hash_dict)  
        
        # create a dictionary that maps from the route_unique_key to a list of route_type, route_props and route_rels
        route_objs_from_dump.update({route_type.get("unique_key") : [route_type, dict_obj_props, dict_obj_relationships]}) 
        # create a dictionary that maps from route_unique_key to the obj_hash
        mapping_route_key_to_route_hash.update({route_type.get("unique_key") : obj_hash})
                
    return route_objs_from_dump, mapping_route_key_to_route_hash


################################################################################
def preprocess_dump_objects(list_of_dump_objs, BTree, root_node):
    '''
    Calculate the hash values of all objects and update the dictionaries of the objects
    For each inetnum objects additionally call function to map IP range to binary tree
    For each route object call function to map route to inetnum tree.
    For all objects, create a dictionary that maps from each unique key to a list of object informations
    For all objects, create a dictionary that maps from each unique key to the obj hash.    
    Params:
        list_of_dump_objs: A list containing all 
        BTree: A reference to the BinTree class
        root_node: Starting point of the binary tree
    Return:
        A dictionary that maps from the unique_key of each route object to it's properties and relationships
        A dictionary that maps from the unique_key of each route object to it's object hash value
    '''
    
    dict_objs_from_dump = {} # maps from the object_unique_key a list of obj_type_params, obj_props and obj_rels 
    mapping_dump_obj_key_to_obj_hash = {} # dictionary that maps from obj_unique_key to the obj_hash
    dict_obj_relationships = {} # holds the relationships of the object
    dict_obj_props = {}         # holds the properties of the object    
    list_of_route_objects = []  # holds all objects of type "route"
    dict_cidr_lookup = {}
    dict_new_inets = {}
    
    # Use Pickle to open a file which helps
    # to quickly look up the conversion from inetnum IP range to CIDR notation
    if os.path.isfile(PICKLE_FILE):
        with open(PICKLE_FILE, 'rb') as f:
            while 1:
                try:
                    dict_cidr_lookup.update(pickle.load(f))
                except EOFError:
                    break # no more data in the file
     
    # Iterate over all the objects in the dump 
    for dict_obj_type, dict_obj in list_of_dump_objs:

        dict_obj_relationships = {} # make sure dict is empty on each iteration
        dict_obj_props = {}         # make sure dict is emtpy on each iteration
        
        # add the object type to the object
        dict_obj.update({'obj_type':  dict_obj_type.get('obj_type')})
            
        # Add all Route objects to a list. Later, we need this list
        # to map the route objects into the inetnum tree.
        # At this point however, the inetnum tree is not complete,
        # so it makes no sense to do this here. Also, hashes of route
        # objects will be calculated after mapping is done (rels will change)
        if dict_obj_type.get("obj_type") == "ROUTE":
            #print "IT IS A ROUTE"
            list_of_route_objects.append([dict_obj_type, dict_obj])   
            
        else:
            if dict_obj_type.get("obj_type") == "INETNUM":
                # convert the inetnum ip-range into cidr notation and map it in a binary tree
                dict_new_inets.update(add_inetnum_to_binary_tree(BTree, root_node, dict_obj, dict_obj_type.get("unique_key"), dict_cidr_lookup))

            # seperate each object into object properties and relationship properties
            for key in dict_obj:
                if key in RELATIONSHIP_PROPERTIES:
                    dict_obj_relationships.update({key : dict_obj[key]})
                else:
                    dict_obj_props.update({key : dict_obj[key]})
                                  
            # calculate the hashes of all objs (except routes) (obj_hash, property_hash and relationship_hash)
            obj_hash = hashlib.sha1((str)(dict_obj)).hexdigest()
            obj_properties_hash = hashlib.sha1((str)(dict_obj_props)).hexdigest()
            obj_relationships_hash = hashlib.sha1((str)(dict_obj_relationships)).hexdigest()
    
            #update the object property dictionary with the hashes
            hash_dict = {'obj_hash' : obj_hash, 'obj_properties_hash' : obj_properties_hash, 'obj_relationships_hash' : obj_relationships_hash}
            dict_obj_props.update(hash_dict)
       
            # create a dictionary that maps from the object_unique_key to a list of object_type, object_props and object rels
            dict_objs_from_dump.update({dict_obj_type.get("unique_key") : [dict_obj_type, dict_obj_props, dict_obj_relationships]}) 
            # create a dictionary that maps from obj_name to the obj_hash
            mapping_dump_obj_key_to_obj_hash.update({dict_obj_type.get("unique_key") : obj_hash})
    
    # Write all the new mappings (inetnum -> cidr) into a file using pickle
    # This file will be used for other ripe dumps to avoid long calculations
    if dict_new_inets:
        out_file = open(PICKLE_FILE, 'ab') # append the new dictionary to previous output
        pickle.dump(dict_new_inets, out_file)
        out_file.close       
                               
    # map all route objects in the list to the inetnum tree and calculate route hashes 
    route_objs_from_dump, mapping_route_key_to_route_hash = map_routes_to_inetnum(list_of_route_objects, BTree, root_node)
    
    # merge the dictionaries of all other objects with those from the routes
    dict_objs_from_dump.update(route_objs_from_dump)
    mapping_dump_obj_key_to_obj_hash.update(mapping_route_key_to_route_hash)
    return dict_objs_from_dump, mapping_dump_obj_key_to_obj_hash


################################################################################
def initialize_neo4j_graph_db():
    '''
    Make a connection to the neo4j graph database via the RESTful web interface and
    get or create all indexes we need.
    Return:
        The version of neo4j
    '''   
    global GRAPH_DB, ASN_INDEX, ROOT_INDEX, STATISTIC_ROOT, NEO4J_VERSION
    
    neo4j.authenticate(NEO4J_HOST + ":" + NEO4J_PORT, NEO4J_USERNAME, NEO4J_PASSWORD)
    GRAPH_DB = neo4j.GraphDatabaseService(NEO4J_PROTOCOL + NEO4J_HOST + ":" + NEO4J_PORT + NEO4J_DATA_PATH)
    print "NEO VERSION:", GRAPH_DB.neo4j_version[0]
    try:    
        if GRAPH_DB.neo4j_version[0] >= 2:
            NEO4J_VERSION = 2
        else:
            NEO4J_VERSION = 1
    except exceptions.ClientError:
        print "Could not authenticate to neo4j!"
        print "Going to exit.."
        sys.exit(1)
        
    if CLEAR_GRAPH_DB:
        print "Clearing graph.."
        GRAPH_DB.clear() # clear the whole database
        print "\tDone."
    ASN_INDEX = GRAPH_DB.get_or_create_index(neo4j.Node, "AS_Numbers") # an index for all aut-num objs
    ROOT_INDEX = GRAPH_DB.get_or_create_index(neo4j.Node, "Root_Nodes") # an index for root nodes, e.g. inetnum tree root, statistic root
    STATISTIC_ROOT = ROOT_INDEX.get_or_create("Statistic", "Root", {"name": "statistic_root_node"})

    return NEO4J_VERSION


################################################################################
def initialize_binary_tree():
    '''
    Initialize the binary tree by instantiating the class and setting a root node
    Return:
        The instantiated class object of the binary tree and its root node
    '''
    # create a tree and add a root node
    BTree = BinTree()
    root_cidr = IPRange('0.0.0.0', '255.255.255.255').cidrs()
    path_length = root_cidr[0].prefixlen # length of the mask
    binary_host_address = root_cidr[0].ip.bits().replace('.','') # binary representation of CIDR  
    root_data = [binary_host_address, path_length, set([]), False, None] # data contains: binary host address, subnet size, inetnum-range, is_leaf=false, subnet in cidr notation
    root_node = BTree.insert(None, root_data)
    
    return BTree, root_node

################################################################################

def convert(data):
    '''
    Helper function to convert ASCII strings to UTF-8
    Is only used in special mode as a helper function
    
    Params:
        data: any kind of list, string or dictionary
    Return:
        data transformed to UTF-8 strings
    '''
    if isinstance(data, basestring):
        return data.encode('utf-8')
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data
           
###############################################################################
def chunker(seq, size):
    '''
    split a list into smaller chunks, each with a maximum size
    '''
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))

################################################################################
def write_db_statistics(new_nodes, removed_nodes, changed_nodes, nodes_with_changed_props, nodes_with_changed_rels, unchanged_nodes, number_new_rels, number_removed_rels, number_updated_rels, number_current_nodes):
    '''
    Collect all the statistics of the processed dump and write it as properties
    to a node in the graph
    Params:
        Various numbers about new, changed and replaced nodes and relationships
    '''
    #create a node that holds various statistic parameters about the graph, the runtime of the script, etc.
    script_runtime = int(time.clock() - SCRIPT_START_TIME)
    statistic_dict = {"date": DATE_OF_FILE, "seconds_script_runtime": script_runtime,
                        "number_new_nodes": new_nodes,
                        "number_replaced_nodes": removed_nodes,
                        "number_changed_nodes": changed_nodes,
                        "number_nodes_with_changed_properties": nodes_with_changed_props,
                        "number_nodes_with_changed_relationships": nodes_with_changed_rels, 
                        "number_unchanged_nodes": unchanged_nodes,
                        "number_new_relationships": number_new_rels,
                        "number_removed_relationships": number_removed_rels,
                        "number_updated_relationships": number_updated_rels, # only for relationships with statement property (import, export, default)
                        "number_total_current_nodes_before": number_current_nodes} # equals the number of current nodes before the script was executed
    print "\n###################################################"
    print "-------------- Statistics of dump -----------------"
    for key, value in statistic_dict.iteritems():
        print '{0:40} {1:9d}'.format(key, value)
    
    # create node with relation to the statistics root node
    GRAPH_DB.create(statistic_dict, (STATISTIC_ROOT, "STATISTICS", 0, {"data": DATE_OF_FILE}))

    return 0
  
  
    
####################################################
############ START OF MAIN ROUTINE #################
####################################################
def main(input_ripe_dump):
    '''
    Main routine of the script. Following tasks are done by calling various functions:
        --> Query graph-db and return ID, unique_name and obj_hash of all current nodes
        --> Parse the whole ripe dump and store all objects in dictionaries
        --> Compare the nodes in the graph with the ones in the dump
        --> Create all nodes (and their relationships) that occur in the dump but not in the graph-db
        --> Set all nodes (and their rels) that exist in the graph but not in the dump as replaced
        --> Update all nodes and rels that exist in dump and graph-db, but have changed
            --> a copy of each changed node is made and the old node is set to replaced
            --> each changed relationship is updated by a replaced property
    '''
    global NEO4J_VERSION, SCRIPT_START_TIME
    
    if SPECIAL_MODE:
        var = raw_input("You are about to use the special mode! Are you REALLY sure?\nPress 'Y' to continue: ")
        if var == 'Y' or var == 'y':
            "\tAs you wish. Going to use special mode but take care with the results!"
        else:
            print "\tMaybe a good choice to stop here :-)"
            print "\tGoing to exit!"
            sys.exit(1)  
    
    SCRIPT_START_TIME = time.clock()
    all_current_nodes = []
    nodes_with_changed_props = []
    nodes_with_changed_rels = []
    unchanged_nodes = []
    changed_nodes = []
    new_nodes = []
    nodes_to_remove = []
    pseudo_changed_nodes = []
    number_new_rels, number_removed_rels, number_updated_rels, number_relations_of_new_nodes = 0, 0, 0, 0
    
    
    # initialize the the graph database
    NEO4J_VERSION = initialize_neo4j_graph_db()
    print "######### SETUP ##########"
    print "Input File:", input_ripe_dump
    print "Neo4j version:", NEO4J_VERSION
    print "##########################"
    # initialize the binary tree for the inetnums
    BTree, root_node = initialize_binary_tree()
      
    # visit all nodes in the graph that are not replaced yet and return unique_key, id and obj_hash
    #   Note: This is much faster and memory efficient compared to returning "n" (which is the whole node)    
    #print "Getting all nodes that are not replaced yet..."
    if NEO4J_VERSION == 2:
        query = neo4j.CypherQuery(GRAPH_DB, "START n=node(*) WHERE HAS(n.replaced) AND HAS(n.unique_key) AND n.replaced = {replaced_time} RETURN n.unique_key, ID(n), n.obj_hash")
    else:
        query = neo4j.CypherQuery(GRAPH_DB, "START n=node(*) WHERE HAS(n.replaced) AND HAS(n.unique_key) AND n.replaced = {replaced_time} RETURN n.unique_key, ID(n), n.obj_hash?")
    params = {"replaced_time" : SOME_FUTURE_TIME}
    all_current_nodes = query.execute(**params)

    # Store the unique key, ref_to_node and the obj_hash in a list
    all_current_nodes = [[entry[0], entry[1], entry[2]] for entry in all_current_nodes]
    number_of_current_nodes = len(all_current_nodes)
    print "\nNumber of current nodes in db:", number_of_current_nodes

    # create a dictionary which is more useful here
    mapping_node_key_to_node_reference = {}
    mapping_db_node_key_to_node_hash = {}
    for item in all_current_nodes:
        mapping_node_key_to_node_reference.update({item[0] : item[1]}) #dict contains: key=node-name : value=ref_to_node
        mapping_db_node_key_to_node_hash.update({item[0] : item[2]}) # dict contains key=node-name : value=obj_hash_of_node

    # clear this list, we don't need it anymore
    all_current_nodes[:] = []
    
    # convert the dump from LATIN-1 to UTF-8 encoding and open it
    converted_file = open_and_convert_input_file(input_ripe_dump)
    # Start parsing the current ripe dump file and return a list where each entry has two dicts:
    #           one of the object (with props and rels)
    #           and one of object_type
    list_of_dump_objs = parse_ripe_dump(converted_file)
    
    # preprocess all the objects, that is: 
    #   split each object into properties and reationships
    #   calculate the hash values of the objects
    #   Create a inetnum-tree for all inetnums
    #   Note: route objects are handled particularly
    dict_objs_from_dump, mapping_dump_obj_key_to_obj_hash = preprocess_dump_objects(list_of_dump_objs, BTree, root_node)
    list_of_dump_objs[:] = [] # clear the list, we don't need it anymore
    
    # Check which nodes are new, removed, changed and unchanged in new dump towards db
    dict_node_differences = DictDiffer(mapping_dump_obj_key_to_obj_hash, mapping_db_node_key_to_node_hash)
    
    print "\n\n###################################################"    
    ## -> create new nodes if necessary
    new_nodes = list(dict_node_differences.added())
    print "Number of new nodes in dump:", len(new_nodes)#, new_nodes
    if new_nodes:
        create_new_nodes(new_nodes, dict_objs_from_dump, mapping_node_key_to_node_reference)
        number_relations_of_new_nodes = create_relationships_of_new_nodes(new_nodes, dict_objs_from_dump, mapping_node_key_to_node_reference)
    
    print "\n\n###################################################"    
    ## --> remove nodes (=tag as replaced), set it's relationships as replaced and remove from index 
    nodes_to_remove = list(dict_node_differences.removed())
    print "Number of nodes that do not exist in dump anymore:", len(nodes_to_remove)#, nodes_to_remove 
    if nodes_to_remove:
        mark_nodes_and_rels_as_replaced(nodes_to_remove, mapping_node_key_to_node_reference)
    
    print "\n\n###################################################"
    ## --> update those properties or rels of nodes that have changed
    changed_nodes = list(dict_node_differences.changed())
    print "Number of changed nodes --> update properties / rels of those:", len(changed_nodes)#, changed_nodes
    if changed_nodes:
        # get a list of ids of changed nodes, so we can query the obj_property_hash and obj_relationship_hash of the changed nodes
        id_list_of_changed_nodes = []
        #id_list_of_changed_nodes = [entry[1] for entry in all_current_nodes if entry[0] in changed_nodes]
        id_list_of_changed_nodes = [mapping_node_key_to_node_reference.get(entry) for entry in changed_nodes]
        
        # query the database with all changed nodes as input and return their property and relationship hashes
        # NOTE: The property hash and relationship hash could also be returned at the very fist db-query
        #       However, this way is more efficient and saves memory, as we only to get the additonal hashes of those nodes, which have changed.
        if NEO4J_VERSION == 2:
            query_changed_nodes = neo4j.CypherQuery(GRAPH_DB, "START n=node({node_id_list}) RETURN n.unique_key, n.obj_properties_hash, n.obj_relationships_hash")
        else:
            query_changed_nodes = neo4j.CypherQuery(GRAPH_DB, "START n=node({node_id_list}) RETURN n.unique_key, n.obj_properties_hash?, n.obj_relationships_hash?")
        params = {"node_id_list" : id_list_of_changed_nodes}
        all_changed_nodes = query_changed_nodes.execute(**params)
        
        # create two dicts relating to the nodes in graph, that map from node name to property_hash and relationship_hash, respectively
        mapping_db_node_key_to_node_property_hash = {}
        mapping_db_node_key_to_node_relationship_hash = {}
        # create two dicts relating to the objs from dump, that map from obj name to the property_hash and relationship_hash, respectiveley
        mapping_dump_obj_key_to_node_property_hash = {}
        mapping_dump_obj_key_to_node_relationship_hash = {}
        for item in all_changed_nodes:
            mapping_db_node_key_to_node_property_hash.update({item[0]: item[1]}) # dict contains (from graph-db) key=node-name : value=property hash of node
            mapping_db_node_key_to_node_relationship_hash.update({item[0]: item[2]}) # dict contains (from graph-db) key=node-name : value=relationship hash of node
            
            mapping_dump_obj_key_to_node_property_hash.update({item[0]: dict_objs_from_dump.get(item[0])[1].get("obj_properties_hash")}) # dict contains (from ripe-dump) key=node-name : value=property hash of node
            mapping_dump_obj_key_to_node_relationship_hash.update({item[0]: dict_objs_from_dump.get(item[0])[1].get("obj_relationships_hash")}) # dict contains (from ripe-dump) key=node-name : value=relationship hash of node
            
        # initialize two objects of DictDiffer to compare property hashes and relationship hashes    
        dict_node_prop_diff = DictDiffer(mapping_dump_obj_key_to_node_property_hash, mapping_db_node_key_to_node_property_hash)
        dict_node_rel_diff = DictDiffer(mapping_dump_obj_key_to_node_relationship_hash, mapping_db_node_key_to_node_relationship_hash)
        
        print "\n\t#######################"
        ## -> get list of nodes whose properties have changed
        nodes_with_changed_props = list(dict_node_prop_diff.changed())
        print "\tNumber of nodes with changed properties:", len(nodes_with_changed_props)#, nodes_with_changed_props
        if nodes_with_changed_props:    
            if SPECIAL_MODE:   
                # using special node, which should not be used on daily basis!
                update_node_properties_special_mode(nodes_with_changed_props, dict_objs_from_dump, mapping_node_key_to_node_reference)               
            else:
                # using normal mode
                update_node_properties(nodes_with_changed_props, dict_objs_from_dump, mapping_node_key_to_node_reference)
            
        
        print "\n\t#######################"    
        ## -> get list of nodes whose relationships have changed
        nodes_with_changed_rels = list(dict_node_rel_diff.changed())
        print "\tNumber of nodes with changed relationships:", len(nodes_with_changed_rels)#, nodes_with_changed_rels
        if nodes_with_changed_rels:
            number_new_rels, number_removed_rels, number_updated_rels = update_node_relationships(nodes_with_changed_rels, dict_objs_from_dump, mapping_node_key_to_node_reference)
        
        print "\n\t#######################"   
        pseudo_changed_nodes = list(set(changed_nodes) - (set(nodes_with_changed_props) | set(nodes_with_changed_rels)))    
        print "\tNodes that did change but neither rel nor prop changed:", len(pseudo_changed_nodes)
        if pseudo_changed_nodes:
            print "-#-Pseudo Changed Nodes:", pseudo_changed_nodes
            update_obj_hash(pseudo_changed_nodes, dict_objs_from_dump, mapping_node_key_to_node_reference)

        
    
    print "\n\n###################################################"
    unchanged_nodes = list(dict_node_differences.unchanged())
    print "Number of unchanged Nodes--> everything fine, nothing to do with them:", len(unchanged_nodes)#, unchanged_nodes
        
    # create a node with statistics about the dump
    write_db_statistics(len(new_nodes), len(nodes_to_remove), len(changed_nodes) - len(pseudo_changed_nodes),
                        len(nodes_with_changed_props), len(nodes_with_changed_rels),
                        len(unchanged_nodes) + len(pseudo_changed_nodes), number_new_rels + number_relations_of_new_nodes,
                        number_removed_rels, number_updated_rels, number_of_current_nodes)
    
    # remove all temporary files
    print "\nCleaning up:"
    print "\tRemoving temp file:", LOCAL_PATH + TEMP_FILE_NAME
    try:
        os.remove(LOCAL_PATH + TEMP_FILE_NAME)
    except OSError:
        print "\tCould not remove temp file:", LOCAL_PATH + TEMP_FILE_NAME
    print "\tRemoving ripe dump:", LOCAL_PATH + input_ripe_dump
    try:
        os.remove(LOCAL_PATH + input_ripe_dump)
    except OSError:
        print "\tCould not remove temp file:", LOCAL_PATH + TEMP_FILE_NAME
    
    print "\n\n###################################################"
    print "###################################################"
    print("\nScript finished successfully.")
    
    
    
if __name__ == "__main__":
    try:
        input_file_name = sys.argv[1]
    except IndexError:
        print('Usage: %s <file_name_of_dump>' % sys.argv[0])
    else:
        main(input_file_name)

