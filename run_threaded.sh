#!/bin/bash

### Unpack the data
source unpack_data.sh

conda deactivate
conda activate tcp_env
python3 check_symbolic_properties.py -f ./study_data/scenarios/ -s ./results/scenarios/ --threaded
python3 check_symbolic_properties.py -f ./study_data/tcp/run1/ -s ./results/tcp/ --threaded
python3 check_symbolic_properties.py -f ./study_data/interfuser/run1/ -s ./results/interfuser/ --threaded

conda activate lav_env
python3 check_symbolic_properties.py -f ./study_data/lav/run1/ -s ./results/lav/ --threaded
python3 generate_tables.py
conda deactivate
