#!/bin/sh
ddr=../data/anti_corruption
poetry run python \
   014_ate_generate_datasets.py --config=$ddr/config.ini \
                   --datasetdir=$ddr/datasets_partial \
                   --cleartxtdir=$ddr/clear_txts  \
                   --increment_size=2  \
                   --metadatafile=$ddr/011_exported.xlsx  \
                   --strategy="partial-spc-desc" \
                  #  --metadatafile=$ddr/010_download_pdfs.jsonl  \
                  #  --strategy="partial-spc-desc"
