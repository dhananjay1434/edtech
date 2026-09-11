import asyncio, logging, os, socket, uuid
from dotenv import load_dotenv
load_dotenv()

from cde.db import db_adapter
from cde.jobs.queue import claim_job, fail_job
from cde.jobs.handlers import handle_read_sheet, handle_grade_sheet, handle_diagnose_sheet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cde.worker")

HANDLERS = {"read_sheet": handle_read_sheet, "grade_sheet": handle_grade_sheet,
           "diagnose_sheet": handle_diagnose_sheet}
POLL_SECONDS = 2


async def run_once(owner: str) -> bool:
    """Claim and run one job. Returns True if work was done."""
    for kind, handler in HANDLERS.items():
        job = claim_job(db_adapter.db, kind, owner)
        if not job:
            continue
        logger.info("claimed job=%s kind=%s attempt=%s",
                    job["_id"], kind, job["attempt_count"])
        try:
            await handler(db_adapter, job, owner)
            logger.info("completed job=%s", job["_id"])
        except Exception as exc:
            logger.exception("job=%s failed", job["_id"])
            fail_job(db_adapter.db, job["_id"], owner, job["fencing_token"], str(exc))
        return True
    return False


async def main():
    owner = f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:6]}"
    logger.info("worker %s started", owner)
    while True:
        did_work = await run_once(owner)
        if not did_work:
            await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
