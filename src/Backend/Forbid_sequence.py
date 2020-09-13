import re
from .tools import (
    rewrite_sequence_to_aminoacids,
    find_sequence_in_gene,
    rewrite_codons_to_sequence,
    rewrite_to_rna,
)
from itertools import product
from .CAI_calculation import calculate_CAI
from ..logs import errors, failed_forbidding


def add_forbid_sequences_to_all(all_forbidden_sequences, new_forbidden):
    """Adds list of sequences given into all forbidden sequences"""
    for sequence in new_forbidden:
        if sequence != "":
            all_forbidden_sequences.append(sequence)
    return all_forbidden_sequences


def forbid_sequences(all_forbidden_sequences, input_gene, formatted_codons):
    still_found = 0
    if all_forbidden_sequences != []:
        all_forbidden_sequences = list(
            dict.fromkeys(sorted(all_forbidden_sequences, key=len))
        )
        still_found = 1
        for number, sequence in enumerate(all_forbidden_sequences):
            all_forbidden_sequences[number] = rewrite_to_rna(sequence)
    while still_found:
        done_sequences = []
        for sequence in all_forbidden_sequences:
            lenght = get_valid_sequence_lenght(
                all_forbidden_sequences[len(all_forbidden_sequences) - 1]
            )
            done_sequences.append(sequence)
            input_gene, still_found = eliminate_occurances_of_sequence(
                input_gene, done_sequences, lenght, formatted_codons
            )
    errors.append("Failed to eliminate sequeces: {}".format(failed_forbidding))
    return input_gene


def get_valid_sequence_lenght(sequence):
    lenght = len(sequence)
    if lenght % 3 != 0:
        lenght += 1
        if lenght % 3 != 0:
            lenght += 1
    return lenght


def eliminate_occurances_of_sequence(
    input_gene, done_sequences, lenght, formatted_codons
):
    sequence = done_sequences[-1]
    all_occurances_of_sequence = find_sequence_in_gene(sequence, input_gene)
    new_gene = ""
    new_gene, failed= change_sequence_to_eliminate_multiple_occurances(
        all_occurances_of_sequence,
        input_gene,
        done_sequences,
        lenght,
        formatted_codons,
    )
    if all_occurances_of_sequence != []:
        input_gene = new_gene
    if find_sequence_in_gene(sequence, input_gene) != [] and not failed:
        return input_gene, 1
    return input_gene, 0


def change_sequence_to_eliminate_multiple_occurances(
    all_occurances_of_sequence,
    input_gene,
    done_sequences,
    lenght,
    formatted_codons,
):
    """Function eliminating all the occurances of sequence.

    Function eliminates all occurances of the sequence by
    eliminating them one by one, and giving one occurance
    eliminator 2 bases before and 2 bases after the editable
    occurance, assuring new occurances won't appear. It 
    retunrs new sequence without forbidden sequences, if successful
    or adds sequence to failed if it failed to remove it. 

    Args:
        all_occurances_of_sequence: List of all occurances.
        input_gene: Gene from which we want to eliminate sequences.
        done_sequences: List of all already eliminated sequences.
        lenght: Lenght of eliminated sequence
        formatted_codons: List of formatted codons.
    """
    begin = 0
    new_sequence = ""
    failed = 0
    sequence = done_sequences[-1]
    for occurance in all_occurances_of_sequence:
        sequence_range = get_sequence_from_occurance_places(
            input_gene, occurance, lenght
        )
        if begin > sequence_range[0]:
            begin = sequence_range[0]
            new_sequence = new_sequence[:begin]
        new_sequence += input_gene[begin : sequence_range[0]]
        to_append, failed = eliminate_one_occurance(
            input_gene[sequence_range[0] : sequence_range[1]],
            done_sequences,
            formatted_codons,
            new_sequence[sequence_range[0] - 2 : sequence_range[0]],
            input_gene[sequence_range[1] : sequence_range[1] + 2],
        )
        new_sequence += to_append
        begin = sequence_range[1]
        if failed and sequence.replace("U", "T") not in failed_forbidding:
            failed_forbidding.append(sequence.replace("U", "T"))
    new_sequence += input_gene[begin:]
    return new_sequence, failed


def get_sequence_from_occurance_places(input_gene, occurance, lenght):
    """Exports occurance to get whole codons containing it.

    Function defines if occurance starts at new codon, and if not
    it goes back by 1 or 2 places, assuring the occurance is whole 
    codon, it also takes codon after since the occurance moves max
    2 bases back.

    Args:
        input_gene: Gene from which we take the sequence.
        occurance: Int symbolizing start of the found occurance
        lenght: Int symbolizing the lenght of the sequence

    Returns:
        Tuple symbolizing start and end of edited occurance
    """
    if occurance % 3 == 0:
        start = occurance
    elif occurance % 3 == 1:
        start = occurance - 1
    else:
        start = occurance - 2
    if start < 0:
        start = 0
    end = start + lenght + 3
    if end > len(input_gene):
        end = len(input_gene)
    return (start, end)


def eliminate_one_occurance(
    input_string, done_sequences, formatted_codons, pre="", post=""
):  
    """Change given sequence to get rid of done forbidden sequences.

    Funtion takes the good possibilities from 
    create_all_good_possbilities and selects the best one
    according to the CAI score.

    Args:
        input_string:String of starting sequence.
        done_sequences:List of all sequences already eliminated.
        formatted_codons: List of formatted codons.
        pre:The part of sequence before input, which is not changed.
        post:The part of the sequence after input, which is not changed.
    
    Returns:
        Best string and 0 if it was found or
        input string and 1 if it wasn't.
    """
    good_possibilities, failed = create_all_good_possibilities(
        input_string, 
        done_sequences, 
        formatted_codons, 
        pre, 
        post
    )
    if failed:
        return input_string, failed
    best = (0, "")
    for possibility in good_possibilities:
        calculated = (
            calculate_CAI(possibility, formatted_codons),
            possibility,
        )
        if calculated[0] > best[0]:
            best = calculated
    return best[1], 0

def create_all_good_possibilities(
    input_string, done_sequences, formatted_codons, pre="", post=""
):
    """Function creating possibilities to eliminate sequence.

    It creates all possible products, and selects good ones
    combinations not containing any of the forbidden ones, 
    yet still coding the same protein.

    Args:
        input_string:String of starting sequence.
        done_sequences:List of all sequences already eliminated.
        formatted_codons: List of formatted codons.
        pre:The part of sequence before input, which is not changed.
        post:The part of the sequence after input, which is not changed.
    
    Returns:
        List of good possibilities if found and 0
        if none good possibilities were found returns 
        input sequence and 1.
    """
    aminoacids = rewrite_sequence_to_aminoacids(input_string)
    possible_codons_list = get_codons_based_on_aminoacid(
        aminoacids, formatted_codons
    )
    all_possibilities = [
        rewrite_codons_to_sequence(x) for x in product(*possible_codons_list)
    ]
    good_possibilities = []
    for possibility in all_possibilities:
        if not check_if_sequences_in_forbidden(
            pre + possibility + post, done_sequences
        ):
            good_possibilities.append(possibility)
    if not len(good_possibilities):
        return input_string, 1
    return good_possibilities, 0



def get_codons_based_on_aminoacid(aminoacids, formatted_codons):
    """Returns list of codons coding aminoacids in given order.
    
    Function takes list of aminoacids in order and collects
    codons coding that aminoacids, staying in order.

    Example:
        get_codons_based_on_aminoacid("MC", formatted_codon_bias)
        gives [["AUG"]["UGC", "UGU"]], M is coded by AUG codon 
        and C is coded by both UGC and UGU.

    Arguments:
        aminoacids:
            List(or string) of aminoacids we want to get codons of.
        formatted_codons: 
            List of formatted codons.

    Returns: 
        List of two lists, each is collection of 
        codons coding given aminoacid.
    """
    sequence = []
    for aminoacid in aminoacids:
        list_of_coding_codons = []
        for codon in formatted_codons:
            if codon.aminoacid == aminoacid:
                list_of_coding_codons.append(codon.bases)
        sequence.append(list_of_coding_codons)
    return sequence


def check_if_sequences_in_forbidden(sequence, all_forbidden_sequences):
    """Checks if sequence is in forbidden sequences"""
    for forbidden in all_forbidden_sequences:
        if find_sequence_in_gene(forbidden, sequence) != []:
            return 1
    return 0
