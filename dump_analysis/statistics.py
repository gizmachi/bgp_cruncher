#!/usr/bin/python
#Make statistics for analysed BGP data

class statistics:

    ipv4 = None
    ipv6 = None
    moas = None
    ASsets = None
    masks = None
    batchCount = None
    currentTime = None

    def __init__(self, time):
        self.ipv4 = 0
        self.ipv6 = 0
        self.moas = 0
        self.ASsets = 0
        self.batchCount = 0
        self.masks = []
        for i in range(33): # masks 0 to 32
            self.masks.append(0)
        if time is not None:
            self.currentTime = time

    def getTime(self):
        return currentTime

    def incBatch(self, n=1):
        self.batchCount += n

    def resetBatch(self):
        self.batchCount = 0

    def getBatchSize(self):
        return self.batchCount

    def addMoas(self, n=1):
        self.moas += n

    def addASset(self, n=1):
        self.ASsets += n

    def getMoas(self):
        return self.moas

    def getASsets(self):
        return self.ASsets

    def addIPv6(self, n=1):
        self.ipv6 += n

    def rmIPv6(self, n=1): #Count activity
        self.ipv6 += n

    def addIPv4(self, n=1):
        self.ipv4 += n

    def rmIPv4(self, n=1): #Count activity
        self.ipv4 += n

    def getIPv6(self):
        return self.ipv6

    def getIPv4(self):
        return self.ipv4

    def addMask(self, m, n=1):
        self.masks[m] += n

    def getMasks(self):
        return self.masks

    # Return ratio of IPv6 prefixes
    def ipv6ratio(self):
        if self.getIPv6() == 0: #Protects against division by 0
            return 0
        else:
            ratio = 100 * self.getIPv6() / (self.getIPv6() + self.getIPv4())
            return ratio

    def printstats(self):
        print "Statistics for BGP dump:"
        print "IPv4 updates: " + str(self.getIPv4())
        print "IPv6 updates: " + str(self.getIPv6())
        print "IPv6 constitutes " + str(self.ipv6ratio()) + "% of overall activity"
        print "MOAS found (exact prefix/mask match): " + str(self.getMoas()) + ", " + str(self.getASsets()) + " from AS-sets"
        print "Mask counts:"
        m = self.getMasks()
        for i in range(33): #Print activity for each mask
            print "/" + str(i) + ": "  + str(m[i])


