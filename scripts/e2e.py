"""Run real-browser verification with isolated databases, credentials and bounded servers."""

import argparse
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

root = Path(__file__).resolve().parents[1]


def ready(url: str, process: subprocess.Popen):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError(f"Server exited before readiness: {url}")
        try:
            response = httpx.get(url, timeout=1)
            if response.status_code == 200:
                return
        except (httpx.ConnectError, httpx.ReadTimeout):
            pass
        time.sleep(0.1)
    raise RuntimeError(f"Server did not become ready: {url}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--postman",
        action="store_true",
        help="Also run the collection with pinned Newman via npm exec",
    )
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="procureai-e2e-") as directory:
        env = {
            **os.environ,
            "ENVIRONMENT": "development",
            "JWT_SECRET": secrets.token_urlsafe(48),
            "DEMO_PASSWORD": secrets.token_urlsafe(24) + "A1",
            "DATABASE_URL": f"sqlite:///{directory}/browser.db",
            "COOKIE_SECURE": "false",
            "CORS_ORIGINS": json.dumps(["http://localhost:5174"]),
            "FRONTEND_URL": "http://localhost:5174",
            "STAGING_URL": "",
            "API_PROXY_TARGET": "http://127.0.0.1:8001",
        }
        python = sys.executable
        for command in (
            [python, "-m", "alembic", "upgrade", "head"],
            [python, "-m", "app.seed"],
        ):
            subprocess.run(command, cwd=root / "backend", env=env, check=True)
        processes = []
        with (Path(directory) / "servers.log").open("w+") as log:
            try:
                for command, cwd, url in (
                    (
                        [python, "-m", "uvicorn", "app.main:app", "--port", "8001"],
                        root / "backend",
                        "http://127.0.0.1:8001/api/v1/health",
                    ),
                    (
                        [
                            "node",
                            "node_modules/vite/bin/vite.js",
                            "--host",
                            "127.0.0.1",
                            "--port",
                            "5174",
                            "--strictPort",
                        ],
                        root / "frontend",
                        "http://127.0.0.1:5174/",
                    ),
                ):
                    process = subprocess.Popen(
                        command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT
                    )
                    processes.append(process)
                    ready(url, process)
                subprocess.run(
                    ["npm", "run", "test:e2e"],
                    cwd=root / "frontend",
                    env=env,
                    check=True,
                )
                if args.postman:
                    environment = Path(directory) / "postman-environment.json"
                    environment.write_text(
                        json.dumps(
                            {
                                "name": "Isolated verification",
                                "values": [
                                    {
                                        "key": "base_url",
                                        "value": "http://127.0.0.1:8001/api/v1",
                                        "enabled": True,
                                    },
                                    {
                                        "key": "password",
                                        "value": env["DEMO_PASSWORD"],
                                        "enabled": True,
                                    },
                                ],
                            }
                        )
                    )
                    environment.chmod(0o600)
                    subprocess.run(
                        [
                            "npm",
                            "exec",
                            "--yes",
                            "--package=newman@6.2.3",
                            "--",
                            "newman",
                            "run",
                            str(root / "postman/procurement.postman_collection.json"),
                            "--environment",
                            str(environment),
                            "--bail",
                        ],
                        cwd=directory,
                        check=True,
                    )
            except (subprocess.CalledProcessError, RuntimeError):
                log.seek(0)
                print(
                    "Server diagnostics:\n" + "".join(log.readlines()[-50:]),
                    file=sys.stderr,
                )
                raise
            finally:
                for process in reversed(processes):
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    main()
