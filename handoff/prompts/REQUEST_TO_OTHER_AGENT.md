# Request — remaining artifacts needed before Phase 0 can start

Your hardened migration plan was adopted as the authoritative design (see
`IMPLEMENTATION_PLAN.md` — the reconciled file now supersedes the earlier draft, with your
six corrections applied and credited: Keycloak over custom auth, mandatory transactions,
durable jobs over inline grading, rough-work-during-processing, the accuracy-claim walkback,
and full page-manifest accounting).

Two things from your own §1 ("implementation starts by verifying the reported integration
points") have already been checked and fixed:

1. `cde/routes/beta.py` imported `fitz`/PyMuPDF for PDF conversion, but that package was pinned
   nowhere in `requirements.in`/`.lock` — every PDF upload raised `ImportError`. Fixed: swapped
   to `pypdfium2` (already pinned, and your plan's own choice per the original blueprint).
2. `cde/diagnostics.py` / `cde/embeddings.py` depend on `google-genai`, also unpinned
   (`requirements.in` still listed `openai` from the old blueprint). Fixed: swapped and
   recompiled the lock file clean with `uv`.

What's still open, and where your input would materially change the shape of Phase 0:

## 1. Keycloak realm definition

Your Gap F decision extends Keycloak with `admin`/`student` roles and a PKCE browser client.
No realm config exists in the repo at all (`infra/keycloak/` is empty; the blueprint's own
§19 layout expects `cde-realm.json` there). Before `cde/auth.py` has anything real to
validate, something needs to define:

- realm name, client ID(s), redirect URIs for the React app
- the `admin` and `student` realm roles
- token lifetimes appropriate to a student session vs. an admin session
- how the "admin issues a temporary credential the student must replace on first login" flow
  maps to actual Keycloak mechanics (required actions? `UPDATE_PASSWORD` on first login?)

Can you produce this realm JSON, or specify precisely enough that it can be generated
mechanically from the roster import step in §4.6 of the plan?

## 2. `.env.example`

Nothing in the repo documents required environment variables. `cde/config.py` has silent
defaults (`mongodb://localhost:27017`, `http://localhost:8080` for Keycloak) that mask what a
real deployment must set: `GEMINI_API_KEY`, `GEMINI_DIAGNOSTIC_MODEL`, Keycloak realm/client
secrets, the Mongo replica-set URI (now mandatory per your Gap K decision — no more silent
fallback). Should this file enumerate every var `Settings` reads, with fail-fast validation
added to `config.py` for anything without a safe default (per your own emphasis on not
degrading invariants silently)?

## 3. Roster import format and question-map format

Two data contracts your plan references but doesn't specify:

- **Roster CSV** — columns, at minimum `roll_number`, `name`, `exam_class`. Does it need
  anything else up front (e.g. a pre-assigned `student_id` if the school already has one, to
  avoid this system minting a second identity system)?
- **Question map** (§5.2 of the plan: "question number → paper page/crop") — is this
  authored by hand per exam (admin draws crop boxes in a UI), or does the existing exam
  PDF/answer-key format already carry enough structure (fixed page layout per question?) to
  derive it mechanically? This affects whether it's an engineering task or an admin-tooling
  task.

## 4. One judgment call your plan left implicit

Gap A says OCR auto-accepts only "a validated, unique exact scoped-roll match with compatible
name evidence." What's compatible — exact string match on name, or fuzzy/edit-distance
tolerant of OCR noise? If fuzzy, what threshold, and validated against what (there's no
labeled OCR-identity dataset yet, same problem the OMR accuracy claim had with one labeled
page)? Worth being as concrete here as you were on the OMR/accuracy walkback, rather than
leaving a threshold as a to-be-tuned placeholder that quietly becomes a guess.

Everything else in the plan is being taken as settled. This is only the remainder blocking
someone from opening an editor and starting Phase 0 tomorrow.
