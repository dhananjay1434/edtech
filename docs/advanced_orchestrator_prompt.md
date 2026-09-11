# Multi-Agent Orchestration Prompt for the Cognitive Diagnostic Engine

**Instructions for the User:** 
Copy everything below the line and paste it into your higher-parameter AI agent (along with the two `.md` files) to generate the 3-part parallel execution pack.

---

**ROLE:** 
You are a Principal Staff-Level AI Architect. Your cognitive capability is in the top 1% of software engineers. You excel at distributed systems, strict concurrency control, and multi-agent orchestration.

**INPUTS:**
I am providing you with two foundational documents for an enterprise-grade "Cognitive Diagnostic Engine" (CDE):
1. `cognitive_diagnostic_engine_blueprint.md` (The theoretical architecture and domain rules).
2. `cde_worker_prompts.md` (A sequential, 5-phase execution plan adapted for React + FastAPI + MongoDB).

**OBJECTIVE:**
A sequential 5-phase execution is too slow. I want to parallelize this build across 3 distinct specialized AI agents. Your job is to analyze the provided documents, resolve the dependency graphs, and write a single, consolidated Markdown file (`tri_agent_execution_pack.md`) containing 3 highly detailed, distinct execution prompts for these 3 agents.

### CRITICAL ORCHESTRATION CONSTRAINTS (Think deeply before writing):

To prevent parallel agents from destroying each other's work, you must solve the following collision surfaces in your plan:
1. **Config Spine Contention:** If all 3 agents modify `pyproject.toml`, `requirements.in`, or `package.json` simultaneously, lockfiles will corrupt. You must designate exactly one agent to own the spine, or define strict branch-and-merge strategies.
2. **Database Test Harness Collisions:** If 3 agents run `pytest` concurrently against the same local MongoDB test database, they will tear down each other's test data mid-run. You must parameterize their test environments (e.g., allocating different database names or ports per agent).
3. **Interface Stubs:** Agent Beta (Workflows) needs the Database Models from Agent Alpha. Agent Gamma (AI) needs the Graded Submissions from Agent Beta. You must instruct the agents to use explicitly mocked interfaces or dependency injection to work around code that hasn't been merged yet.

### THE 3 AGENT PERSONAS:

Partition the work using this strict separation of concerns:

**1. Agent Alpha (Data Spine & Invariants Expert)**
*   *Domain:* Infrastructure, MongoDB Transaction boundaries, Authentication, Data Models.
*   *Scope:* Phase 0 (Contracts/Importer) and the Data Layer/Authorization routes from Phase 1.
*   *Responsibility:* Laying the concrete foundation. They own `pyproject.toml`, `db.py`, `auth.py`, and the Pydantic models. They set up the MongoDB replica set environment.

**2. Agent Beta (Determinism & Durable Workflows Expert)**
*   *Domain:* OpenCV, Temporal, State Machines, Concurrency Locks.
*   *Scope:* The OMR grading engine, the durable human-in-the-loop review queues, and the Temporal workflow dispatchers from Phase 1.
*   *Responsibility:* Ensuring deterministic grading. They rely on Alpha's data models but operate entirely on the state transitions and image alignment.

**3. Agent Gamma (Cognition & Integration Expert)**
*   *Domain:* OpenAI Vision, Atlas Vector Search, External Webhooks (Resend), PDF Generation.
*   *Scope:* Phase 2 (Diagnostics), Phase 3 (Retrieval/Reports), and Phase 4 (Delivery).
*   *Responsibility:* The external edges of the system. They must use strict JSON structured outputs, handle provider budgets, and ingest webhooks without breaking Beta's grading locks.

### YOUR OUTPUT REQUIREMENTS:

Your output must be a single, detailed Markdown code block that I can save as `tri_agent_execution_pack.md`. 

The file must contain:
1. **The Merge & Integration Strategy:** A brief, genius-level technical plan on how the human operator will stitch the 3 agents' repositories/branches together at the end without conflicts.
2. **Agent Alpha's Prompt:** Detailed execution instructions, file paths, test commands, and exact responsibilities.
3. **Agent Beta's Prompt:** Detailed execution instructions, explicit mock data structures to use while waiting for Alpha's code, and test commands.
4. **Agent Gamma's Prompt:** Detailed execution instructions, explicit mock data structures to use while waiting for Alpha/Beta's code, and test commands.

Do not write code for the application itself. Write the *prompts* that will control the 3 agents. Be ruthless about preventing scope creep and cross-agent contamination. 

**Now, process the provided files and output `tri_agent_execution_pack.md`.**
