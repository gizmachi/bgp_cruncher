#!/usr/bin/python

import sys

lines = sys.stdin.readlines()

print lines

for line in lines:
    print line[:-1]
