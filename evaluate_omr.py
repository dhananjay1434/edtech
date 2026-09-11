
import asyncio
import json
import os
import sys

# Add the cde package to the path so we can import the engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cde.omr_engine.engine import process_omr_sheet

async def main():
    gt_path = r"C:\Users\bit\Downloads\Extract the Last Page from PDF OMR\full_ground_truth.json"
    if not os.path.exists(gt_path):
        print("Ground truth not ready yet!")
        return
        
    with open(gt_path, "r") as f:
        ground_truth = json.load(f)
        
    total_questions = 0
    total_correct = 0
    total_ambiguous = 0
    total_incorrect = 0
    
    print("Starting evaluation of OpenCV OMR Engine...")
    print("-" * 50)
    
    for i in range(1, 11):
        img_path = fr"C:\Users\bit\Downloads\Extract the Last Page from PDF OMR\test_pages\page_{i}.png"
        page_key = f"page_{i}"
        
        if page_key not in ground_truth:
            print(f"Skipping page {i}, no ground truth.")
            continue
            
        gt_answers = ground_truth[page_key]
        
        with open(img_path, "rb") as f:
            image_bytes = f.read()
            
        # Run our deterministic engine
        result = await process_omr_sheet(image_bytes)
        
        page_correct = 0
        page_ambiguous = 0
        page_incorrect = 0
        
        for q in result.questions:
            q_num = str(q.question_number)
            if q_num not in gt_answers:
                continue
                
            expected = int(gt_answers[q_num])
            
            # Map letter to number for comparison
            letter_map = {"A": 1, "B": 2, "C": 3, "D": 4, None: 0}
            actual = letter_map.get(q.selected_option, 0)
            
            if q.needs_review:
                page_ambiguous += 1
                total_ambiguous += 1
            elif actual == expected:
                page_correct += 1
                total_correct += 1
            else:
                page_incorrect += 1
                total_incorrect += 1
                
        total_questions += len(result.questions)
        print(f"Page {i}: {page_correct} Correct | {page_incorrect} Incorrect | {page_ambiguous} Sent to Review Queue")

    print("-" * 50)
    print("FINAL EVALUATION METRICS")
    print(f"Total Questions Analyzed: {total_questions}")
    print(f"Auto-Graded Correctly: {total_correct} ({(total_correct/total_questions)*100:.2f}%)")
    print(f"Auto-Graded Incorrectly (Errors): {total_incorrect} ({(total_incorrect/total_questions)*100:.2f}%)")
    print(f"Flagged for HITL Review: {total_ambiguous} ({(total_ambiguous/total_questions)*100:.2f}%)")
    
if __name__ == "__main__":
    asyncio.run(main())

