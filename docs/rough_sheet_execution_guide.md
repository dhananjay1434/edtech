# Rough Sheet Diagnostics: Execution Guide

**Target Repository:** `https://github.com/dhananjay1434/edtech.git`  
**Context:** We are upgrading a Cognitive Diagnostic Engine (FastAPI/React) from summative scoring to formative assessment. We need to ingest raw, uncropped "rough sheet" images (student scratchpads), bypass OpenCV bounding boxes, and send them directly to Gemini 1.5 Pro to diagnose *why* a student got an OMR question wrong.

**Agent Instructions:** Do not break the existing mock Keycloak authentication or the current OpenCV OMR pipeline. Implement the exact code and routes specified below.

---

## 1. Backend: Ingestion Endpoint
**File to modify:** `cde/routes/beta.py` (or `alpha.py`) & `cde/uploads.py`

Create a new route that allows students to upload their rough work after their OMR submission is accepted.

**Implementation Logic:**
1. Create `POST /api/exams/{exam_id}/submissions/{submission_id}/rough-sheets`
2. Accept a `multipart/form-data` file upload.
3. Save the file locally to `mock_s3_storage/{submission_id}_rough_sheet.png`.
4. Update the MongoDB `submissions` collection to include the rough sheet path:
```python
@router.post("/api/exams/{exam_id}/submissions/{submission_id}/rough-sheets")
async def upload_rough_sheet(
    exam_id: str,
    submission_id: str,
    file: UploadFile = File(...),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter)
):
    # 1. Save file
    file_location = f"mock_s3_storage/{submission_id}_rough_sheet.png"
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())
        
    # 2. Update MongoDB
    db_adapter.db.submissions.update_one(
        {"_id": submission_id, "exam_id": exam_id},
        {"$set": {"rough_sheet_path": file_location}}
    )
    return {"status": "success", "rough_sheet_path": file_location}
```

---

## 2. Backend: Diagnostic Engine Integration
**File to modify:** `cde/workflows.py` or wherever `diagnose()` is called.

*Note: `cde/diagnostics.py` has already been patched to accept a `rough_sheet_path` kwarg. Do not rewrite `diagnostics.py`.*

**Implementation Logic:**
During the grading pipeline, when processing incorrect answers, check if the submission has a `rough_sheet_path`. If it does, pass it to the diagnostic engine.

```python
# Inside the grading worker loop
submission = db.submissions.find_one({"_id": submission_id})
rough_sheet_path = submission.get("rough_sheet_path")

if not is_correct and rough_sheet_path:
    diagnostic_result = await diagnose(
        context=question_context, 
        crops=[], # Bypass OpenCV crops
        prompt=rubric_prompt, 
        schema=diagnostic_schema,
        rough_sheet_path=rough_sheet_path # Feed full image to Gemini
    )
    
    # Save the DiagnosticResult (Arithmetic Slip, Conceptual Deficit, etc.)
    db.submissions.update_one(
        {"_id": submission_id, "answers.question_number": q_num},
        {"$set": {"answers.$.diagnostic": diagnostic_result}}
    )
```

---

## 3. Backend: Class-Level Aggregation Endpoint
**File to modify:** `cde/routes/beta.py`

We need an endpoint for the teacher dashboard to identify generalized problems across the class.

**Implementation Logic:**
```python
@router.get("/api/exams/{exam_id}/insights")
async def get_class_insights(exam_id: str, db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    pipeline = [
        {"$match": {"exam_id": exam_id}},
        {"$unwind": "$answers"},
        {"$match": {"answers.is_correct": False, "answers.diagnostic": {"$exists": True}}},
        {"$group": {
            "_id": {
                "question": "$answers.question_number",
                "error_type": "$answers.diagnostic.diagnostic_tag"
            },
            "count": {"$sum": 1},
            "explanations": {"$push": "$answers.diagnostic.explanation"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    results = list(db_adapter.db.submissions.aggregate(pipeline))
    
    # Format for the frontend
    formatted = [
        {
            "question_number": r["_id"]["question"],
            "error_type": r["_id"]["error_type"],
            "count": r["count"],
            "sample_explanation": r["explanations"][0] if r["explanations"] else ""
        }
        for r in results
    ]
    return {"insights": formatted}
```

---

## 4. Frontend: Rough Sheet Dropzone
**File to modify:** `web/src/features/student/StudentExamView.tsx` (or similar)

**Implementation Logic:**
Add a simple file upload input that triggers an `XMLHttpRequest` to the new `/rough-sheets` endpoint after the main OMR is submitted.

```typescript
const uploadRoughSheet = async (file: File, examId: string, submissionId: string) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`/api/exams/${examId}/submissions/${submissionId}/rough-sheets`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer mock_token` },
        body: formData
    });
    
    if (response.ok) alert("Rough sheet analyzed!");
};
```

---

## 5. Frontend: Teacher Insights Dashboard
**File to modify:** `web/src/features/teacher/TeacherDashboard.tsx`

**Implementation Logic:**
Fetch the `/insights` endpoint and render alerts for high-frequency errors.

```typescript
// Fetch insights on mount
const [insights, setInsights] = useState([]);
useEffect(() => {
    fetch(`/api/exams/${examId}/insights`, { headers: { 'Authorization': 'Bearer mock_token' }})
        .then(res => res.json())
        .then(data => setInsights(data.insights));
}, [examId]);

// Render
return (
    <div className="insights-panel">
        {insights.map(insight => (
            <div className="alert bg-red-100 p-4 rounded-md mb-2">
                <strong>Action Required: Question {insight.question_number}</strong>
                <p>{insight.count} students made this exact error: {insight.error_type}</p>
                <p className="italic text-sm">Example: {insight.sample_explanation}</p>
            </div>
        ))}
    </div>
);
```
