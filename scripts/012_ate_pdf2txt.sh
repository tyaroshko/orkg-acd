#!/bin/sh
ddr=../data/anti_corruption
poetry run python \
   012_ate_pdf2txt.py --config=$ddr/config.ini \
                   --txtdir=$ddr/txts \
                   --pdfdir=$ddr/pdfs
