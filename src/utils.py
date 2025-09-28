import csv

def save_lane_results_to_csv(lane_counts, file_prefix="lane_results"):
    """
    Save lane-wise counts to separate CSV files.
    lane_counts: dict, e.g. {1: {'car': 12, 'bus': 3}, 2: {'car': 5, 'bus': 2}}
    file_prefix: string, e.g. "lane_results" (files will be lane_results_lane1.csv, lane_results_lane2.csv...)
    """
    for lane_id, class_counts in lane_counts.items():
        filename = f"{file_prefix}_lane{lane_id}.csv"
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["class", "count"])
            for class_name, count in class_counts.items():
                writer.writerow([class_name, count])