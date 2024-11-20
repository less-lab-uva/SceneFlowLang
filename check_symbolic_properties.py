import argparse
import json
import os
import re
import time
from multiprocessing import Pool

from tqdm import tqdm
import SG_Utils as utils
from SymbolicMonitor import SymbolicMonitor
from pathlib import Path


def atof(text):
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    float regex comes from https://stackoverflow.com/a/12643073/190597
    '''
    return [atof(c) for c in re.split(r'[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)',
                                      text)]


def check_directory_single_thread(dir_to_check, save_folder, threaded=False):
    m = SymbolicMonitor(log_path=save_folder, route_path=dir_to_check.name)
    rsv_folder = dir_to_check/'rsv'
    sg_name_list = [p for p in os.listdir(rsv_folder) if p.endswith(".pkl")]
    sg_name_list = sorted(sg_name_list, key=natural_keys)
    # # Get 1 sg every 10 frames (2Hz)
    # if sut == 'InterFuser' or sut == 'TCP':
    #     if sut == 'TCP' and dir_to_check.name == 'done_RouteScenario_24':
    #         pass
    #     else:
    #         sg_name_list = [p for i, p in enumerate(sg_name_list) if i % 10 == 0]
    print(f"{str(dir_to_check)}: Checking {len(sg_name_list)} files")
    start = time.time()
    sgs = []
    ego_logs_path = dir_to_check/'ego_logs.json'
    ego_logs = None
    if ego_logs_path.exists():
        ego_logs = json.loads(ego_logs_path.read_text())['records']
    for sg_name in tqdm(sg_name_list, disable=threaded):
        sg = utils.load_sg(str(rsv_folder / sg_name))
        sg.graph['name'] = sg_name
        sg.graph['frame'] = sg_name.replace('.pkl', '')
        sg.graph['cache'] = {}
        if ego_logs is not None:
            cur_log = ego_logs[int(sg.graph['frame'])]
            ego_node = [node for node in sg.nodes if node.name == 'ego'][0]
            ego_node.attr['carla_speed'] = cur_log['state']['velocity']['value']
        sgs.append(sg)
    load_sg_end = time.time()
    print(f"Took {load_sg_end - start:.2f} seconds to load SGs")
    utils.add_missing(sgs)
    print(f"Took {time.time() - load_sg_end:.2f} seconds to add missing SGs")
    for sg in tqdm(sgs, disable=threaded):
        m.check(sg, save_usage_information=True)
        # m.save_all_relevant_subgraphs(sg, sg_name.replace('.pkl', ''))
    m.save_final_output()
    end = time.time()
    print(f"{str(dir_to_check)} | Checked {len(sg_name_list)} SGs | Total time taken: {end - start:.2f} seconds | Average time per SG: {(end - start) / len(sg_name_list):.2f} seconds")

def check_directory(dir_to_check, save_folder, sgs, threaded=False):
    m = SymbolicMonitor(log_path=save_folder, route_path=dir_to_check.name)
    rsv_folder = dir_to_check/'rsv'
    sg_name_list = [p for p in os.listdir(rsv_folder) if p.endswith(".pkl")]
    sg_name_list = sorted(sg_name_list, key=natural_keys)
    start = time.time()
    utils.add_missing(sgs)
    print(f"Took {time.time() - start:.2f} seconds to add missing SGs")
    for sg in tqdm(sgs, disable=threaded):
        m.check(sg, save_usage_information=True)
        # m.save_all_relevant_subgraphs(sg, sg_name.replace('.pkl', ''))
    m.save_final_output()
    end = time.time()
    print(f"{str(dir_to_check)} | Checked {len(sg_name_list)} SGs | Total time taken: {end - start:.2f} seconds | Average time per SG: {(end - start) / len(sg_name_list):.2f} seconds")

def main():
    parser = argparse.ArgumentParser(prog='Property checker')
    parser.add_argument('-f', '--folder_to_check', type=Path, required=True)
    parser.add_argument('-s', '--save_folder', type=Path, default='default/')
    parser.add_argument('-t', '--threaded', action='store_true')
    parser.add_argument('--n_threads', type=int, default=8)
    parser.add_argument('--no_iter', action='store_true')
    args = parser.parse_args()

    dirs = [p for p in args.folder_to_check.iterdir()]
    if args.threaded:
        results = []
        with Pool(args.n_threads) as p:
            for d in dirs:
                # Check if d is a directory
                if d.is_dir():
                    print(d)
                    start = time.time()
                    rsv_folder = Path(d) /'rsv'
                    sg_name_list = [p for p in os.listdir(rsv_folder) if p.endswith(".pkl")]
                    sg_name_list = sorted(sg_name_list, key=natural_keys)
                    sgs = []
                    ego_logs_path = Path(d) /'ego_logs.json'
                    ego_logs = None
                    if ego_logs_path.exists():
                        ego_logs = json.loads(ego_logs_path.read_text())['records']
                    for sg_name in tqdm(sg_name_list, disable=False):
                        sg = utils.load_sg(str(rsv_folder / sg_name))
                        sg.graph['name'] = sg_name
                        sg.graph['frame'] = sg_name.replace('.pkl', '')
                        sg.graph['cache'] = {}
                        if ego_logs is not None:
                            cur_log = ego_logs[int(sg.graph['frame'])]
                            ego_node = [node for node in sg.nodes if node.name == 'ego'][0]
                            ego_node.attr['carla_speed'] = cur_log['state']['velocity']['value']
                        sgs.append(sg)
                    print(f"Took {time.time() - start:.2f} seconds to load all SGs")
                    results.append(p.apply_async(check_directory, (d, args.save_folder, sgs, True)))
                else:
                    continue
            for r in results:
                r.wait()
    else:
        if args.no_iter:
            check_directory_single_thread(args.folder_to_check, args.save_folder, False)
        else:
            for d in sorted(dirs):
                check_directory_single_thread(d, args.save_folder, False)


if __name__ == "__main__":
    main()
