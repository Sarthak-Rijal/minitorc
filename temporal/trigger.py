import argparse
import asyncio
import os
from temporalio.client import Client
from workflows import ReleaseWorkflow


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-id", default="release-001")
    args = parser.parse_args()

    host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(host)

    handle = await client.start_workflow(
        ReleaseWorkflow.run,
        args.release_id,
        id=args.release_id,
        task_queue="release-queue",
    )
    print(f"Started workflow: {handle.id}")
    print(f"Watch it at: http://{host.split(':')[0]}:8080")


if __name__ == "__main__":
    asyncio.run(main())
