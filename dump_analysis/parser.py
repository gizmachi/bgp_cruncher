import socket
import struct
from parser_head import *

# Convert ip from int representation to string
def int2ip(addr):                                                               
        return socket.inet_ntoa(struct.pack("<I", addr))

# Convert entry to string
def entryToStr(entry):
    ret = ""
    # entry[0] is always the type 
    # Parser.typeDump 
    if entry[0] == Parser.typeDump:
        # Prefix
        pre = int2ip(entry[1])
        # Prefix length
        l = entry[2]
        # And the entries for that prefix
        for item in entry[3]:
            # TABLEDUMPV2|PREFIX/LEN|PEER_IP|PEER_AS|AS_PATH|NEXT_HOP
            ret += "TABLEDUMPV2|"+str(pre)+"/"+str(l)+"|"+str(int2ip(item[0]))+"|"+str(item[1])+"|"+str(item[3])+"|"+str(item[4])+"\n"
    # Parser.typeUpdate
    elif entry[0] == Parser.typeUpdate:
        # Source IP
        sip = entry[1]
        # Source AS
        sas = entry[2]
        # And the announced/withdrawn prefix
        for item in entry[3]:
            # Parser.typeAnnounce
            if item[0] == Parser.typeAnnounce:
                # BGP4MP|SRC_IP|SRC_AS|A|PREFIX/LEN|AS_PATH|NEXT_HOP
                ret += "BGP4MP|"+str(sip)+"|"+sas+"|A|"+str(int2ip(item[1]))+"/"+str(item[2])+"|"+str(item[3])+"|"+str(item[4])+"\n"
            elif item[0] == Parser.typeWithdraw:
                # BGP4MP|SRC_IP|SRC_AS|W|PREFIX/LEN
                ret += "BGP4MP|"+str(sip)+"|"+sas+"|W|"+str(int2ip(item[1]))+"/"+str(item[2])+"\n"

    return ret[:-2]

# Get a string representation from an as path
def attr_aspath(a):
    if a.contents.flag & ATTR_FLAG_BIT(BGP_ATTR_AS_PATH) and a.contents.aspath and a.contents.aspath.contents.str:
        return str(a.contents.aspath.contents.str)
    else:
        return ""

# Parser..
class Parser:

    # Types of the entries
    typeDump = 'D'
    typeUpdate = 'U'
    typeAnnounce = 'A'
    typeWithdraw = 'W'

    def __init__(self, filename):
        # open dump
        self.my_dump = bgpdump_open_dump(c_char_p(filename))

    def next(self):
        while True:
            ret = ()
            # Read next entry
            my_entry = bgpdump_read_next(self.my_dump)
            # Is it valid?
            if not my_entry:
                # Is there data left?
                if self.my_dump.contents.eof != 0:
                    bgpdump_close_dump(self.my_dump)
                    raise StopIteration
                continue
            # Switch type
            t = my_entry.contents.type
            # ========================================
            #           TABLE_DUMP_V2
            # ========================================
            if t == BGPDUMP_TYPE_TABLE_DUMP_V2:
                # Switch subtype
                st = my_entry.contents.subtype
                # IPV4_UNICAST
                if st == BGPDUMP_SUBTYPE_TABLE_DUMP_V2_RIB_IPV4_UNICAST:
                    # Create new tuple for the prefix (Prefix, Prefix length)
                    ret = createDump(my_entry.contents.body.mrtd_table_dump_v2_prefix.prefix.v4_addr.s_addr,
                            my_entry.contents.body.mrtd_table_dump_v2_prefix.prefix_length)
                    # And add the entries
                    for i in range(0, my_entry.contents.body.mrtd_table_dump_v2_prefix.entry_count):
                        # Attributes
                        a = my_entry.contents.body.mrtd_table_dump_v2_prefix.entries[i].attr.contents
                        # Prefix
                        p = my_entry.contents.body.mrtd_table_dump_v2_prefix.entries[i].peer.contents
                        # Timestamp
                        # NOTE: we need the originated_time timestamp, otherwise we would get the imprecise dump time
                        timestamp = my_entry.contents.body.mrtd_table_dump_v2_prefix.entries[i].originated_time
                        # Append new entry for the prefix (i.e. a peer that announced the prefix)
                        ret[3].append(createDumpEntry(p.peer_ip.v4_addr.s_addr, # Peer IP
                        		p.peer_as, # Peer AS
                        		p.peer_bgp_id.s_addr, # Peer BGP Id
                        		str(a.aspath.contents.str), # AS path
                        		a.origin, # Origin
                        		a.nexthop.s_addr, # Next hop
                        		timestamp)) # Timestamp
                # Unknown subtype
                else:
                    continue

            # ========================================
            #           BGP4MP
            # ========================================
            elif t == BGPDUMP_TYPE_ZEBRA_BGP:
                # Subtype
                if my_entry.contents.subtype == BGPDUMP_SUBTYPE_ZEBRA_BGP_MESSAGE_AS4 or my_entry.contents.subtype == BGPDUMP_SUBTYPE_ZEBRA_BGP_MESSAGE:
                    # We need more subtypes
                    if my_entry.contents.body.zebra_message.type == BGP_MSG_UPDATE:
                        entry = my_entry
                        # src ip
                        ip = str(int2ip(entry.contents.body.zebra_message.source_ip.v4_addr.s_addr)) 
                        # src as
                        ass = str(entry.contents.body.zebra_message.source_as)
                        # New return tuple
                        ret = createUpdate(ip, ass)
                        # Add the messages of the peer (withdraw or announce)
                        # Withdraw message
                        # Timestamp
                        # NOTE: the contents.time timestamp is correct here (change time == dump time for BGP messages)
                        # entry.contents.body.zebra_entry.time_last_change
                        timestamp = my_entry.contents.time
                        if entry.contents.body.zebra_message.withdraw_count != 0 or entry.contents.attr.contents.flag & ATTR_FLAG_BIT(BGP_ATTR_MP_UNREACH_NLRI):
                            # Withdrawn prefixes
                            addWithdrawPrefix(ret, entry.contents.body.zebra_message.withdraw, entry.contents.body.zebra_message.withdraw_count, timestamp)
                            # More prefixes
                            if entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST] and entryattr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST].contents.prefix_count:
                                addWithdrawPrefix(ret, entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST].contents.nlri, entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST].contents.prefix_count,timestamp)
                            if entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_MULTICAST] and entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_MULTICAST].contents.prefix_count:
                                addWithdrawPrefix(ret, entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_MULTICAST].contents.nlri,entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_MULTICAST].contents.prefix_count,timestamp)
                            if entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST_MULTICAST] and entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST_MULTICAST].contents.prefix_count:
                                addWithdrawPrefix(ret, entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST_MULTICAST].contents.nlri,entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST_MULTICAST].contents.prefix_count,timestamp)

                        # Announce
                        if entry.contents.body.zebra_message.announce_count != 0 or entry.contents.attr.contents.flag & ATTR_FLAG_BIT(BGP_ATTR_MP_REACH_NLRI):
                            # Announced prefixes
                            addAnnouncePrefix(ret, entry.contents.body.zebra_message.announce, entry.contents.body.zebra_message.announce_count, entry, timestamp)
                            # Some more
                            if entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST] and entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST].contents.prefix_count:
                                addAnnouncePrefix(ret, entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST],entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST].contents.prefix_count,entry,timestamp)
                            if entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_MULTICAST] and entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_MULTICAST].contents.prefix_count:
                                addAnnouncePrefix(ret, entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_MULTICAST],entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_MULTICAST].contents.prefix_count,entry,timestamp)
                            if entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST_MULTICAST] and entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST_MULTICAST].contents.prefix_count:
                                addAnnouncePrefix(entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST_MULTICAST],entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST_MULTICAST].contents.prefix_count,entry,timestamp)

                    else:
                        print "Message: ",my_entry.contents.body.zebra_message.type 
                        continue
                else: # Ignore the rest
                    print "Subtype:",my_entry.contents.subtype
                    continue
            # ========================================
            #           What?
            # ========================================
            else:
                print t

            # Free memory :)
            bgpdump_free_mem(my_entry)

            return ret

    def __iter__(self):
        return self


# Dump has format:
# ret = [
#           type,               -   0
#           prefix,             -   1
#           prefix length,      -   2
#           [                   -   3
#               peer ip             -   0
#               peer as             -   1
#               peer bgp id         -   2
#               as path             -   3
#               origin              -   4
#               next hop ip         -   5

# Update has format:
# ret = [
#           type,               -   0
#           source ip,          -   1
#           source as,          -   2
#           [                   -   3
#               prefix                  -   0
#               prefix length           -   1
#               as path(only announce)  -   2
#               next hop(only announce) -   3


# Some helper functions
def createDumpEntry(peer_ip, peer_as, peer_id, as_path, origin, next_hop, ts):
    return (peer_ip, peer_as, peer_id, as_path, origin, next_hop, ts)

def createDump(prefix, prefix_length):
    return (Parser.typeDump, prefix, prefix_length, [])

def createAnnounce(prefix, prefix_length, as_path, next_hop, ts):
    return (Parser.typeAnnounce, prefix, prefix_length, as_path, next_hop, ts)

def createWithdraw(prefix, prefix_len, ts):
    return (Parser.typeWithdraw, prefix, prefix_len, ts)

def createUpdate(peer_ip, peer_as):
    return (Parser.typeUpdate, peer_ip, peer_as, [])

def addWithdrawPrefix(ret, prefix, count, ts):
    for idx in range(0,count):
        ret[3].append(createWithdraw(prefix[idx].address.v4_addr.s_addr, prefix[idx].len, ts))

def addAnnouncePrefix(ret, prefix, count, entry, ts):
    for idx in range(0,count):
        ret[3].append(createAnnounce(prefix[idx].address.v4_addr.s_addr, prefix[idx].len, str(attr_aspath(entry.contents.attr)), entry.contents.attr.contents.nexthop.s_addr, ts))

