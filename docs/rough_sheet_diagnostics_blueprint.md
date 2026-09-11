# Formative Diagnostics & Rough Sheet Analytics Blueprint

## 1. Architectural Vision
Move the Cognitive Diagnostic Engine from **summative assessment** (scoring OMR bubbles) to true **formative assessment** (diagnosing *why* a student failed). 

By leveraging the spatial reasoning capabilities of Gemini 1.5 Pro, the system will accept unstructured, messy "rough sheets", map scribbled calculations to specific exam questions, and classify the student's exact learning gaps. These individual gaps are then aggregated to provide teachers with class-wide insights, identifying systemic teaching issues.

---

## 2. Implementation Phases

### Phase 1: Unstructured Image Ingestion
**Goal:** Capture student rough sheets without requiring rigid templates or OpenCV bounding boxes.
* **Frontend (`StudentDiagnosticView.tsx` or new `StudentUpload.tsx`):**
  * Add an upload zone for students to submit photos of their "Rough Sheets" after an exam is complete.
* **Backend (`cde/uploads.py`):**
  * Store these uncropped, raw images securely in the local file store (or S3) and associate them with the student's `Submission` document.

### Phase 2: Gemini 1.5 Spatial Routing & Diagnostics
**Goal:** Process the entire raw rough sheet in a single AI pass, mapping calculations to wrong answers.
* **Update `cde/diagnostics.py`:**
  * Bypass the OpenCV `omr.py` requirement for `work_box` coordinates when dealing with rough sheets.
  * Construct a unified prompt that includes:
    1. The raw, full-page rough sheet image.
    2. A JSON array of the student's *incorrect* OMR choices.
    3. The original exam `question_context`.
  * **System Prompt Update:** Instruct Gemini to act as the spatial router *and* the diagnostic classifier simultaneously.
  * **Expected Output Schema (Pydantic):**
    ```python
    class DiagnosticResult(BaseModel):
        question_number: int
        found_on_rough_sheet: bool
        diagnostic_tag: Literal["Arithmetic Slip", "Procedural Flaw", "Conceptual Deficit", "Unknown"]
        explanation: str
    ```

### Phase 3: Database Persistence
**Goal:** Store the diagnostic taxonomies so they can be queried globally.
* **MongoDB Submissions Collection (`cde/db.py`):**
  * Append the `DiagnosticResult` objects directly to the student's answers array in the database.
  * Example document structure:
    ```json
    {
      "student_id": "std_123",
      "exam_id": "exam_456",
      "answers": [
        {
          "question_number": 4,
          "omr_selected": "C",
          "is_correct": false,
          "error_taxonomy": "Conceptual Deficit",
          "rough_work_analysis": "Student applied real-number properties to imaginary numbers."
        }
      ]
    }
    ```

### Phase 4: Class-Level Analytics Engine
**Goal:** Automatically identify generalized problems across the entire class.
* **New Backend Endpoint (`GET /api/exams/{exam_id}/insights`):**
  * Build a MongoDB Aggregation Pipeline to group the diagnostic tags by question.
  * **Aggregation Logic:**
    ```javascript
    db.submissions.aggregate([
      { $match: { exam_id: "exam_456" } },
      { $unwind: "$answers" },
      { $match: { "answers.is_correct": false } },
      { $group: {
          _id: { 
            question: "$answers.question_number", 
            error_type: "$answers.error_taxonomy" 
          },
          count: { $sum: 1 }
      }},
      { $sort: { count: -1 } }
    ])
    ```

### Phase 5: Teacher Insights Dashboard (UI)
**Goal:** Surface the MongoDB aggregations to the teacher in an actionable format.
* **Frontend (`TeacherExamDashboard.tsx`):**
  * Create a new "Class Insights" tab next to the Teacher Roster.
  * Render an Alert component for high-frequency conceptual errors.
  * **Example UI Output:**
    > 🚨 **Action Required: Question 6**
    > 14 students (70% of the class) got this wrong. 12 of those errors were classified as a **Conceptual Deficit** regarding fraction division. 
    > *Recommendation: Re-teach the 'invert and multiply' rule before the next exam.*

---

## 3. Technical Risks & Mitigations
1. **Context Window Limits:** A full rough sheet image + 10 questions takes significant context. Gemini 1.5 Pro natively handles 1M-2M tokens, so this is fully supported, but latency may be 10-15 seconds per API call.
2. **Illegible Handwriting:** If Gemini cannot read the rough sheet, it should elegantly default to the `Unknown` diagnostic tag rather than hallucinating an error type. The prompt must explicitly enforce this.
