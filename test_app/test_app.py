"""
Test App CLI: key management & SFTP file operations

Features:
  - keygen                  Generate RSA keypair
  - upload <local> <remote> Upload local file to remote /storage path
  - download <remote> <local> Download remote file under /storage path
  - rm <remote>             Remove remote file under /storage
  - ls <remote_dir>         List directory under /storage
  - share-list              List current shares via /config
  - share-add <path> <mode> <user_id>  Add a share (updates /config)
  - share-rm <share_id>     Remove a share by its ID (updates /config)

Usage:
  python test_app.py <command> [options]

Requirements:
  pip install paramiko
"""
import argparse
import os
import json
import stat
import sys
from paramiko import RSAKey, SSHClient, AutoAddPolicy
from paramiko.sftp_client import SFTPClient
from io import StringIO

# Default key file names
default_priv = 'id_test.rsa'
default_pub  = default_priv + '.pub'

# SSH/SFTP connection settings
HOST = 'localhost'
PORT = 8022
USERNAME = 'unused'


def generate_keypair(out_dir):
    key = RSAKey.generate(2048)
    priv_path = os.path.join(out_dir, default_priv)
    pub_path  = priv_path + '.pub'
    key.write_private_key_file(priv_path)
    os.chmod(priv_path, 0o600)
    pub_str = f"{key.get_name()} {key.get_base64()}"
    with open(pub_path, 'w') as pub_file:
        pub_file.write(pub_str + '\n')
    print(f"Private key: {priv_path}\nPublic key:  {pub_path}\n")
    print("Public key to paste into backend admin:")
    print(pub_str)


def connect_sftp(priv_key):
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    pkey = RSAKey.from_private_key_file(priv_key, password=None)
    client.connect(
        hostname=HOST,
        port=PORT,
        username=USERNAME,
        pkey=pkey
    )
    return client.open_sftp(), client


def cmd_upload(args):
    sftp, sh = connect_sftp(args.key)
    remote = '/storage/' + args.remote.lstrip('/')
    sftp.put(args.local, remote)
    print(f"Uploaded {args.local} to {remote}")
    sftp.close(); sh.close()


def cmd_download(args):
    sftp, sh = connect_sftp(args.key)
    remote = '/storage/' + args.remote.lstrip('/')
    sftp.get(remote, args.local)
    print(f"Downloaded {remote} to {args.local}")
    sftp.close(); sh.close()


def cmd_rm(args):
    sftp, sh = connect_sftp(args.key)
    path = '/storage/' + args.target.lstrip('/')
    sftp.remove(path)
    print(f"Removed {path}")
    sftp.close(); sh.close()


def cmd_ls(args):
    sftp, sh = connect_sftp(args.key)
    path = '/storage/' + args.remote_dir.lstrip('/')
    for entry in sftp.listdir(path):
        print(entry)
    sftp.close(); sh.close()


def read_config(sftp):
    with sftp.file('/config', 'r') as f:
        data = f.read().decode()
    return json.loads(data)


def write_config(sftp, shares):
    data = json.dumps(shares, indent=2)
    with sftp.file('/config', 'w') as f:
        f.write(data)
    print("Updated shares config.")


def cmd_share_list(args):
    sftp, sh = connect_sftp(args.key)
    shares = read_config(sftp)
    print(json.dumps(shares, indent=2))
    sftp.close(); sh.close()


def cmd_share_add(args):
    sftp, sh = connect_sftp(args.key)
    shares = read_config(sftp)
    new_id = max((s['id'] for s in shares), default=0) + 1
    shares.append({ 'id': new_id,
                    'path': args.path,
                    'mode': args.mode,
                    'user_id': args.user_id })
    write_config(sftp, shares)
    sftp.close(); sh.close()


def cmd_share_rm(args):
    sftp, sh = connect_sftp(args.key)
    shares = read_config(sftp)
    shares = [s for s in shares if s['id'] != args.share_id]
    write_config(sftp, shares)
    sftp.close(); sh.close()


def main():
    parser = argparse.ArgumentParser(description='Test App CLI')
    parser.add_argument('--key', default=default_priv,
                        help='Path to private key')
    sub = parser.add_subparsers(dest='cmd', required=True)

    sub.add_parser('keygen', help='Generate keypair')
    up = sub.add_parser('upload', help='Upload file')
    up.add_argument('local')
    up.add_argument('remote')
    dn = sub.add_parser('download', help='Download file')
    dn.add_argument('remote')
    dn.add_argument('local')
    rm = sub.add_parser('rm', help='Remove file')
    rm.add_argument('target')
    ls = sub.add_parser('ls', help='List directory')
    ls.add_argument('remote_dir')

    sub.add_parser('share-list', help='List shares')
    sa = sub.add_parser('share-add', help='Add share')
    sa.add_argument('path')
    sa.add_argument('mode', choices=['R','W','RW'])
    sa.add_argument('user_id', type=int)
    sr = sub.add_parser('share-rm', help='Remove share')
    sr.add_argument('share_id', type=int)

    args = parser.parse_args()
    if args.cmd == 'keygen':
        generate_keypair('.')
    elif args.cmd == 'upload': cmd_upload(args)
    elif args.cmd == 'download': cmd_download(args)
    elif args.cmd == 'rm': cmd_rm(args)
    elif args.cmd == 'ls': cmd_ls(args)
    elif args.cmd == 'share-list': cmd_share_list(args)
    elif args.cmd == 'share-add': cmd_share_add(args)
    elif args.cmd == 'share-rm': cmd_share_rm(args)

if __name__ == '__main__':
    main()
