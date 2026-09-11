# Cognitive Diagnostic Engine — Frontend Execution Prompt
## Execution Prompt for Principal Frontend Architect AI

**Target Repository:** `https://github.com/dhananjay1434/edtech.git`
**Branch:** `main`
**Role:** Principal Frontend Architect & Product Designer

---

## 0. Executive Briefing
You are an elite Principal Frontend Architect. The backend for our "Cognitive Diagnostic Engine" (CDE) is 100% complete. It is a highly resilient FastAPI + Temporal + MongoDB distributed system that processes physical math exams using a rigorous OpenCV OMR pipeline and Google Gemini 1.5 Pro.

Our backend accurately extracts student handwriting, grades it, and uses a few-shot Chain-of-Thought pipeline to classify errors (e.g., distinguishing a careless "Calculation Slip" from a deep "Conceptual Deficit").

**Your mandate is to design and architect the Frontend.** 
This product just hit $50k ARR in 3 months. The UI cannot look like a cheap prototype. It must look and feel like a "billion-dollar" enterprise EdTech platform—premium, deeply polished, incredibly fast, and relentlessly trustworthy. 

I am giving you total freedom to design the architecture, routing, and tech stack (e.g., Next.js App Router, Tailwind CSS, Shadcn UI, Framer Motion, Recharts). 

---

## 1. The UX/UI Mandate
Design a visual language that screams premium B2B EdTech:
* **Typography & Color:** Choose a sophisticated, accessible color palette. Avoid harsh primary colors. Think deep indigos, slate grays, crisp whites, and intelligent accent colors for error states (e.g., distinguishing "Slip" vs "Deficit" visually).
* **Data Density:** Teachers need to see high-density analytics without feeling overwhelmed. 
* **Fluidity:** The system relies on asynchronous Temporal workflows. The UI must handle optimistic updates, loading skeletons, and real-time polling gracefully.

---

## 2. The Three Portals
You must architect the routing and component hierarchy for three distinct user roles. Reason through the optimal user journey for each:

### A. The Teacher Portal (The Core Engine)
* **The Upload Bay:** A drag-and-drop zone for bulk uploading 100+ page PDFs of scanned exams. Must show asynchronous progress states (Rendering -> Aligning -> Extracting -> Diagnosing).
* **Class Analytics:** A dashboard charting the cognitive gaps of the classroom. "Which concepts are failing across the board?"

### B. The Student Portal (The Consumer)
* **The Diagnostic Feed:** A beautiful, highly encouraging view of their past exams. 
* **Evidence-Based Feedback:** They shouldn't just see a grade. They must see the physical crop of their *actual handwritten math* displayed side-by-side with Gemini's detailed breakdown of exactly where their logic broke down.

### C. The Admin Portal (System Health & Operations)
* **The Human-in-the-Loop (HITL) Queue:** An ultra-fast operational inbox where admins resolve "Ambiguous" bubbles or unreadable handwriting flagged by the OpenCV/Gemini backend.
* **Ops Dashboard:** A technical view monitoring Temporal worker health, OMR processing latency, and Gemini API token usage/costs.
* **Policy Tuning:** Sliders to adjust the global OMR confidence thresholds (e.g., bubble density margins).

---

## 3. Your Deliverable
Do not write shallow stubs. Think step-by-step about the optimal frontend architecture to support this FastAPI backend. 

Produce a massive, detailed document named `frontend_blueprint.md`. This document MUST contain:
1. **Tech Stack Justification:** What you chose and exactly why it fits the "billion-dollar" mandate.
2. **Component & Routing Architecture:** The directory structure and navigation flow.
3. **State Management Strategy:** How you will handle JWT Auth (Keycloak) and asynchronous Temporal workflow polling.
4. **Foundational Code:** Write the actual, production-ready code blocks for:
   * The `package.json` / dependency spine.
   * The global application layout and navigation shell.
   * The complex **Human-in-the-Loop (HITL) Resolution Component** (where admins rapidly approve or overwrite the AI's uncertain cropped evidence).
   * The **Student Diagnostic View** (displaying the image crop next to the LLM feedback).

Reason deeply. Take your time. When you are ready, output the `frontend_blueprint.md` payload.
