import os
import asyncio
import asyncssh
import db
from fs import VirtualFS

# Host key filenames under root directory
HOST_KEY_NAME = 'key.rsa'

async def start_server(host, port):
    # Ensure host key in place
    root = db.ROOT_DIR
    os.makedirs(root, exist_ok=True)
    key_path = os.path.join(root, HOST_KEY_NAME)

    # Start listening
    print(f'Listening for SFTP on {host}:{port} …')
    await asyncssh.listen(
        host, port,
        server_host_keys=[key_path],
        sftp_factory=VirtualFS
    )


def start_sftp(host, port):
    # Print immediately before starting loop
    print(f'Starting SFTP server at {host}:{port}...')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server(host, port))
    loop.run_forever()