#!/bin/sh
ddr=../data/anti_corruption
poetry run python \
   007_restricted_snowball.py --config=$ddr/config.ini \
                   --outfile=$ddr/007_restricted_snowball_output.jsonl \
                   --inptmfile=$ddr/006_ptm_output.npy \
                   --indictfile=$ddr/004_stopwords_reduceddict.jsonl \
                   --infile=resume \
                   --incooccurrencefile=$ddr/005_reduced_joint_probabilities.npy
