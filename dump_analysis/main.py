#!/usr/bin/env python

from time import strftime
from parser import *

def main():
    p = Parser('test_up.bz2')
    print "Start:",strftime("%Y-%m-%d %H:%M:%S")

    a = 1
    b = (a,a)
    a = 2
    print b

    i = 0
    for item in p:
        if i%10000 == 0:
            pass
#            print i
        i +=1
        print entryToStr(item)

    print i,"lines"

    print "Stop:",strftime("%Y-%m-%d %H:%M:%S")

if __name__ == '__main__':
    main()

