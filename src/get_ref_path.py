from os.path import dirname, join
import pandas as pd


def parse_analysis_files(analysis_files):
    '''
    :parse fasta name from 'analysis_files.txt' generated by GP
    '''
    df = pd.read_csv(analysis_files, sep='\t', header=0)
    return df[['SAMPLE_ALIAS', 'REFERENCE_SEQUENCE']]

bam_list = '/cil/shed/sandboxes/xiaoli/fungal-pipeline/analysis/crypto/batch1_162_samples_bamlist.tsv'
ref_list = '/gsap/garage-fungal/Crypto_neoformans_seroD_B454/analysis/JEC21_NCBI/batch1_162_samples_refs.txt'

df = pd.DataFrame(columns=['SAMPLE_ALIAS', 'REFERENCE_SEQUENCE'])
with open(bam_list, 'r') as bams:
    for path in bams:
        fdir = dirname(path.split('\t')[1])
        ref_seq = parse_analysis_files(join(fdir, 'analysis_files.txt'))
        df = pd.concat([df, ref_seq])
df.drop_duplicates().to_csv(ref_list, sep='\t', index=False)
