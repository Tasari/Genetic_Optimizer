from math import exp, fsum, log
from .tools import get_most_frequent_codons, rewrite_sequence_to_codons, reformat_table_codon_freq_aa

def geomean(xs):
    return exp(fsum(log(x) for x in xs) / len(xs))

def calculate_CAI(data, formatted_codon_bias_table, alldata=1):
    if alldata:
        sequence = data.all_data().replace("T", 'U').replace('\n', '')
    else:
        sequence=data
    to_count=[]
    codon_freq_aa = reformat_table_codon_freq_aa(formatted_codon_bias_table)
    forbidden = ['UGG', 'AUG', 'UAA', 'UGA', 'UAG']
    most_frequent_codons = get_most_frequent_codons(formatted_codon_bias_table)
    for codon in rewrite_sequence_to_codons(sequence):
        if codon in forbidden:
            continue
        to_count.append(codon_freq_aa[codon][0]/most_frequent_codons[codon_freq_aa[codon][1]].frequencyper1000)
    result = round(geomean(to_count), 3)
    if alldata:
        data.set_CAI(result)
    return result 
    '''
    for codon in formatted_codon_bias_table:
        if codon.bases not in dicto_testo.keys():
            dicto_testo[codon.bases] = codon
    for codon in rewrite_sequence_to_codons(sequence):
        if codon in forbidden:
            continue
        if dicto_testo[codon].amount != 0:
            w = dicto_testo[codon].amount/most_frequent_codons[dicto_testo[codon].aminoacid].amount
        else:
            w = 0.5/most_frequent_codons[dicto_testo[codon].aminoacid].amount
        to_count.append(w)
'''