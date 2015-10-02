#!/usr/bin/python

import struct
import hashlib

class asnode:

    id_hash = None
    property_dict = None
    node_type = None

    def __init__(self, nr):
        self.node_type = 'as_number'
        self.property_dict = {}
        self.property_dict['as_number'] = nr
        self.id_hash = hashlib.sha1(self.toStr()).hexdigest()


    def getProperties(self):
        params = {
            'node_type':self.node_type,
            'node_id':self.id_hash,
            'node_hash':self.id_hash,   # Replace if properties are modified
            }
        params.update(self.property_dict)
        return params




    def toStr(self):
        string = "as: " + str(self.property_dict['as_number'])
        return string        

