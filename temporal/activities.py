import asyncio
import random
from datetime import datetime
from temporalio import activity


@activity.defn
async def build_components(release_id: str) -> str:
    activity.logger.info(f"[{release_id}] Building components...")
    await asyncio.sleep(2)
    activity.logger.info(f"[{release_id}] Build complete.")
    return f"artifact-{release_id}.tar.gz"


@activity.defn
async def run_integration_tests(release_id: str) -> str:
    activity.logger.info(f"[{release_id}] Running integration tests...")
    await asyncio.sleep(2)

    # Randomly fail 30% of the time — watch Temporal retry automatically
    if random.random() < 0.3:
        raise RuntimeError(f"[{release_id}] Integration tests failed — flaky test detected")

    activity.logger.info(f"[{release_id}] All tests passed.")
    return "tests_passed"


@activity.defn
async def sign_artifact(release_id: str) -> str:
    activity.logger.info(f"[{release_id}] Signing artifact...")
    await asyncio.sleep(1)
    signature = f"sig-{release_id}-{datetime.utcnow().isoformat()}"
    activity.logger.info(f"[{release_id}] Artifact signed: {signature}")
    return signature


@activity.defn
async def await_human_approval(release_id: str) -> str:
    activity.logger.info(f"[{release_id}] Waiting for human approval...")
    # Polls every 5 seconds — in real life this blocks until a signal arrives
    for i in range(24):
        activity.heartbeat(f"Waiting for approval — attempt {i+1}/24")
        await asyncio.sleep(5)
        activity.logger.info(f"[{release_id}] Still waiting for approval...")
    raise RuntimeError(f"[{release_id}] Approval timed out after 2 minutes")


@activity.defn
async def deploy_to_truck(release_id: str) -> str:
    activity.logger.info(f"[{release_id}] Deploying to truck...")
    await asyncio.sleep(2)
    activity.logger.info(f"[{release_id}] Deployment complete.")
    return f"deployed-{release_id}"
