import os
import base64
from google import genai

API_KEY = "REDACTED-GEMINI-KEY"
os.environ["GEMINI_API_KEY"] = API_KEY
client = genai.Client(api_key=API_KEY)

# Generate a 1x1 png image
image_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")

prompt = "This is a student's rough sheet. Identify what they were trying to solve."

try:
    interaction = client.interactions.create(
        model="gemini-3.1-pro-preview",
        input=[
            {"type": "text", "text": prompt},
            {"type": "image", "data": base64.b64encode(image_data).decode('utf-8'), "mime_type": "image/png"}
        ]
    )
    print("Success:", interaction.output_text)
except Exception as e:
    print(f"Error: {e}")
