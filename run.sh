#!/bin/bash

### Unpack the data
source unpack_data.sh

for run in {1..3}
do
  for phi in {-1..12}
  do
    echo "Run ${run}, Phi ${phi}"
    conda activate tcp_env
    python3 check_symbolic_properties.py -f ./study_data/scenarios/ -s ./results_time_ego/scenarios/ --run $run --phi $phi --ego_only
    python3 check_symbolic_properties.py -f ./study_data/tcp/run1/ -s ./results_time_ego/tcp/ --run $run --phi $phi --ego_only
    python3 check_symbolic_properties.py -f ./study_data/interfuser/run1/ -s ./results_time_ego/interfuser/ --run $run --phi $phi --ego_only

    conda activate lav_env
    python3 check_symbolic_properties.py -f ./study_data/lav/run1/ -s ./results_time_ego/lav/ --run $run --phi $phi --ego_only
    python3 generate_tables.py
    conda deactivate
  done
done
