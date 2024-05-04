#!/bin/sh
ddr=../data/anti_corruption
pipenv run python \
   009_extend_items_google_scholar.py --config=$ddr/config.ini \
                   --outfile=$ddr/009_extend_items_google_scholar.jsonl \
                   --initems=resume \
                   --searchauthor=0
