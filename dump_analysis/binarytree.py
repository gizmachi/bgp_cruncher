class TreeNode:
    '''
    Stores the tree "nodes" (of the CBinTree) that are created in memory
    '''
    left, right, data, level = None, None, 0, 0
    
    def __init__(self, data, level):
        self.left = None    # left stands for 0
        self.right = None   # right stands for 1
        
        # create an empty dummy node with the binary IP up to the current level
        self.data = [data[0][0:level], level, [], False, None]

    def mark_as_leaf(self, data):
        # mark an existing node as leaf
        
        #if not data[2]:
        #    print "There is no data!", data
        #    print "Self?!:", self
         
        self.data[3] = True # set leaf as true
        self.data[2].extend(data[2]) # store the (additional) inetnum in the node   
        
        #if not self.data[2]:
        #    print "Self data is still empty after extending...:", self.data   
        # self.data[2] = data[2] 
        return self

################################################################################

class BinTree:
    '''
    The binary inetnum tree that is build up in memory.
    Is used to transfer the inetnum-tree to the neo4j graph
    '''
    global number_of_leafs

    def __init__(self):
        # initializes the root member
        self.root = None
    
    def addNode(self, data, level):
        # creates a new node and returns it
        return TreeNode(data, level)
        
    def markLeaf(self, root, data):
        # marks a node as leaf and appends the inetnum
        return root.mark_as_leaf(data)

    def insert(self, root, data, level=0):
        # insert a node to the tree          
        # as long as the the last level isn't reached, go down the tree and create empty nodes if necessary    
        if level < data[1]:
            if root == None:
                # if there is no node yet, add an emtpy one
                # and continue going down the tree
                root = self.addNode(data, level)                          
            if data[0][level] == str(0):
                # if there is a zero '0', go into the left sub-tree
                root.left = self.insert(root.left, data, level+1)                           
            else:
                # otherwise there is a '1', so go into the right sub-tree
                root.right = self.insert(root.right, data, level+1)
            return root
            
        else:
            # The final level was reached           
            if root == None:
                # Create a new node (there was no node before) and mark it as leaf
                new_node = self.addNode(data, level)
                leaf_node = self.markLeaf(new_node, data)
                return leaf_node                           
            else:
                # Otherwise mark the current node as leaf but keep it's relations (children)
                # Note: This node might already be a leaf, so update the properties
                leaf_node = self.markLeaf(root, data)
                return leaf_node

                            
    def printTree(self, root):
        # prints the tree path
        if root == None:
            pass
        else:
            self.printTree(root.left)
            print root.data
            self.printTree(root.right)
   

    def find_inetnum_leaf(self, root, data, level=0, last_seen_leaf=None):
        while level < data[1]:
            #print "LEVEL:", level, data
            if root == None:
                # The end of the tree has been reached, return the last seen leaf
                return last_seen_leaf.data[2]
            else:
                # The tree is not finished, so go further down
                if root.data[3]: # the current node is a leaf
                    last_seen_leaf = root
                if data[0][level] == str(0):
                    # go to the left
                    root = root.left
                else:
                    # go to the right
                    root = root.right
            level +=1
            
        # The while loop finished, so we reached the final level of the subnet
        # check if this node is a leaf, otherwise return the last seen leaf
        if root:
            if root.data[3]:
                last_seen_leaf = root            
        return last_seen_leaf.data[2]
                       

