import asyncio
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cde.omr_engine.engine import process_omr_sheet

async def main():
    gt_path = r'C:\Users\bit\Downloads\Extract the Last Page from PDF OMR\ground_truth_page10.json'
    
    with open(gt_path, 'r') as f:
        ground_truth = json.load(f)['page_10']
        
    img_path = r'C:\Users\bit\Downloads\Extract the Last Page from PDF OMR\test_pages\page_10.png'
    with open(img_path, 'rb') as f:
        image_bytes = f.read()
        
    result = await process_omr_sheet(image_bytes)
    
    letter_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, None: 0}
    
    errors = []
    
    for q in result.questions:
        q_num = str(q.question_number)
        if q_num not in ground_truth: continue
        
        expected = int(ground_truth[q_num])
        actual = letter_map.get(q.selected_option, 0)
        
        if not q.needs_review and actual != expected:
            errors.append({
                'q': q.question_number,
                'expected': expected,
                'actual': actual,
                'confidence': q.confidence,
                'scores': q.scores
            })
            
    errors.sort(key=lambda x: x['q'])
    
    print(f'Total Hard Errors Found: {len(errors)}')
    for e in errors:
        s_fmt = [round(s, 2) for s in e['scores']]
        print(f"Q{e['q']:<3} | Expected: {e['expected']} | Actual: {e['actual']} | Conf: {e['confidence']:.2f} | Scores: {s_fmt}")

if __name__ == '__main__':
    asyncio.run(main())
