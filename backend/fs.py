import os
import json
import asyncssh
from auth import find_user_by_pubkey
from db import _connect

# ROOT_DIR used in db._connect

class VirtualFS(asyncssh.SFTPServer):
    def __init__(self, chan, conn):
        super().__init__(chan)
        key = conn.get_extra_info('public_key')
        self.pubkey = key.export_public_key().decode() if key else None
        self.uid = find_user_by_pubkey(self.pubkey)

    def _real_path(self, path):
        if not path.startswith('/storage'):
            raise FileNotFoundError(path)
        rel = path[len('/storage'):].lstrip('/')
        from db import ROOT_DIR
        userdir = os.path.join(ROOT_DIR, self.pubkey)
        full = os.path.join(userdir, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        return full

    async def open(self, path, pflags, attrs):
        if path == '/config':
            return ConfigFile(self.uid, pflags)
        real = self._real_path(path)
        mode = self._flags_to_mode(pflags)
        return await asyncssh.open_file(real, mode)

    def _flags_to_mode(self, flags):
        modes = {asyncssh.SFTP_OPEN_READ: 'r',
                 asyncssh.SFTP_OPEN_WRITE: 'w',
                 asyncssh.SFTP_OPEN_READ | asyncssh.SFTP_OPEN_WRITE: 'r+'}
        return modes.get(flags, 'r')

    async def stat(self, path):
        if path == '/config':
            attrs = asyncssh.SFTPAttrs()
            attrs.permissions = 0o600
            attrs.size = len(ConfigFile(self.uid, asyncssh.SFTP_OPEN_READ)._serialize_config())
            return attrs
        real = self._real_path(path)
        return await asyncssh.stat(real)

    async def readdir(self, path):
        if path == '/':
            return ['storage', 'config']
        if path == '/storage':
            return [self.pubkey]
        if path.startswith('/storage'):
            real = self._real_path(path)
            return os.listdir(real)
        raise FileNotFoundError(path)

    async def mkdir(self, path, attrs):
        real = self._real_path(path)
        os.makedirs(real, exist_ok=True)

    async def remove(self, path):
        real = self._real_path(path)
        os.remove(real)

class ConfigFile:
    def __init__(self, uid, pflags):
        from db import _connect, _lock
        self.uid = uid
        self.reading = bool(pflags & asyncssh.SFTP_OPEN_READ)
        self.buffer = '' if not self.reading else self._serialize_config()

    def _serialize_config(self):
        from db import _connect, _lock
        with _lock, _connect() as c:
            rows = c.execute("SELECT id, path, mode, user_id FROM SHARE WHERE owner_id=?", (self.uid,)).fetchall()
        return json.dumps([{ 'id':r[0],'path':r[1],'mode':r[2],'user_id':r[3] } for r in rows], indent=2)

    async def read(self, offset, length):
        return self.buffer.encode()[offset:offset+length]

    async def write(self, offset, data):
        self.buffer += data.decode()
        return len(data)

    async def close(self):
        from db import _connect, _lock
        if not self.reading:
            shares = json.loads(self.buffer)
            with _lock, _connect() as c:
                c.execute("DELETE FROM SHARE WHERE owner_id=?", (self.uid,))
                for s in shares:
                    c.execute("INSERT INTO SHARE(owner_id,path,mode,user_id) VALUES(?,?,?,?)", (
                        self.uid, s['path'], s['mode'], s['user_id']
                    ))
                c.commit()