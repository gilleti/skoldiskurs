# skoldiskurs

Here, we outline the pipeline of Ema's project, from data collection and parsing to training and using the vector representations.

Pipeline is largely as follows:

1. Download data from riksdagens open data.
2. Run sparv pipeline to tokenize and extract lemmas.
3. Parse data and transform to datafiles (using create_datafile.py and clean_corpus.py)
4. Train vectors with train_sentence.py.
5. Use vectors.

## THE DATA

The corpora we are working with is two-fold: a political corpus and a newspaper corpus. The political corpus consists of the following data sources:

1. Riksdagens anföranden.

   1.1. To download riksdagens anföranden, we have to use to scripts: data_scripts/anforanden/download_anforanden_1962-1992.sh and data_scripts/anforanden/download_anforanden_1993-2023.sh. These scripts require no input (apart from changing some hardcoded paths) and can be run as is. Execution of the scripts generate (1) a directory anforanden_1993-2023_json where source files from 1993-2023 are stored and (2) a git clone of the state riksdagen-corpus which is a curated and partially manually corrected of older anföranden, within the welfare-state-analytics project run by Måns Magnusson. The files from 1993 and forward is generally of high quality while the older anföranden have some data quality issues, partically mitigated in the riksdagen-corpus.


   1.2. To parse riksdagens anföranden, there is two scripts (due to the different sources of the data): parse_anforanden_1962-1992.py and parse_anforanden_1962-1992.py and parse_anforanden_1993-2023.py. The scripts require no user input (apart from changing some hardcoded paths) and should generate two parquet dataframes: anforanden_1993-2023.parquet and anforanden_1962-1992.parquet.

2. Riksdagens motioner.

   2.1. The pipeline for riksdagens motioner is largely the same as for anforanden. The scripts data_scripts/motioner/download_motioner_2014-2023.sh and data_scripts/motioner/download_motioner_2014-2023.sh generated two dirs of json files: motioner_1971_2013_json and motioner_2014-2023_json. Data from 1962-1970 is missing from riksdagens datasets and is therefore not included. There are some pdf:s available for download on riksdagens hemsida. That is on my to do list.

   2.2. To parse motioner, use data_scripts/motioner/parse_motioner_1971-2013.py and data_scripts/parse_motioner_2014-2023.py. These scripts generate two dataframes stored in parquet files, which is the data we will be using to create our vectors. All older files (both motioner and anföranden) result in less detailed dataframes, consisting of document id:s (of varying quality), text and dates.

## THE PRE-PROCESSING

The data is processed using the sparv pipeline. Tokenization and lemmatization is performed. Pre-processing scripts are found in the transform directory. The script transform_data.py takes as input the parquet files outputted from the download steps and outputs a concatenated parquet files called political_corpus.txt. This is actually an unnecessary step that was undertaken before I realized that the sparv pipeline demands a different data structure. Because of this, an extra step create_sparv_input.py is performed. This creates the sparv specific corpus structure of corpus/year/source as described in the sparv user manual.

The pipeline results in a number of xml under the export directory at corpus/year/export.

## THE TRAINING

The training is outlined from Justyna Sikora's pipeline for the Språkbanken news corpora vectors. However, some changes have been made. At the time of writing, there is an issue with the Sparv pipeline being too slow. There was some initial problems with the Sparv config file resulting in some data that is not interesting to us but solely slows down the process and with some invalid XML. As time is short, I have not been able to re-run this data with the right settings, therefore we need to do some post-process cleanup. I will not go in to further detail here but it can be found in the post-process scripts.

Edit: Sparv pipeline is too slow, so I had to do part of the tokenization and lemmatization using the underlying library Stanza. Therefore, things have gotten messy. Part of the output is in the form of one XML file (partly invalid XML) per infile; the other is one concatenated txt file.

1. sparv_to_vector.py is run with the arguments -start YYYY -end YYYY where YYYY is an int year such as 1975. It takes the sparv xml files, corrects and extracts lemmas where can be found, with token as a fall back. It results in a (a) temporary dir tmp where txt files are stored (Sparv output) (and later concatenated into one large txt file and (b) one large txt file (Stanza output).

The Python script makes a call to run.sh with the (1) input dir where the corpus is stored, (2) the concatenated corpus file and (3) the name of the outputted vector model. This is then inputted to train_sentences.py via sparv.sh where the fasttext vectors are created. The corpus file is a txt file with one sentence per line.

## NOTE
First round resulted in contaminated vectors for "skola" due to the baseform of "skall" and "ska", which is "skola". Another round of tokenization where "skall" and "ska" is represented by (fictuous) baseform "skall" is performed.