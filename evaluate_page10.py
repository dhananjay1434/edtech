
import asyncio
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cde.omr_engine.engine import process_omr_sheet

async def main():
    gt_path = r"C:\Users\bit\Downloads\Extract the Last Page from PDF OMR\ground_truth_page10.json"
    
    with open(gt_path, "r") as f:
        ground_truth_raw = json.load(f)
        
    gt_answers = ground_truth_raw["page_10"]
    
    print("Evaluating OpenCV OMR Engine on Page 10...")
    print("-" * 50)
    
    img_path = r"C:\Users\bit\Downloads\Extract the Last Page from PDF OMR\test_pages\page_10.png"
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
        elif actual == expected:
            page_correct += 1
        else:
            page_incorrect += 1
            
    total_questions = len(result.questions)
    
    print(f"Total Questions Analyzed: {total_questions}")
    print(f"Auto-Graded Correctly: {page_correct} ({(page_correct/total_questions)*100:.2f}%)")
    print(f"Auto-Graded Incorrectly (Errors): {page_incorrect} ({(page_incorrect/total_questions)*100:.2f}%)")
    print(f"Flagged for HITL Review: {page_ambiguous} ({(page_ambiguous/total_questions)*100:.2f}%)")
    
if __name__ == "__main__":
    asyncio.run(main())

