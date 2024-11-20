import json
import os
import pandas as pd
from typing import Tuple
from pathlib import Path

EXCLUDED_PROPERTIES = [
    "816_vehicle2_cannot_follow_vehicle1_10_visible",
    "816_vehicle2_cannot_follow_vehicle1_50_visible",
]
PROPERTIES_MAPPING = {
    "816_vehicle2_cannot_follow_vehicle1_10_visible": {
        "name": r"$\phi_1^{10*}$",
        "violating_entity": "yield_vehicle_2"
    },
    "816_vehicle2_cannot_follow_vehicle1_50_visible": {
        "name": r"$\phi_1^{50*}$",
        "violating_entity": "yield_vehicle_2"
    },
    "816_vehicle2_cannot_follow_vehicle1_10_super_near": {
        "name": r"$\phi_1^{10}$",
        "violating_entity": "yield_vehicle_2"
    },
    "816_vehicle2_cannot_follow_vehicle1_50_super_near": {
        "name": r"$\phi_1^{50}$",
        "violating_entity": "yield_vehicle_2"
    },
    "820_vehicle2_needs_to_yield_to_vehicle1_stop_tie": {
        "name": r"$\phi_2$",
        "violating_entity": "yield_vehicle_2"
    },
    "821_vehicle2_needs_to_yield_to_vehicle1_stop": {
        "name": r"$\phi_3$",
        "violating_entity": "yield_vehicle_2"
    },
    "829_vehicle2_needs_to_yield_to_emergency": {
        "name": r"$\phi_4$",
        "violating_entity": "yield_vehicle_2"
    },
    "839_give_bikes_room_passing": {
        "name": r"$\phi_5$",
        "violating_entity": "pass_vehicle_1"
    },
    "839_give_bikes_room_passing_buffer": {
        "name": r"$\phi_5^*$",
        "violating_entity": "pass_vehicle_1"
    },
    "843_opp_clear_for_crossing": {
        "name": r"$\phi_6$",
        "violating_entity": "pass_vehicle_1"
    },
    "846_lane_you_leave_must_match_lane_you_enter": {
        "name": r"$\phi_7$",
        "violating_entity": "lane_vehicle_1"
    },
    "921_vehicle2_cannot_follow_emergency_vehicle1_10": {
        "name": r"$\phi_8^{10}$",
        "violating_entity": "yield_vehicle_2"
    },
    "921_vehicle2_cannot_follow_emergency_vehicle1_50": {
        "name": r"$\phi_8^{50}$",
        "violating_entity": "yield_vehicle_2"
    }
}



def process_stats_json(json_file_path: Path) -> dict:
    j = json.loads(json_file_path.read_text())
    dfa_stats = {p["name"]: 0 for p in PROPERTIES_MAPPING.values()}
    for key, value in j.items():
        for prop_name, n_dfa in value.items():
            if dfa_stats[PROPERTIES_MAPPING[prop_name]["name"]] < n_dfa:
                dfa_stats[PROPERTIES_MAPPING[prop_name]["name"]] = n_dfa
    return dfa_stats

def process_violation_json(json_file_path: Path, violation_name: str) -> dict:
    d = {}
    j = json.loads(json_file_path.read_text())
    if j["ego_id"] == j["entity_mapping"][PROPERTIES_MAPPING[violation_name]["violating_entity"]]:
        d["ego"] = 1
        d["other"] = 0
    else:
        d["ego"] = 0
        d["other"] = 1
    return d

def create_df_from_violations(violations_dict: dict) -> pd.DataFrame:
    # Prepare data for the dataframe
    rows = []
    # Define columns
    prop_columns = [PROPERTIES_MAPPING[key]["name"] for key in PROPERTIES_MAPPING if key not in EXCLUDED_PROPERTIES]
    columns = [(prop, 'ego') for prop in prop_columns]
    columns.extend([(prop, 'other') for prop in prop_columns])
    columns = sorted(columns)
    # Iterate over the data
    for first_key, second_level_dict in violations_dict.items():
        row = {}
        for col in columns:
            if col[0] in list(second_level_dict.keys()):
                row[col] = second_level_dict[col[0]][col[1]]
            else:
                row[col] = 0
        rows.append((first_key, row))
    # Create a DataFrame with MultiIndex columns
    df = pd.DataFrame([{col: row.get(col, None) for col in columns} for _, row in rows],
                      index=[first_key for first_key, _ in rows])
    # Assign MultiIndex columns
    df.columns = pd.MultiIndex.from_tuples(columns)
    return df

def parse_properties_check(base_folder: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    violations_dict = {}
    all_dfa_stats = {}
    for folder in os.listdir(base_folder):
        violations_dict[folder] = {}
        subfolder_list = os.listdir(base_folder / folder)
        if "stats.json" not in subfolder_list:
            print(f"{base_folder / folder} does not have stats.json")
            continue
        else:
            dfa_stats = process_stats_json(base_folder / folder / "stats.json")
            all_dfa_stats[folder] = dfa_stats
        if len(subfolder_list) > 1:
            for subfolder in subfolder_list:
                if subfolder in EXCLUDED_PROPERTIES:
                    continue
                violation_name = subfolder
                violation_dir = base_folder / folder / subfolder
                if os.path.isdir(violation_dir):
                    violation_dir = base_folder / folder / subfolder / "violations"
                    all_d = {
                        "ego": 0,
                        "other": 0
                    }
                    for json_file in os.listdir(violation_dir):
                        json_file_path = violation_dir / json_file
                        d = process_violation_json(json_file_path, violation_name)
                        all_d["ego"] += d["ego"]
                        all_d["other"] += d["other"]
                    violations_dict[folder][PROPERTIES_MAPPING[violation_name]["name"]] = all_d
    violations_df = create_df_from_violations(violations_dict)
    dfa_stats_df = pd.DataFrame(all_dfa_stats).T
    return violations_df, dfa_stats_df



# ## Autonomous Vehicles (TCP, InterFuser, LAV)
tcp_violations_df, tcp_dfa_stats_df = parse_properties_check(
    Path("./results/tcp/"))
lav_violations_df, lav_dfa_stats_df = parse_properties_check(
    Path("./results/lav/"))
interfuser_violations_df, interfuser_dfa_stats_df = parse_properties_check(
    Path("./results/interfuser/"))

# Sum the tcp_violations_df
aggregated_tcp_violations = tcp_violations_df.sum()
# Convert the Series to a DataFrame and set the index to "TCP"
aggregated_tcp_violations = aggregated_tcp_violations.to_frame().T
aggregated_tcp_violations.index = ["TCP~\cite{wu2022trajectory} "]
# Sum the lav_violations_df
aggregated_lav_violations = lav_violations_df.sum()
# Convert the Series to a DataFrame and set the index to "LAV"
aggregated_lav_violations = aggregated_lav_violations.to_frame().T
aggregated_lav_violations.index = ["LAV~\cite{chen2022lav}  "]
# Sum the lav_violations_df
aggregated_interfuser_violations = interfuser_violations_df.sum()
# Convert the Series to a DataFrame and set the index to "InterFuser"
aggregated_interfuser_violations = aggregated_interfuser_violations.to_frame().T
aggregated_interfuser_violations.index = ["InterFuser~\cite{shao2023safety}"]
# Concatenate the DataFrames
aggregated_violations = pd.concat([aggregated_tcp_violations, aggregated_lav_violations])
aggregated_violations = pd.concat([aggregated_violations, aggregated_interfuser_violations])
# Append the total row to the DataFrame with the index "Total"
total_row = aggregated_violations.sum()
aggregated_violations.loc['Total'] = total_row
# Rename the sub-columns
aggregated_violations = aggregated_violations.rename(columns={'ego': 'e', 'other': 'o'}, level=1)
# Replace all 0 with '-'
aggregated_violations = aggregated_violations.replace(0, '-')
# Switch position of col 1 and col 2
cols = list(aggregated_violations.columns)
cols[0], cols[1], cols[2], cols[3] = cols[2], cols[3], cols[0], cols[1]
# Drop last 2 columns
cols = cols[:-2]
aggregated_violations = aggregated_violations[cols]
print(aggregated_violations)


df_dropped = aggregated_violations.drop(
    columns=['$\phi_1^{50}$', '$\phi_1^{10}$', "$\phi_4$", "$\phi_5$", "$\phi_6$", "$\phi_8^{10}$"], level=0)
# Replace NaN back with '-'
df_dropped = df_dropped.replace(pd.NA, '-')
print(df_dropped)



def post_process_latex(latex: str) -> str:
    # Add hline after Total
    latex = latex.replace('Total', '\\hline\nTotal')
    # Col format
    new_col_format = ""
    col_format = latex.split("\\begin{tabular}{")[1].split("}\n")[0]
    for idx, col in enumerate(col_format):
        if idx == 0:
            new_col_format += "|"
            new_col_format += "l"
            new_col_format += "|"
        elif idx > 1 and idx % 2 == 0:
            new_col_format += "c"
            new_col_format += "|"
        else:
            new_col_format += "c"
    latex = latex.replace(col_format, new_col_format)
    latex = latex.replace("\\multicolumn{2}{l}", "\\multicolumn{2}{c|}")
    # Replace rules with hlines
    latex = latex.replace("\\toprule", "\\hline")
    latex = latex.replace("\\midrule", "\\hline")
    latex = latex.replace("\\bottomrule", "\\hline")
    return latex



# latex = aggregated_violations.to_latex(escape=False)
latex = df_dropped.to_latex(escape=False)
latex = post_process_latex(latex)


print(latex)


# ## Leaderboard 2.0 - ScenarioLogs
violations_df, dfa_stats_df = parse_properties_check(
    Path("./results/scenarios/"))


# Filter rows where any value in the row is non-zero
filtered_df = violations_df.loc[(violations_df != 0).any(axis=1)]

# Get the current index
current_index = filtered_df.index
# Create new index names
new_index = [f'S{i + 1}' for i in range(len(current_index))]  # + ['Total']
# Create a dictionary mapping the new index names to the original index names
index_mapping = {new: old for new, old in zip(new_index, current_index)}
# Invert index mapping
inverted_index_mapping = {v: k for k, v in index_mapping.items()}
# Assign the new index names to the DataFrame
filtered_df.index = new_index
# Rename the sub-columns
filtered_df = filtered_df.rename(columns={'ego': 'e', 'other': 'o'}, level=1)

# Switch position of col 1 and col 2
cols = list(filtered_df.columns)
cols[0], cols[1], cols[2], cols[3] = cols[2], cols[3], cols[0], cols[1]
# Drop last 2 columns
cols = cols[:-2]
filtered_df = filtered_df[cols]
# Drop all rows except the ones in keep_rows
keep_rows = [
    inverted_index_mapping["VehicleTurningRoute_left"],
    inverted_index_mapping["OppositeVehicleTakingPriority"],
    inverted_index_mapping["HazardAtSideLaneTwoWays"],
]
filtered_df = filtered_df.loc[keep_rows]
# Rename all row indexes from 1 to n
filtered_df = filtered_df.reset_index(drop=True)
# Add S in front of the index
filtered_df.index = [f'S{i + 1}' for i in range(len(filtered_df))]
# Calculate the sum of each column
total_row = filtered_df.sum()
# Append the total row to the DataFrame with the index "Total"
filtered_df.loc['Total'] = total_row
# Replace all 0 with '-'
filtered_df = filtered_df.replace(0, '-')
print(filtered_df)


df_dropped = filtered_df.drop(
    columns=['$\phi_1^{50}$', "$\phi_2$", "$\phi_4$", "$\phi_5$", "$\phi_7$", "$\phi_8^{10}$"], level=0)
# Replace NaN back with '-'
df_dropped = df_dropped.replace(pd.NA, '-')
print(df_dropped)
print(index_mapping)
latex = df_dropped.to_latex(escape=False)
latex = post_process_latex(latex)
print(latex)
