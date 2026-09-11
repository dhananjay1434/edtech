import os
import sys
import base64
import json
from google import genai
from pydantic import BaseModel, Field

# Force stdout to utf-8 if needed, but safer to just use ascii logs
API_KEY = "REDACTED-GEMINI-KEY"
os.environ["GEMINI_API_KEY"] = API_KEY

client = genai.Client(api_key=API_KEY)

def generate_rough_sheet():
    print("[*] Generating a mock student rough sheet using Nano Banana (gemini-3.1-flash-image)...")
    prompt = "A photo of a student's messy math rough work on ruled notebook paper. The calculations are for a quadratic equation. There is a visible sign error where -b is written as positive. The handwriting is realistic and slightly scrawled."
    
    interaction = client.interactions.create(
        model="gemini-3.1-flash-image",
        input=prompt,
        response_format={
            "type": "image",
            "aspect_ratio": "3:4",
            "image_size": "1K"
        }
    )
    
    filename = "mock_rough_sheet.png"
    with open(filename, "wb") as f:
        f.write(base64.b64decode(interaction.output_image.data))
    print(f"[+] Generated rough sheet saved to {filename}")
    return filename, base64.b64decode(interaction.output_image.data)

class DiagnosticResult(BaseModel):
    error_type: str = Field(description="The categorization of the error (e.g. Arithmetic Slip, Conceptual Deficit).")
    explanation: str = Field(description="Detailed explanation of the student's mistake.")
    confidence: float = Field(description="Confidence in the diagnosis from 0.0 to 1.0.")

def analyze_rough_sheet(image_data):
    print("\n[*] Analyzing the generated rough sheet using Gemini Vision (gemini-3.1-pro-preview)...")
    
    prompt = """
    This is a student's rough sheet for a math exam. 
    Analyze the handwriting and calculations carefully. 
    Identify what the student was trying to solve, pinpoint the exact mathematical error they made, and categorize it.
    """
    
    interaction = client.interactions.create(
        model="gemini-3.1-pro-preview",
        input=[
            {"type": "text", "text": prompt},
            {
                "type": "image",
                "data": base64.b64encode(image_data).decode('utf-8'),
                "mime_type": "image/png"
            }
        ],
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": DiagnosticResult.model_json_schema()
        }
    )
    
    print("\n[=] Diagnosis Results:")
    print(interaction.output_text)

if __name__ == "__main__":
    try:
        filename, img_data = generate_rough_sheet()
        analyze_rough_sheet(img_data)
    except Exception as e:
        print(f"Error: {e}")
