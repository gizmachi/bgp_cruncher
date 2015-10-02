# -*- coding: utf-8 -*-
'''
BGP Tools - Parse and analyze MRT dumps
Copyright (C) 2014
Author Johann SCHLAMP <schlamp@in.tum.de>
Author Leonhard RABEL <rabel@in.tum.de>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

from libbgpdump import *
import socket


class MRTParser:
   '''
   A parser for MRT format BGP dumps (both RIB dumps and UPDATE messages).
   Use iterator to retrieve results:
      for i in parser:
         ...

   Results will be tuples in the format:
      (<timestamp>, <prefix_int>, <prefix_mask>, <str(path)>)

   Get string representation for a prefix:
      prefix = socket.inet_ntoa(struct.pack("!I", prefix_int)) + "/" + str(prefix_mask)
   '''

   def __init__(self, filename):
      self.dump = bgpdump_open_dump(c_char_p(filename))
      self.stack = list()

   def next(self):
      if len(self.stack) > 0:
         return self.stack.pop(0)

      while self.dump is not None:
         entry = bgpdump_read_next(self.dump)
         if not entry:
            if self.dump.contents.eof != 0:
               bgpdump_close_dump(self.dump)
               self.dump = None
            continue

         # RIB ENTRY
         if entry.contents.type == BGPDUMP_TYPE_TABLE_DUMP_V2:
            if entry.contents.subtype == BGPDUMP_SUBTYPE_TABLE_DUMP_V2_RIB_IPV4_UNICAST:
               prefix = socket.ntohl(int(entry.contents.body.mrtd_table_dump_v2_prefix.prefix.v4_addr.s_addr))
               mask = int(entry.contents.body.mrtd_table_dump_v2_prefix.prefix_length)
               for i in range(0, entry.contents.body.mrtd_table_dump_v2_prefix.entry_count):
                  timestamp = entry.contents.body.mrtd_table_dump_v2_prefix.entries[i].originated_time
                  attr = entry.contents.body.mrtd_table_dump_v2_prefix.entries[i].attr.contents
                  path = str(attr.aspath.contents.str)
                  self.stack.append((timestamp, prefix, mask, path))

         # UPDATE MESSAGE
         if entry.contents.type == BGPDUMP_TYPE_ZEBRA_BGP:
            if entry.contents.subtype == BGPDUMP_SUBTYPE_ZEBRA_BGP_MESSAGE_AS4 or entry.contents.subtype == BGPDUMP_SUBTYPE_ZEBRA_BGP_MESSAGE:
               if entry.contents.body.zebra_message.type == BGP_MSG_UPDATE:
                  timestamp = entry.contents.time

                  # WITHDRAW
                  if entry.contents.body.zebra_message.withdraw_count != 0 or entry.contents.attr.contents.flag & ATTR_FLAG_BIT(BGP_ATTR_MP_UNREACH_NLRI):
                     self._stack(timestamp, entry.contents.body.zebra_message.withdraw, entry.contents.body.zebra_message.withdraw_count)

                     if entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST] and entryattr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST].contents.prefix_count:
                        self._stack(timestamp, entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST].contents.nlri, entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST].contents.prefix_count)

                     if entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_MULTICAST] and entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_MULTICAST].contents.prefix_count:
                        self._stack(timestamp, entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_MULTICAST].contents.nlri, entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_MULTICAST].contents.prefix_count)

                     if entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST_MULTICAST] and entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST_MULTICAST].contents.prefix_count:
                        self._stack(timestamp, entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST_MULTICAST].contents.nlri, entry.contents.attr.contents.mp_info.contents.withdraw[AFI_IP][SAFI_UNICAST_MULTICAST].contents.prefix_count)

                  # ANNOUNCE
                  if entry.contents.body.zebra_message.announce_count != 0 or entry.contents.attr.contents.flag & ATTR_FLAG_BIT(BGP_ATTR_MP_REACH_NLRI):
                     path = str(entry.contents.attr.contents.aspath.contents.str)
                     self._stack(timestamp, entry.contents.body.zebra_message.announce, entry.contents.body.zebra_message.announce_count, path)

                     if entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST] and entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST].contents.prefix_count:
                        path = str(entry.contents.attr.contents.aspath.contents.str)
                        self._stack(timestamp, entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST].contents.nlri, entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST].contents.prefix_count, path)

                     if entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_MULTICAST] and entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_MULTICAST].contents.prefix_count:
                        path = str(entry.contents.attr.contents.aspath.contents.str)
                        self._stack(timestamp, entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_MULTICAST].contents.nlri, entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_MULTICAST].contents.prefix_count, path)

                     if entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST_MULTICAST] and entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST_MULTICAST].contents.prefix_count:
                        path = str(entry.contents.attr.contents.aspath.contents.str)
                        self._stack(timestamp, entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST_MULTICAST].contents.nlri, entry.contents.attr.contents.mp_info.contents.announce[AFI_IP][SAFI_UNICAST_MULTICAST].contents.prefix_count, path)

         bgpdump_free_mem(entry)

         if len(self.stack) > 0:
            return self.stack.pop(0)

      raise StopIteration

   def _stack(self, timestamp, prefixes, count, path=None):
      for i in range(0,count):
         self.stack.append((timestamp, socket.ntohl(int(prefixes[i].address.v4_addr.s_addr)), prefixes[i].len, path))

   def __iter__(self):
      return self


if __name__ == '__main__':
   print("For use as a module only, exiting.")
   sys.exit(0)
