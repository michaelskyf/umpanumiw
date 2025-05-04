import argparse
import sys
import asyncio
from gui import launch_gui
from sftp_server import start_sftp
import db


def main():
    parser = argparse.ArgumentParser(description="File-Sharing Backend Server")
    parser.add_argument('--ui', choices=['terminal', 'gui'], default='terminal',
                        help='Choose interface for initial setup')
    parser.add_argument('--root', required=True,
                        help='Root directory for storing user files and DB')
    parser.add_argument('--host', default='0.0.0.0', help='Listen address')
    parser.add_argument('--port', type=int, default=8022, help='SFTP port')
    args = parser.parse_args()

    # Store root directory globally and initialize DB
    db.ROOT_DIR = args.root
    db.init_db()

    asyncio.create_task(start_sftp(args.host, args.port))

    if args.ui == 'gui':
        launch_gui()
    else:
        from auth import terminal_prompt
        terminal_prompt()

    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)