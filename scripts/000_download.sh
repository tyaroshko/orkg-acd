#!/bin/sh
poetry run python \
   000_download.py --config=../data/anti_corruption/config.ini \
                   --outfile=../data/anti_corruption/000_download_output.jsonl \
                   --infile=resume                  
                  #  --infile=../data/GAN/in-seed.csv
