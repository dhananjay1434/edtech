import os
import re

path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\cde\api.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

if "setup_logging" not in text:
    # Add imports
    text = "from cde.logging import setup_logging, set_correlation_id\nimport uuid\n" + text
    
    # Add setup_logging right after app = FastAPI()
    text = text.replace("app = FastAPI()", "app = FastAPI()\nsetup_logging()")
    
    # Add middleware
    middleware = """
@app.middleware("http")
async def correlation_id_middleware(request, call_next):
    cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response
"""
    text = text.replace("app = FastAPI()\nsetup_logging()", "app = FastAPI()\nsetup_logging()\n" + middleware)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
