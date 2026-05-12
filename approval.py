import asyncio
from temporalio.client import Client

async def approve():
    client = await Client.connect('localhost:7233')
    handle = client.get_workflow_handle('release-001')
    await handle.signal('approve')
    print('Approval sent.')

asyncio.run(approve())