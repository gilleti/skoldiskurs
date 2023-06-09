from lxml import etree
import string
import argparse
import re
from pathlib import Path
import os
import subprocess
import shutil

parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter)
parser.add_argument("-start", "--start_year")
parser.add_argument("-end", "--end_year")
args = vars(parser.parse_args())


def is_stanza_file_present(path_to_file):
    if os.path.exists(path_to_file):
        return True
    else:
        return False

def mend_broken_xml(xml_file):
    f = Path(xml_file)
    f.write_text(f.read_text().replace("SALDO sense", "SALDO_sense"))

    
def read_xml(xml_file):    
    parser = etree.XMLParser(recover = True)
    tree = etree.parse(xml_file, parser = parser)
    root = tree.getroot()

    sentences = []
    tokenized_sentences = root.findall("sentence")
    if len(tokenized_sentences) > 0:
        # If data has been sentence tokenized by sparv
        for tokenized_sentence in tokenized_sentences:
            lemmas = []
            for token in tokenized_sentence.iter("token"):
                lemma = token.get("lemma")
                if lemma:
                    lemmas.append(lemma)
                else:
                    lemmas.append(token.text)
            sentences.append(lemmas)
        return (1, sentences)
    else: # If data that is not tokenized on sentence level
        lemmas = []
        for token in root.iter("token"):
            lemma = token.get("lemma")
            if lemma:
                lemmas.append(lemma)
            else:
                lemmas.append(token.text)
    return (0, lemmas) # TO DO Find better var name


def create_corpus(tokens):
    # This is Justyna's corpus
    # We only need it because we forgot to include sentence_tokenization during sparv processing
    sents = []
    my_list = []
    punct = string.punctuation
    for token in tokens:
        if token == "." or token == "!" or token == "?":
            if len(my_list) > 0:
                sents.append(my_list)
                my_list = []
            else:
                my_list = []
        elif type(token) == str:
            if token in punct:
                pass
            else:
                my_list.append(token.strip().lower())
        if type(token) != str:
            my_list.append(token.strip())
        #print(f"Number of sentences in the corpus: {len(sents)}.")
    return sents # Nested list of sentence
        

def save_corpus(corpus, outfile):
    with open(outfile, "w") as f:
        # Loop over each inner list and join the tokens back into sentences
        for sublist in corpus:
            # Clean corpus in line with Justyna's pipeline for commensurability
            corpus = ' '.join(str(v) for v in sublist)
            corpus = re.sub("[0-9]+", " ", corpus)
            corpus = re.sub("[^A-Za-zåäöÖÅÄ\s]", " ", corpus)
            
            f.write(corpus + "\n")
            # Write the sentence to the text file, followed by a new line character



corpus_dir = "/home/hilhag/prjs/sprakbanken/corpus/"
start_year = int(args["start_year"])
end_year = int(args["end_year"])
years = list(range(start_year, end_year))
for year in years:
    print(corpus_dir + str(year))
    out_dir =  corpus_dir + "tmp/" + str(start_year) + "_" + str(end_year) + "/"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if is_stanza_file_present(corpus_dir + str(year) + "/stanza_tokens.txt") == False:
        print("Processing Sparv data")
        year_dir = corpus_dir + str(year) + "/" + "export/xml_export.pretty/"
        files = os.listdir(year_dir)
        for f in files:
            input_file = year_dir + f
            if input_file.endswith("xml"):
                mend_broken_xml(input_file)
                sentence_tokenization, tokens = read_xml(input_file)
                # sentence_tokenization is a binary value indicating if sentence tokenization has already been performed by sparv
                if sentence_tokenization == 0:
                    sentences = create_corpus(tokens)
                else:
                    sentences = tokens
            outfile = out_dir + f[:-4] + ".txt"
            save_corpus(sentences, outfile)
        conc_file = str(start_year) + "_" + str(end_year) + ".txt"
        filenames = os.listdir(out_dir)
        with open(out_dir + conc_file, 'a') as outfile:
            for fname in filenames: # This is some dumb shit I have to do because of sparv failure
                with open(out_dir + fname) as infile:
                    outfile.write(infile.read())
    else:
        stanza_file = corpus_dir + str(year) + "/stanza_tokens.txt"
        conc_file = out_dir + str(start_year) + "_" + str(end_year) + ".txt" # dst file
        # copy stanza file to dst dir just for some structure
        # really quite unnecessary
        shutil.copy(stanza_file, conc_file)


concatenated_file_name = str(start_year) + "_" + str(end_year) + ".txt"
bin_file_name = str(start_year) + "_" + str(end_year) + "_lemmatized.bin"
subprocess.Popen(["./run.sh", out_dir, concatenated_file_name, bin_file_name])
