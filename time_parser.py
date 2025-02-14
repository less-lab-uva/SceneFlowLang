import argparse
import json
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib import cbook

from pathlib import Path
from glob import glob

def main():
    parser = argparse.ArgumentParser(prog='Property checker')
    parser.add_argument('-f', '--folder_to_check', type=Path, required=True)
    args = parser.parse_args()
    timing_files = glob(f'{args.folder_to_check}/**/*_frame_times_*.json')
    all_times = []
    folder_times = defaultdict(list)
    for timing_file in timing_files:
        folder = timing_file.split('/')[1]
        with open(timing_file) as f:
            times_data = json.load(f)
            times = times_data['frame_times']
            times = [i * 1e-9 for i in times]  # convert from ns to s
            all_times.extend(times)
            folder_times['all'].extend(times)
            folder_times[folder].extend(times)
    plt.boxplot(folder_times.values(), labels=folder_times.keys())
    stats = cbook.boxplot_stats(folder_times.values(), labels=folder_times.keys())
    for data in stats:
        print(f"{data['label']} (seconds)")
        print(f"\tq1:\t{data['q1']}")
        print(f"\tmedian:\t{data['med']}")
        print(f"\tq3:\t{data['q3']}")
        print(f"\tmax:\t{max(data['fliers'])}")
        print(f"\tmean:\t{data['mean']}")
    plt.show()

if __name__ == '__main__':
    main()