# Cognitive Diagnostic Engine — Deep Business Logic Patch
## Execution Prompt for Advanced Reasoning AI

**Target Repository:** `https://github.com/dhananjay1434/edtech.git`
**Branch:** `main`

---

## 0. Executive Briefing
You are an elite Principal AI Architect. You are taking over a structurally sound Version 0.9 prototype. The previous agent swarm successfully built the distributed architecture: explicit MongoDB transaction boundaries, Temporal workflow orchestration, and subprocess-isolated OMR. 

**Your task is to implement the "Deep Empirical Business Logic" inside the existing adapters.** 
I will not hold your hand or dictate the exact libraries and math to use. I will present the three critical failure points of the current stubs. You must reason through the optimal architectural and mathematical solutions and write the production-grade code to fix them.

Clone the repository and execute the following three patches. Do not alter the overarching FastAPI or Temporal structural boundaries.

---

## Patch 1: The Concurrency Threat
**Target File:** `cde/merger_adapters.py`

**The Reality:** The previous Merger Agent bridged synchronous PyMongo with asynchronous Temporal by wrapping every database call in `asyncio.to_thread()`. Under high load (e.g., 5,000 concurrent submissions), this naive implementation will spin up an unbounded number of OS threads, leading to severe CPU thread-thrashing and pod crashes.

**Your Objective:** Architect a bounded concurrency solution that protects the asynchronous event loop without dropping the synchronous PyMongo `unit_of_work` transaction logic. You are free to design the exact threading or connection-pooling mechanism required to secure this bridge.

---

## Patch 2: The Deterministic OMR Kernel
**Target File:** `cde/omr.py` (Called by the secure sandbox in `omr_adapter.py`)

**The Reality:** The adapter securely sandboxes the `omr.py` script, but the script itself is a shallow stub. Real student exams are scanned with severe skew, coffee stains, aggressive erasures (smudges), and terrible lighting. 

**Your Objective:** Write the actual, hardcore OpenCV optical mark recognition pipeline.
1. It must mathematically snap skewed, malformed physical paper scans back into a perfect top-down grid.
2. It must mechanically strip the "Student Name/ID" bounding box to guarantee PII never reaches the downstream LLM.
3. It must deterministically read bubble fills, accounting for aggressive erasures and light smudges. If a bubble is truly ambiguous, flag it to trigger the LLM/HITL fallback.
Design the computer vision math as you see fit.

---

## Patch 3: Gemini Cognitive Tuning
**Target File:** `cde/diagnostics.py`

**The Reality:** The Pydantic structured output validation is flawless, but the string `prompt` passed to `gemini-1.5-pro` is a shallow zero-shot instruction. Without heavy guidance, Gemini cannot reliably distinguish between a simple "Calculation Slip" (e.g., 3x=12 -> x=5) and a deep "Conceptual Deficit" (e.g., misunderstanding imaginary numbers).

**Your Objective:** Engineer a highly sophisticated prompt architecture inside the `diagnose(...)` function. Design the necessary few-shot examples, chain-of-thought constraints, and visual reasoning instructions required to force Gemini to act as a world-class cognitive diagnostician.

---

## Execution
Think deeply about the implications of each implementation. Once your reasoning is complete, output the exact code required to rewrite these three files, and commit the changes as `feat(core): implement deep business logic`.
