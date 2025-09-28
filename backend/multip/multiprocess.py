from multiprocessing import Pool
from Logic.yolo import process_video
from Logic.formula import analyze_traffic_data
from src.detect_video import detect_video
import csv
import json
video_files = [
    "data/traffic1.mp4",
    "data/traffic2.mp4",
    "data/traffic3.mp4",
    "data/traffic4.mp4"
]

def save_as_csv(results, file_path="data/traffic.csv"):
    """
    Save aggregated results to CSV
    """
    import csv
    keys = results[0].keys() if results else []
    with open(file_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    print(f"[CSV] Saved results to {file_path}")

def save_as_json(results, file_path="data/traffic_summary.json"):
    """
    Save aggregated results to JSON
    """
    import json
    with open(file_path, "w") as f:
        json.dump(results, f, indent=4)
    print(f"[JSON] Saved results to {file_path}")

def process_single_video(video):
    """
    Process a single video and return summary counts.
    """
    # Run detection (you can disable output_video_path or show_window if you want)
    summary = detect_video(video, show_window=False)
    return summary
def main():
    # Process videos in parallel
    with Pool(processes=4) as pool:
        all_results = pool.map(process_single_video, video_files)

    # Aggregate all video results using your formula.py logic
    aggregated_result = analyze_traffic_data(all_results)

    # Save detailed per-video results
    save_as_csv(all_results, file_path="data/traffic.csv")
    save_as_json(all_results, file_path="data/traffic_summary.json")

    # Optional: also save aggregated summary
    save_as_csv([aggregated_result], file_path="data/traffic_total.csv")
    save_as_json([aggregated_result], file_path="data/traffic_total.json")

    print("Final Aggregated Result:")
    print(aggregated_result)

if __name__ == "__main__":
    main()