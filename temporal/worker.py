import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from activities import (
    build_components,
    run_integration_tests,
    sign_artifact,
    await_human_approval,
    deploy_to_truck,
)
from workflows import ReleaseWorkflow


async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="release-queue",
        workflows=[ReleaseWorkflow],
        activities=[
            build_components,
            run_integration_tests,
            sign_artifact,
            await_human_approval,
            deploy_to_truck,
        ],
    )
    print("Worker started. Listening on release-queue...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
