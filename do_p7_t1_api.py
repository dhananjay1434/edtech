import os
path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\cde\api.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
text = re.sub(r"from cde\.routes import alpha, beta, gamma, admin, student\n?", "from cde.routes import beta, admin, student\n", text)
text = re.sub(r"app\.include_router\(alpha\.router\)\n?", "", text)
text = re.sub(r"app\.include_router\(gamma\.router\)\n?", "", text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

req_path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\requirements.in"
with open(req_path, "r", encoding="utf-8") as f:
    reqs = f.read()
reqs = re.sub(r"temporalio\n?", "", reqs)
with open(req_path, "w", encoding="utf-8") as f:
    f.write(reqs)
