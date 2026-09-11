path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\web\src\api\roughSheets.ts"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace("export async function roughRequest<T>(api: CdeApi, path: string, options: RequestInit = {}): Promise<T> {", "export async function roughRequest<T>(_api: CdeApi, path: string, options: RequestInit = {}): Promise<T> {")
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
