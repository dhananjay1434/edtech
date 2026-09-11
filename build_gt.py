
import json
import os

gt_path = r"C:\Users\bit\Downloads\Extract the Last Page from PDF OMR\full_ground_truth.json"
ground_truth = {}

for i in range(1, 11):
    pred_file = fr"C:\Users\bit\Downloads\Extract the Last Page from PDF OMR\new_preds_{i}.json"
    if not os.path.exists(pred_file):
        print(f"Missing {pred_file}")
        continue
    with open(pred_file, "r") as f:
        preds = json.load(f)
        
    page_data = {}
    for p in preds:
        # map state or predicted_option
        opt = p.get("predicted_option", 0)
        page_data[str(p["question"])] = opt
        
    ground_truth[f"page_{i}"] = page_data

with open(gt_path, "w") as f:
    json.dump(ground_truth, f)

print(f"Compiled ground truth from existing prediction files into {gt_path}")

