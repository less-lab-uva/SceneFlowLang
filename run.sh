#!/bin/bash

### Unpack the data
source unpack_data.sh

conda activate tcp_env
python3 check_symbolic_properties.py -f ./study_data/scenarios/ -s ./results/scenarios/
python3 check_symbolic_properties.py -f ./study_data/tcp/run1/ -s ./results/tcp/
python3 check_symbolic_properties.py -f ./study_data/interfuser/run1/ -s ./results/interfuser/

conda activate lav_env
python3 check_symbolic_properties.py -f ./study_data/lav/run1/ -s ./results/lav/
python3 generate_tables.py
conda deactivate
