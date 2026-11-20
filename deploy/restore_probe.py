"""Verify a backup by starting the real API against a disposable restored copy."""

import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def main():
    data = json.load(sys.stdin)
    snapshot = Path(data["snapshot"]).resolve()
    if snapshot.parent != Path("/data/backups") or not snapshot.name.startswith(
        "acceptance-"
    ):
        raise SystemExit("Restore probe requires an acceptance backup in /data/backups")
    with tempfile.TemporaryDirectory(prefix="restore-") as directory:
        restored = Path(directory) / "restored.db"
        shutil.copyfile(snapshot, restored)
        with sqlite3.connect(restored) as db:
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise SystemExit("Restored database failed integrity check")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(128)
            port = listener.getsockname()[1]
            with tempfile.TemporaryFile(mode="w+") as log:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "app.main:app",
                        "--fd",
                        str(listener.fileno()),
                    ],
                    pass_fds=[listener.fileno()],
                    env={**os.environ, "DATABASE_URL": f"sqlite:///{restored}"},
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                try:
                    base = f"http://127.0.0.1:{port}/api/v1"
                    for _ in range(100):
                        if process.poll() is not None:
                            raise RuntimeError("Restored API exited before readiness")
                        try:
                            with urllib.request.urlopen(
                                f"{base}/health", timeout=1
                            ) as response:
                                if response.status == 200:
                                    break
                        except (urllib.error.URLError, TimeoutError):
                            time.sleep(0.1)
                    else:
                        raise RuntimeError("Restored API did not become ready")
                    payload = json.dumps(
                        {"email": data["email"], "password": data["password"]}
                    )
                    login = urllib.request.Request(
                        f"{base}/auth/login",
                        data=payload.encode(),
                        headers={"Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(login, timeout=10) as response:
                        token = json.load(response)["access_token"]
                    profile = urllib.request.Request(
                        f"{base}/auth/me",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    with urllib.request.urlopen(profile, timeout=5) as response:
                        if json.load(response)["id"] != data["user_id"]:
                            raise RuntimeError(
                                "Restored API returned the wrong identity"
                            )
                    print(
                        "Backup restored; real API readiness, login and identity checks passed."
                    )
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    main()
