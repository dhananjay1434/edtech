import asyncio
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cde.omr_engine.engine import process_omr_sheet

async def main():
    img_path = r'C:\Users\bit\Downloads\Extract the Last Page from PDF OMR\test_pages\page_10.png'
    with open(img_path, 'rb') as f:
        image_bytes = f.read()
        
    result = await process_omr_sheet(image_bytes)
    
    correct_scores = []
    for q in result.questions:
        if q.state == 'filled':
            best = max(q.scores)
            correct_scores.append(best)
            
    correct_scores.sort()
    print("Lowest 15 scores of bubbles marked 'filled':")
    for s in correct_scores[:15]:
        print(round(s, 2))

if __name__ == '__main__':
    asyncio.run(main())
