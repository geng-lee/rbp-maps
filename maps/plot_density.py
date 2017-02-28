#!/usr/local/bin/python2.7
# encoding: utf-8
'''
density.plot_all_tss -- shortdesc

density.plot_all_tss is a description

It defines classes_and_methods

@author:     brian

@copyright:  2016 organization_name. All rights reserved.

@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

import collections
import logging
import os
import subprocess
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

import density.ReadDensity
import density.normalization_functions as norm
from density import Map
from plot import Plot

logger = logging.getLogger('plot_features')

__all__ = []
__version__ = 0.1
__date__ = '2016-05-06'
__updated__ = '2016-05-06'

DEBUG = 1
TESTRUN = 0
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


def main(argv=None):  # IGNORE:C0111

    # Setup argument parser
    # USAGE: 
    # python plot_features_from_xintao_using_erics_manifest.py -o /projects/ps-yeolab3/bay001/maps/se/xintao/8-15-2016 -f -m /home/elvannostrand/data/clip/CLIPseq_analysis/ENCODEclip_20160718/ALLDATASETS_submittedonly.txt -e se -r /projects/ps-yeolab3/bay001/maps/alt_splicing/8-5-2016/xintao-as-miso -s
    # manifest file is taken from here: /home/gpratt/Dropbox/encode_integration/20160408_ENCODE_MASTER_ID_LIST_AllDatasets.csv
    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter)

    parser.add_argument(
        "-ip",
        "--ip-bam",
        dest="ipbam",
        required=True
    )
    parser.add_argument(
        "-input",
        "--input-bam",
        dest="inpbam",
        required=True
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        required=True
    )
    parser.add_argument(
        "-e",
        "--event",
        dest="event",
        help="event. Can be either: se, unscaledbed, bed",
        required=True
    )
    parser.add_argument(
        "-c",
        "--conditions",
        dest="annotations",
        help="annotation files",
        nargs='+',
        required=True
    )
    parser.add_argument(
        "-at",
        "--annotation_type",
        dest="annotation_type",
        help="annotation type (miso, xintao, [bed])",
        nargs='+',
        required=True
    )
    parser.add_argument(
        "-exon",
        "--exon_offset",
        dest="exon_offset",
        help="exon offset (default: 50)",
        default=50,
        type=int
    )
    parser.add_argument(
        "-intron",
        "--intron_offset",
        dest="intron_offset",
        help="intron offset (default: 300)",
        default=300,
        type=int
    )
    parser.add_argument(
        "-conf",
        "--confidence",
        dest="confidence",
        help="Keep only this percentage of events while removing others " \
             "as outliers (default 0.95)",
        default=0.95,
        type=float)
    parser.add_argument(
        "-norm",
        "--norm_level",
        dest="normalization_level",
        help="normalization_level 0: raw IP, [1]: subtraction, 2: entropy, " \
             "3: raw input", default=1, type=int
    )
    parser.add_argument(
        "-s",
        "--scale",
        dest="scale",
        help="if the features are of different lengths, scale them to 100",
        default=False,
        action='store_true'
    )
    parser.add_argument(
        "-f",
        "--flip",
        dest="flip",
        help="legacy option for *.neg -> *.pos bw",
        default=False,
        action='store_true'
    )

    # Toplevel directory:
    topdir = os.path.dirname(os.path.realpath(__file__))
    external_script_dir = os.path.join(topdir, 'external_scripts/')
    make_bigwigs_script = os.path.join(external_script_dir, 'make_bigwig_files.py')
    chrom_sizes = os.path.join(external_script_dir, 'hg19.chrom.sizes')
    # sys.path.append(external_script_dir)
    os.environ["PATH"] += os.pathsep + external_script_dir
    # Process arguments
    args = parser.parse_args()
    outfile = args.output
    event = args.event.lower()


    # Process outlier removal
    confidence = args.confidence

    # Process testing and some other stuff

    annotations = args.annotations
    annotation_type = args.annotation_type

    # Process mapping options
    exon_offset = args.exon_offset
    intron_offset = args.intron_offset

    # Process normalization options
    norm_level = args.normalization_level

    # process ip args
    ip_bam = args.ipbam
    input_bam = args.inpbam


    """ be aware this is flipped by default """
    ip_pos_bw = ip_bam.replace('.bam', '.norm.neg.bw')
    ip_neg_bw = ip_bam.replace('.bam', '.norm.pos.bw')

    input_pos_bw = input_bam.replace('.bam', '.norm.neg.bw')
    input_neg_bw = input_bam.replace('.bam', '.norm.pos.bw')

    # process scaling
    scale = args.scale

    # process flip
    is_flipped = args.flip

    """
    Check if bigwigs exist, otherwise make
    """
    call_bigwig_script = False
    required_input_files = [ip_bam, ip_pos_bw, ip_neg_bw,
                            input_bam, input_pos_bw, input_neg_bw]
    for i in required_input_files:
        if not os.path.isfile(i):
            print("Warning: {} does not exist".format(i))
            logger.error("Warning: {} does not exist".format(i))
            call_bigwig_script = True
    if call_bigwig_script:

        cmd = 'python {} --bam {} --genome {} --bw_pos {} --bw_neg {} --dont_flip'.format(
            make_bigwigs_script,
            ip_bam,
            chrom_sizes,
            ip_pos_bw, ip_neg_bw
        )
        subprocess.call(cmd, shell=True)
        cmd = 'python {} --bam {} --genome {} --bw_pos {} --bw_neg {} --dont_flip'.format(
            make_bigwigs_script,
            input_bam,
            chrom_sizes,
            input_pos_bw,
            input_neg_bw
        )
        subprocess.call(cmd, shell=True)
    else:
        print("all files found, skipping norm.bw creation.")
    """
    Create ReadDensity objects. Note! This will effectively "flip back" bws
    """
    if not is_flipped:
        rbp = density.ReadDensity.ReadDensity(
            pos=ip_pos_bw, neg=ip_neg_bw, bam=ip_bam
        )
        inp = density.ReadDensity.ReadDensity(
            pos=input_pos_bw, neg=input_neg_bw, bam=input_bam
        )
    else:
        rbp = density.ReadDensity.ReadDensity(
            pos=ip_neg_bw, neg=ip_pos_bw, bam=ip_bam
        )
        inp = density.ReadDensity.ReadDensity(
            pos=input_neg_bw, neg=input_pos_bw, bam=input_bam
        )
    """
    Create annotations - turn annotation, type into annotation:type dicts
    """
    annotation_files = {}

    if len(annotations) != len(annotation_type):
        print(
        "We have a different number of annotation types than annotations.")
        exit(1)
    else:
        for i in range(0, len(annotations)):
            annotation_files[annotations[i]] = annotation_type[i]

    """
    Create objects
    """
    if event == 'se':
        se = Map.SkippedExon(rbp, inp, outfile,
                             norm.normalize_and_per_region_subtract,
                             annotation_files, exon_offset=50,
                             intron_offset=300, min_density_threshold=0,
                             conf=0.95)
        print('se')
        se.create_matrices()
        print('create')
        se.normalize_matrix()
        print('norm')
        se.set_means_and_sems()
        print('meansandsems')
        se.write_intermediates_to_csv()
        se.plot()
if __name__ == "__main__":
    main()