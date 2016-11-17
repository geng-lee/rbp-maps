#!/usr/local/bin/python2.7
# encoding: utf-8
'''
     up_ex       ex_up     ex_dn       dn_ex
====[=----]-----[----=]===[=----]-----[----=]====

@author:     user_name

@copyright:  2015 organization_name. All rights reserved.

@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

import annotations
import sys
import os
import collections
from plot import Plot

import seaborn as sns
import pandas as pd
import datetime
import thread
import matrix_functions as mtx

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from __builtin__ import True



__all__ = []
__version__ = 0.1
__date__ = '2015-12-19'
__updated__ = '2015-12-19'

DEBUG = 0
TESTRUN = 1
PROFILE = 0

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg



def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by user_name on %s.
  Copyright 2016 organization_name. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    # Setup argument parser
    parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output", dest="output", help="output directory", required = False )
    parser.add_argument("-i", "--input", dest="input", help="input manifest containing list of bedfiles containing: chr, start, stop, -log10(pval), log2(fold), strand", required = True )
    parser.add_argument("-m", "--miso", dest="miso", help="miso annotation file", required = True )
    parser.add_argument('-V', "--version", action='version', version=program_version_message)
    parser.add_argument('-f', "--foldchange", dest="fc", help="log2 fold change cutoff (default = 0)", type=float, default=0, required = False)
    parser.add_argument('-p', "--pvalue", dest="pv", help= "-log10(p-value) cutoff (default = 5)", type=float, default=5, required = False)
    parser.add_argument('-s', "--hashval", dest="hash", help = "hash value (default = 100000)", type=int, default=100000, required = False)
    parser.add_argument('-eo', "--exonoverhang", dest="exonoverhang", help = "exon offset overhang (default = 50)", type=int, default=50, required = False)
    parser.add_argument('-io', "--intronoverhang", dest="intronoverhang", help="intron offset overhange (default = 300)", type=int, default=300, required = False)
    parser.add_argument('-t', "--eventtype", dest="event",help="event type", default="SE", required=False)
    # Process arguments
    args = parser.parse_args()
        
    miso = args.miso
    outdir = args.output
    infile = args.input
    l2fc_cutoff = args.fc
    l10p_cutoff = args.pv
    exon_overhang = args.exonoverhang
    intron_overhang = args.intronoverhang
    hashing_val = args.hash
    event_type = args.event
    
    """
    all exons for now... this may change depending on the annotation we use.
    """
    all_exons = annotations.read_four_region_miso(miso, 
                                                  hashing_val, 
                                                  event_type,
                                                  exon_overhang, 
                                                  intron_overhang) # create teh dictionary
    
    counts = {}
    with open(infile, 'r') as f:
        for line in f:
            line = line.strip()
            outfile = os.path.join(outdir, os.path.basename(line).replace('compressed.bed','compressed.txt'))
            counts['region1'] = mtx.make_hist_se(line, 
                                                 outfile, 
                                                 hashing_val, 
                                                 l10p_cutoff, 
                                                 l2fc_cutoff, 
                                                 all_exons, 
                                                 exon_overhang, 
                                                 intron_overhang)
            err = {'region1':[0]*((exon_overhang+intron_overhang+1)*4)}
            title = os.path.basename(line)
            output_file = outfile.replace('compressed.txt','compressed.png')
            Plot.plot_se(counts, counts, counts, err, err, title, output_file)
    return 0

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
        sys.argv.append("-v")
        sys.argv.append("-r")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'rbpmaps.overlap_peak_with_annot_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())