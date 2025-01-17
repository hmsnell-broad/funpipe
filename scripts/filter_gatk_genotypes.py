#!/usr/bin/env python3
""" Perform genotype filters on GATK generated VCF

Note that this is a piece of legacy code from the Broad's fungal group, and is
provided as is, without optimizing the performance, code style and
documentation etc. Only minimal changes were introduced to ensure compatibility
with the funpipe package.

"""

from __future__ import print_function
from __future__ import division

import sys
import re
import argparse
import funpipe.vcftools

parser = argparse.ArgumentParser()
parser.add_argument('infile', help='VCF filename', type=str)
parser.add_argument('--min_GQ', help='minimum GQ/RGQ to be kept', type=int)
parser.add_argument(
    '--keep_GQ_0_refs',   # (keeps ref calls w RGQ/GQ=0)
    help='keep ref calls with GQ/RGQ 0 despite min_GQ', action='store_true')
parser.add_argument(
    '--min_percent_alt_in_AD', type=float,
    help='min percent alt in AD to be kept for variants')
parser.add_argument(
    '--min_total_DP', help='min total DP to be kept', type=float)
parser.add_argument(
    '--het_binomial_p',
    help='filter hets that fail binomial test with given p-value', type=float)
parser.add_argument(
    '--keep_all_ref', help='don\'t filter reference bases',
    action='store_true')
args = parser.parse_args()

infile = args.infile
keep_all_ref = args.keep_all_ref
keep_GQ_0_refs = args.keep_GQ_0_refs
min_GQ = int(0)
min_AD = float(0)
min_tot_DP = int(0)
het_binomial_p = False

if args.min_GQ:
    min_GQ = args.min_GQ
if args.min_percent_alt_in_AD:
    min_AD = args.min_percent_alt_in_AD
if args.min_total_DP:
    min_tot_DP = args.min_total_DP
if args.het_binomial_p:
    het_binomial_p = args.het_binomial_p

comment_pattern = re.compile(r"^#")

genome_list = []

header = vcftools.VcfHeader(infile)
caller = header.get_caller()
samples = header.get_samples()

filtered_GQ = {}
for sample in samples:
    filtered_GQ[sample] = 0

filtered_AD = {}
for sample in samples:
    filtered_AD[sample] = 0

filtered_DP = {}
for sample in samples:
    filtered_DP[sample] = 0

filtered_Bi = {}
for sample in samples:
    filtered_Bi[sample] = 0

filtered = {}
for sample in samples:
    filtered[sample] = 0

with open(infile, 'r') as vcf_file:
    for vcf_line in vcf_file:
        if (re.search(comment_pattern, vcf_line)):
            print(vcf_line, end="")
        else:
            record = vcftools.VcfRecord(vcf_line)
            new_vcf_line = "\t".join([str(record.get_chrom()),
                                     str(record.get_pos()),
                                     str(record.get_id()),
                                     str(record.get_ref()),
                                     str(record.get_alt_field()),
                                     str(record.get_qual()),
                                     str(record.get_filter()),
                                     str(record.get_info()),
                                     str(record.get_format())])
            print(new_vcf_line, end="")
            for sample in samples:
                genotype_field = (record.get_genotypes_field(
                                    header.get_sample_index(sample)))
                split_genotype = genotype_field.split(':')
                gq = (record.get_GQ(split_genotype[0],
                                    index=header.get_sample_index(sample)))
                init_gt = split_genotype[0]
                if ((split_genotype[0] in ['0', '0/0', '0|0'])
                        and (keep_all_ref)):
                    (split_genotype[0], GQ_flag, AD_flag, DP_flag, Bi_flag) = (
                        record.get_genotype(
                            index=header.get_sample_index(sample),
                            return_flags=True))
                elif (split_genotype[0] in ['0', '0/0', '0|0'] and
                        gq == '0' and keep_GQ_0_refs):
                    (split_genotype[0], GQ_flag, AD_flag, DP_flag, Bi_flag) = (
                        record.get_genotype(
                            index=header.get_sample_index(sample),
                            min_tot_dp=min_tot_DP, return_flags=True))
                elif split_genotype[0] in ['0', '0/0', '0|0']:
                    (split_genotype[0], GQ_flag, AD_flag, DP_flag, Bi_flag) = (
                        record.get_genotype(
                            index=header.get_sample_index(sample),
                            min_gq=min_GQ, min_tot_dp=min_tot_DP,
                            return_flags=True))
                else:
                    (split_genotype[0], GQ_flag, AD_flag, DP_flag, Bi_flag) = (
                        record.get_genotype(
                            index=header.get_sample_index(sample),
                            min_gq=min_GQ, min_per_ad=min_AD,
                            min_tot_dp=min_tot_DP, het_binom_p=het_binomial_p,
                            return_flags=True))
                if not (init_gt in ['.', './.']):
                    if GQ_flag:
                        filtered_GQ[sample] += 1
                    if AD_flag:
                        filtered_AD[sample] += 1
                    if DP_flag:
                        filtered_DP[sample] += 1
                    if Bi_flag:
                        filtered_Bi[sample] += 1
                    if GQ_flag or AD_flag or DP_flag or Bi_flag:
                        filtered[sample] += 1
                print("\t".join(["", str(":".join(split_genotype))]), end="")
            print("")

# output summary statistics
print("Sample", file=sys.stderr, end="\t")
print("\t".join(samples), file=sys.stderr)
print("filtered_GQ", file=sys.stderr, end="")
for sample in samples:
    print("".join(["\t", str(filtered_GQ[sample])]), end="", file=sys.stderr)
print("\nfiltered_AD", file=sys.stderr, end="")
for sample in samples:
    print("".join(["\t", str(filtered_AD[sample])]), end="", file=sys.stderr)
print("\nfiltered_DP", file=sys.stderr, end="")
for sample in samples:
    print("".join(["\t", str(filtered_DP[sample])]), end="", file=sys.stderr)
print("\nfiltered_Bi", file=sys.stderr, end="")
for sample in samples:
    print("".join(["\t", str(filtered_Bi[sample])]), end="", file=sys.stderr)
print("\nfiltered_total", file=sys.stderr, end="")
for sample in samples:
    print("".join(["\t", str(filtered[sample])]), end="", file=sys.stderr)
print("", file=sys.stderr)
