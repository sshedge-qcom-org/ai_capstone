import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_staging_configuration_is_private_separate_and_never_overwritten(tmp_path):
    root = Path(__file__).resolve().parents[2]
    script = tmp_path / "scripts/configure_staging.py"
    script.parent.mkdir()
    shutil.copyfile(root / "scripts/configure_staging.py", script)
    development = tmp_path / ".env"
    development.write_text("JWT_SECRET=unchanged-development-configuration\n")
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    staging = tmp_path / "deploy/runtime/staging.env"
    content = staging.read_text()
    assert "ENVIRONMENT=production\n" in content
    assert "COOKIE_SECURE=true\n" in content
    secret = next(
        line.split("=", 1)[1] for line in content.splitlines() if line.startswith("JWT_SECRET=")
    )
    assert len(secret) >= 32 and secret not in result.stdout
    assert os.stat(staging).st_mode & 0o777 == 0o600
    assert os.stat(staging.parent).st_mode & 0o777 == 0o700
    repeated = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert repeated.returncode != 0
    assert staging.read_text() == content
    assert development.read_text() == "JWT_SECRET=unchanged-development-configuration\n"
