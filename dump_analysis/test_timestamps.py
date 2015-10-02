#!/usr/bin/python

from parser import Parser


print "sample.update.bz2:"
p = Parser('sample.update.bz2')
count = 0
for a in p:
   if count == 0:
      print "...first timestamp: " + str(a[-1][-1][-1])
   count += 1
print "...entries: " + str(count)
print "...last timestamp: " + str(a[-1][-1][-1])


print "\nsample.dump.bz2:"
p = Parser('sample.dump.bz2')
count = 0
for a in p:
   if count == 0:
      print "...first timestamp: " + str(a[-1][-1][-1])
   count += 1
print "...entries: " + str(count)
print "...last timestamp: " + str(a[-1][-1][-1])
