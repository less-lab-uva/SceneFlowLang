import json
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib import cbook
import matplotlib

matplotlib.rcParams.update({'font.size': 12})

import numpy as np

from pathlib import Path
from glob import glob

from symbolic_properties_ego_only import all_symbolic_properties as ego_all_symbolic_properties
from symbolic_properties import all_symbolic_properties
from generate_tables import PROPERTIES_MAPPING


def get_properties(ego_only):
    return ego_all_symbolic_properties if ego_only else all_symbolic_properties


def plot_data(data_dict, key_order):
    plt.figure(figsize=(16, 9) if len(key_order) > 2 else (5, 9))
    whis_offset = 5
    whis = (whis_offset, 100-whis_offset)
    result = plt.boxplot([data_dict[key] for key in key_order], labels=key_order, whis=whis, showfliers=False, showmeans=True, whiskerprops={'color': 'red', 'linestyle': 'dotted'})
    stats = cbook.boxplot_stats([data_dict[key] for key in key_order], labels=key_order, whis=whis)
    for data in stats:
        print(f"{data['label']} (seconds)")
        print(f"\t{whis[0]}:\t{data['whislo']}")
        print(f"\tq1:\t{data['q1']}")
        print(f"\tmedian:\t{data['med']}")
        print(f"\tq3:\t{data['q3']}")
        print(f"\t{whis[-1]}:\t{data['whishi']}")
        print(f"\tmax:\t{max(data['fliers'])}")
        print(f"\tmean:\t{data['mean']}")
    plt.ylim([0, 0.57] if len(key_order) == 2 else [0, 2])
    plt.xlim([0.5, len(key_order)+0.5])
    hline = plt.hlines(y=0.5, xmin=0.5, xmax=len(key_order)+.5, label='0.5s ($2Hz$) Framerate', linestyle='--')
    for index, key in enumerate(key_order):
        number_above = len([i for i in data_dict[key] if i > 0.5])
        plt.text(index+1, .535 if len(key_order) == 2 else 1.8, f'{key}\n{round(number_above/len(data_dict[key])*100, 2)}%>0.5s $(2Hz)$\nMax:\n{max(data_dict[key]):.2f}s',
                  bbox={'facecolor': 'white', 'alpha': 1, 'edgecolor': 'none', 'pad': 1},
                  ha='center', va='center')
        plt.text(index + 1, min(stats[index]["whishi"] + (.015 if len(key_order) == 2 else 0.035), 0.485 if len(key_order) == 2 else 1000),
                 f'{whis[-1]}%$\leq${stats[index]["whishi"]:.2f}s',
                 bbox={'facecolor': 'white', 'alpha': 1, 'edgecolor': 'none', 'pad': 1},
                 ha='center', va='center')
    plt.ylabel('Time to Compute (seconds)')
    plt.xlabel('Property' if len(key_order) > 2 else 'Evaluation Method')
    plt.title('Time to Compute Properties per Frame')
    plt.legend([hline, result["whiskers"][0], result["medians"][0], result["means"][0]],
               ['0.5s ($2Hz$) Framerate', f'{whis[0]}% to {whis[1]}%', "Median", "Mean"],
               loc='center right')
    filename = f"frame_time_hist_{'ego_only' if len(key_order) == 2 else 'all'}"
    for ending in ['svg', 'pdf']:
        plt.savefig(f'{filename}.{ending}')

def main():
    serial_label = 'Serial'
    parallel_label = 'Parallel'
    ego_files = glob('study_timing_data/results_time_ego/**/*_frame_times_*.json')
    not_ego_files = glob('study_timing_data/results_time/**/*_frame_times_*.json')
    all_files = []
    all_files.extend(ego_files)
    all_files.extend(not_ego_files)
    all_times = []
    totals = defaultdict(int)
    by_phi = defaultdict(list)
    route_map = defaultdict(list)
    folder_times = defaultdict(list)
    parallel_times = defaultdict(list)
    ego_str = ''
    all_str = ' (all)'
    for timing_file in all_files:
        with open(timing_file) as f:
            times_data = json.load(f)
            route = times_data['folder']
            phi = times_data['phi']
            run = times_data['run']
            folder = timing_file.split('/')[-2]
            route_map[route].append((phi, run))
            totals[phi] += len(times_data['frame_times'])
            times = times_data['frame_times']
            times = [i * 1e-9 for i in times]  # convert from ns to s
            all_times.extend(times)
            folder_times['all'].extend(times)
            folder_times[folder].extend(times)
            if 'scenario' not in timing_file:
                if phi == -1:
                    phi_name = serial_label + (ego_str if 'ego' in timing_file else all_str)
                    by_phi[phi_name].extend(times)
                else:
                    parallel_times[('ego' if 'ego' in timing_file else 'all', folder, route, run)].append(times)
    for key, timing_lists in parallel_times.items():
        timing_lists = np.array(timing_lists)
        worst_times = np.max(timing_lists, axis=0)
        by_phi[parallel_label + (ego_str if 'ego' in key[0] else all_str)].extend(worst_times.tolist())
    missing = False
    for route in route_map:
        for phi in range(-1, 12):
            for run in range(1, 11):
                key = (phi, run)
                if key not in route_map[route]:
                    print('missing', route, 'phi', phi, 'run', run)
                    missing = True
    if missing:
        quit()
    key_order = [val['name'] for key, val in PROPERTIES_MAPPING.items()]
    key_order.append(serial_label + ego_str)
    key_order.append(parallel_label + ego_str)
    key_order = [k for k in key_order if k in by_phi.keys()]
    plot_data(by_phi, key_order)
    key_order = [val['name'] for key, val in PROPERTIES_MAPPING.items()]
    key_order.append(serial_label + all_str)
    key_order.append(serial_label + ego_str)
    key_order.append(parallel_label + all_str)
    key_order.append(parallel_label + ego_str)
    key_order = [k for k in key_order if k in by_phi.keys()]
    plot_data(by_phi, key_order)


if __name__ == '__main__':
    main()
