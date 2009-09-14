#!/usr/bin/env python
'''
 Copyright (c) 2009, Brian Savage. All rights reserved.

 Redistribution and use in source and binary forms, with or without 
 modification, are permitted provided that the following conditions 
 are met:

    * Redistributions of source code must retain the above copyright 
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above 
      copyright 
      notice, this list of conditions and the following disclaimer in 
      the documentation and/or other materials provided with the 
      distribution.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
 "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
 LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
 FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE 
 COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
 INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
 BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
 LOSS FF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
 CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT 
 LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN 
 ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
 POSSIBILITY OF SUCH DAMAGE.
'''

# Note / Word of Caution
# The values output by this script may not match the SAC PoleZero 
#   files, as the rdseed.h file in rdseed distribution uses a 
#   truncated value of PI
#     B. Savage 9/12/2009 
#
# History:
#   2009-Sep-12 Initial Version
#      Values are taken only from the RESP files created by rdseed
#      Block 48 is not used or even identified as being important
# Bugs:
#   I am certain there are bugs
#   Wow, this is ugly 

import sys
import os
from math import *

if len(sys.argv) < 2 :
    print "Usage: " + os.path.basename(sys.argv[0]) + " RESP-file"
    print "      Converts a RESP file into a SAC PoleZero file"
    print "      SAC Polezero file is built from station/net/channel"
    exit(-1)

file = sys.argv[1]

fp = open( file )

hash = { 
    "B050F03":    { "name": "station",  'id': 2 },
    "B050F16":    { "name": "network",  'id': 2 },
    "B052F04":    { "name": "channel",  'id': 2 },
    "B052F03":    { "name": "location", 'id': 2 },
    "B053F03":    { "name": "type",     "id": 4 },
    "B053F04":    { "name": "stage",    "id": 4 },
    "B053F05":    { "name": "units",    "id": 5 },
    "B053F07":    { "name": "A0",       "id": 4 },
    "B053F08":    { "name": "fn",       "id": 3 },
    "B053F14":    { "name": "npoles",   "id": 4 },
    "B053F09":    { "name": "nzeros",   "id": 4 },
    "B053F15-18": { "name": "poles",    "id": range(2,4) },
    "B053F10-13": { "name": "zeros",    "id": range(2,4) },
    "B058F03":    { "name": "stage",    "id": 4 },
    "B058F04":    { "name": "sd",       "id": 2 },
    "B058F05":    { "name": "fs",       "id": 4 },
    
    }


stages = list()
data = dict()

block = ""

#
# Parsing
#
for line in fp :
    line = line.replace("\n", "")
    v = line.split()
    key = v[0]
    c = key[0] 
    if c == "#":
        continue
    cur = key[0:4]
    if cur != block:
        if 'block' in data :
            if (data['block'] != "B058") or (data['block'] == "B058" and data['stage'] == 0) :
                stages.append(data.copy())
                data.clear()

    block = cur
    if key in hash :
        data['block'] = block
#        print line
        name = hash[key]['name']
        id   = hash[key]['id']

        if name == "npoles" or name == "nzeros" :
            data[name] = int(v[id])
        elif name == "poles" or name == "zeros" :
            if not name in data:
                data[name] = list()
            for i in id :
                data[name].append( float(v[ i ]))
        elif name == "A0" :
            data[name] = float(v[id])
        elif name == "sd" or name == "fs" :
            if data['stage'] == 0 :
                data[name] = float(v[id])
        elif name == "stage" :
            data[name] = int(v[id])
        elif name == "fn" :
            if data['stage'] == 1 :
                data[name] = float(v[id])
        elif name == "units" :
            if data['stage'] == 1 :
                data[name] = v[id]
        else :
            data[ name ] = v[ id ]

fp.close()

if (data['block'] != "B058") or (data['block'] == "B058" and data['stage'] == 0) :
    stages.append(data)

#
# Computation
#
A0     = 1
npoles = 0
nzeros = 0
gamma  = 0
poles  = list()
zeros  = list()
for s in stages:
    # Convert units to Displacement by adding additional Zeros
    if 'units' in s:
        if s['units'] == "M/S":      gamma = 1
        if s['units'] == "M/S**2":   gamma = 2
     # Compute the Product of all A0 values (converting to correct units)
    if 'A0' in s :
        A0 = A0 * s['A0']
        if s['type'] == "B" :
            A0 = A0 * (2 * pi)**( s['npoles'] - s['nzeros'] )

    # Compute additional normalization factor         
    if 'fn' in s :
        fn = s['fn']
        A0d = (2 * pi * fn)**gamma
    if 'sd' in s :            sd = s['sd'] * (2 * pi * s['fs'])**gamma
        
    # Save Needed Values
    if 'fs' in s :            fs = s['fs']
    if 'station' in s:        station = s['station']
    if 'network' in s:        network = s['network']
    if 'channel' in s:        channel = s['channel']
    if 'location' in s:
        location = s['location']
        if location == "??":
            location = ""

    # Determine how many total poles and zeros exist
    if 'nzeros' in s :        nzeros = nzeros + s['nzeros']
    if 'npoles' in s :        npoles = npoles + s['npoles']
    
    # Save all poles and zeros (converting to correct units)
    if 'poles' in s:
        for i in range(s['npoles'] * 2) :
            if s['type'] == "B" :
                s['poles'][i] = s['poles'][i] * 2 * pi
            poles.append(s['poles'][i])
    if 'zeros' in s:
        for i in range(s['nzeros'] * 2) :
            if s['type'] == "B" :
                s['zeros'][i] = s['zeros'][i] * 2 * pi
            zeros.append(s['zeros'][i])

# Find the final normialization constant
A0 = A0 / A0d


# Add in the additional zeros, converting the output to displacement in meters
for i in range(gamma):
    zeros.append(0.0)
    zeros.append(0.0)
nzeros = nzeros + gamma

# Save Poles and Zeros in a list of Complex Numbers
P = list()
for i in range(0, npoles*2, 2) :
    P.append( complex(poles[i], poles[i+1]) )
Z = list()
for i in range(0, nzeros*2, 2) :
    Z.append( complex(zeros[i], zeros[i+1]) )

# If there are no poles or zeros, set the calculated A0 to defined A0
if npoles == 0 or nzeros == 0:
    calc_A0 = A0
else : # Compute A0 from the poles and Zeros
    f0 = complex(0.0, 2.0 * pi * fs)
    denom = f0 - Z[0]
    for i in range(1,len(Z)):    denom = denom * ( f0 - Z[i] )
    numer = f0 - P[0]
    for i in range(1,len(P)):    numer = numer * ( f0 - P[i])
    calc_A0 = abs( numer / denom )


# Handle cases where frequencies do not match
if abs(fs - fn) > 1e-4 :
    print "Warning: [",station,network,channel,"]",
    print "Sensitivity and Normalization Frequencies not equal"
    print "      Will Calcuate Normalization Constant (rdseed/evalresp default)"
    print "      Sensitivity Frequency   ", fs
    print "      Normalization Frequency ", fn
    A0 = calc_A0

# Handle cases where the A0 values do not match
if abs(A0 - calc_A0)/calc_A0 > 0.005 :
    print "Warning: [",station,network,channel,"]",
    print "Calculated and Defined A0 do not match"
    print "      Defined   ", A0, "  from collected RESP file values"
    print "      Calculated", calc_A0, "  from poles and zeros"
    print "      Using Calculated Normalization Constant (rdseed/evalresp default)"
    A0 = calc_A0


# Create a file name out save the polezero file
out = "SAC_PZs_" + network + "_" + station + "_" + channel + "_" + location + "_from_" + file
fp = open(out, 'w')

print >> fp, "ZEROS",nzeros
for i in range(0,nzeros*2,2) :
    if zeros[i] != 0.0 or zeros[i+1] != 0.0:
        print >> fp, "%.4f  %.4f" % ( zeros[i], zeros[i+1] )

print >> fp, "POLES",npoles
for i in range(0,npoles*2,2) :
    print >> fp, "%.4f  %.4f" % ( poles[i], poles[i+1] )

print >>fp, "CONSTANT %.6e" % ( A0 * sd )

fp.close()

#print "CONSTANT %.6E" % ( calc_A0 * sd )
#print "CONSTANT %.6E" % ( orig_A0 * sd )

