"""Atomic JSON snapshots and cross-process locking, using only the standard library."""
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import threading
import time


class FileStore:
    def __init__(self,path=None):
        self.path=Path(path).expanduser().resolve() if path else None
        self._rows=[];self._initialized=False;self._mutex=threading.RLock()

    @contextmanager
    def transaction(self):
        with self._mutex:
            if self.path is None:
                state={'format_version':1,'initialized':self._initialized,'entries':deepcopy(self._rows)}
                yield state
                self._rows=deepcopy(state['entries']);self._initialized=state['initialized']
                return
            self.path.parent.mkdir(parents=True,exist_ok=True)
            lock=self.path.with_suffix(self.path.suffix+'.lock')
            with lock.open('a+b') as handle:
                handle.seek(0,os.SEEK_END)
                if handle.tell()==0:handle.write(b'0');handle.flush()
                deadline=time.monotonic()+10
                while True:
                    try:
                        handle.seek(0)
                        if os.name=='nt':
                            import msvcrt
                            msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
                        else:
                            import fcntl
                            fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                        break
                    except (BlockingIOError,OSError):
                        if time.monotonic()>=deadline:raise ValueError('Arquivo ocupado. Tente novamente em alguns segundos.') from None
                        time.sleep(.05)
                try:
                    state=self._read();before=json.dumps(state,sort_keys=True,ensure_ascii=False,allow_nan=False)
                    yield state
                    if before!=json.dumps(state,sort_keys=True,ensure_ascii=False,allow_nan=False):self._write(state)
                finally:
                    handle.seek(0)
                    if os.name=='nt':msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
                    else:fcntl.flock(handle.fileno(),fcntl.LOCK_UN)

    def _read(self):
        if not self.path.exists():return {'format_version':1,'initialized':False,'entries':[]}
        try:
            state=json.loads(self.path.read_text(encoding='utf-8'))
            if state.get('format_version')!=1 or not isinstance(state.get('entries'),list) or not isinstance(state.get('initialized'),bool):raise ValueError()
            return state
        except (ValueError,UnicodeError,AttributeError):raise ValueError('Arquivo de registros inválido. Restaure um backup; o arquivo não será sobrescrito.') from None

    def _write(self,state):
        content=json.dumps(state,ensure_ascii=False,allow_nan=False,indent=2)
        fd,name=tempfile.mkstemp(prefix=self.path.name+'.',suffix='.tmp',dir=self.path.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as handle:
                handle.write(content);handle.flush();os.fsync(handle.fileno())
            os.replace(name,self.path)
        finally:
            if os.path.exists(name):os.unlink(name)

    def state(self):
        with self.transaction() as state:return deepcopy(state)
