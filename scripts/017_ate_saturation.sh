#!/bin/sh
ddr=../data/anti_corruption
poetry run python \
   017_ate_saturation.py \
       --config=$ddr/config.ini \
       --in_dir=$ddr/terms_clear \
       --out_thd=$ddr/017_thd.csv
    #    --in_dir=$ddr/terms_clear \
   #  --in_dir=$ddr/terms_partial \