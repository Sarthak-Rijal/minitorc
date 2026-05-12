from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities import (
        build_components,
        run_integration_tests,
        sign_artifact,
        await_human_approval,
        deploy_to_truck,
    )


@workflow.defn
class ReleaseWorkflow:

    def __init__(self):
        self._approved = False

    @workflow.signal
    async def approve(self):
        workflow.logger.info("Human approval signal received.")
        self._approved = True

    @workflow.run
    async def run(self, release_id: str) -> str:
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
        )

        workflow.logger.info(f"Release {release_id} started.")

        await workflow.execute_activity(
            build_components, release_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        await workflow.execute_activity(
            run_integration_tests, release_id,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        await workflow.execute_activity(
            sign_artifact, release_id,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        # Block until the approve signal arrives
        await workflow.wait_condition(lambda: self._approved)
        workflow.logger.info("Approval confirmed — proceeding to deploy.")

        result = await workflow.execute_activity(
            deploy_to_truck, release_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"Release {release_id} complete: {result}")
        return result
