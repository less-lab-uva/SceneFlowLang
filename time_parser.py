import argparse
import json
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib import cbook

from pathlib import Path
from glob import glob

from symbolic_properties_ego_only import all_symbolic_properties as ego_all_symbolic_properties
from symbolic_properties import all_symbolic_properties

def get_properties(ego_only):
    return ego_all_symbolic_properties if ego_only else all_symbolic_properties

def plot_data(data_dict):
    plt.boxplot(data_dict.values(), labels=data_dict.keys())
    stats = cbook.boxplot_stats(data_dict.values(), labels=data_dict.keys())
    for data in stats:
        print(f"{data['label']} (seconds)")
        print(f"\tq1:\t{data['q1']}")
        print(f"\tmedian:\t{data['med']}")
        print(f"\tq3:\t{data['q3']}")
        print(f"\tmax:\t{max(data['fliers'])}")
        print(f"\tmean:\t{data['mean']}")
    plt.show()

def main():
    parser = argparse.ArgumentParser(prog='Property checker')
    parser.add_argument('-f', '--folder_to_check', type=Path, required=True)
    args = parser.parse_args()
    timing_files = glob(f'{args.folder_to_check}/**/*_frame_times_*.json')
    all_times = []
    by_phi = defaultdict(list)
    folder_times = defaultdict(list)
    for timing_file in timing_files:
        folder = timing_file.split('/')[1]
        with open(timing_file) as f:
            times_data = json.load(f)
            phi = times_data['phi']
            ego_only = times_data['ego_only']
            times = times_data['frame_times']
            times = [i * 1e-9 for i in times]  # convert from ns to s
            all_times.extend(times)
            folder_times['all'].extend(times)
            folder_times[folder].extend(times)
            if 'scenario' not in timing_file:
                if phi == -1:
                    phi_name = 'all (ego only)' if ego_only else 'all'
                else:
                    phi_name = get_properties(ego_only)[phi].name
                by_phi[phi_name].extend(times)
    plot_data(by_phi)


if __name__ == '__main__':
    main()