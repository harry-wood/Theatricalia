#!/usr/bin/python

from sounds.metaphone import dm, soundex
from sounds.jarowpy import jarow
from sounds.levenshtein import damerau, qnum

def compare(s1f, s1l, s2f, s2l):
	s1f = unicode(s1f.lower())
	s1l = unicode(s1l.lower())
	s2f = unicode(s2f.lower())
	s2l = unicode(s2l.lower())
	s1 = "%s %s" % (s1f, s1l)
	s2 = "%s %s" % (s2f, s2l)
	soundex1 = soundex(s1)
	soundex2 = soundex(s2)
	soundex1f = soundex(s1f)
	soundex2f = soundex(s2f)
	soundex1l = soundex(s1l)
	soundex2l = soundex(s2l)
	soundexMatch = (soundex1 == soundex2)
	soundexFMatch = (soundex1f == soundex2f)
	soundexLMatch = (soundex1l == soundex2l)
	dm1 = dm(s1)
	dm2 = dm(s2)
	dm1f = dm(s1f)
	dm2f = dm(s2f)
	dm1l = dm(s1l)
	dm2l = dm(s2l)
	dmMatch = (dm1 == dm2 or dm1[0] == dm2[0] or dm1[0] == dm2[1] or dm1[1] == dm2[0])
	dmFMatch = (dm1f == dm2f or dm1[0] == dm2[0] or dm1[0] == dm2[1] or dm1[1] == dm2[0])
	dmLMatch = (dm1l == dm2l or dm1[0] == dm2[0] or dm1[0] == dm2[1] or dm1[1] == dm2[0])
	jarowN = jarow(s1, s2)
	jarowNf = jarow(s1f, s2f)
	jarowNl = jarow(s1l, s2l)
	damerauN = damerau(s1, s2)
	damerauNf = damerau(s1f, s2f)
	damerauNl = damerau(s1l, s2l)
	qnumN = qnum(s1, s2)
	qnumNf = qnum(s1f, s2f)
	qnumNl = qnum(s1l, s2l)
	print "\n%s entered, %s wanted" % (s2, s1)
	#print "Soundex\t\tFull:%s/%s %s\tFirst:%s/%s %s\tLast:%s/%s %s" % (soundex1, soundex2, soundexMatch, soundex1f, soundex2f, soundexFMatch, soundex1l, soundex2l, soundexLMatch)
	print "Metaphone\tFull:%s/%s %s\tFirst:%s/%s %s\tLast:%s/%s %s" % (dm1, dm2, dmMatch, dm1f, dm2f, dmFMatch, dm1l, dm2l, dmLMatch)
	print "Algorithm\tFull name\tFirst name\tLast name"
	print "Jarow\t\t%.4f\t\t%.4f\t\t%.4f\nDamerau\t\t%.4f\t\t%.4f\t\t%.4f" % (jarowN, jarowNf, jarowNl, damerauN, damerauNf, damerauNl)
	#print "Qnum\t\t%.4f\t\t%.4f\t\t%.4f" % (qnumN, qnumNf, qnumNl)

def test():
    compare('Robert', 'Goodwill', 'Bob', 'Goodwell')
    compare('Antony', 'Sher', 'Anthony', 'Share')
    compare('Chuk', 'Iwuji', 'Chuck', 'Iwugee')
    compare('David', 'Tennant', 'Dave', 'Tennant')
    compare('Matthew', 'Somerville', 'Matthew', 'Summerville')
    compare('Lex', 'Shrapnel', 'Alex', 'Shrapnel')
    compare('John', 'Abbott', 'Jon', 'Abbot')
    compare('Ben', 'Addis', 'Benjamin', 'Addis')
    compare('Debbi', 'Kerr', 'Deborah', 'Kerr')
    compare('Katy', 'Stephens', 'Katie', 'Stephen')
    compare('Katy', 'Stephens', 'Kayt', 'Stephens')
    compare('Katy', 'Stephens', 'Ksty', 'Stephens')
    compare('Katy', 'Stephens', 'Akty', 'Stephens')