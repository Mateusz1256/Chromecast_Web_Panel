from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_synology_scripts_exist():
    assert (ROOT / "scripts" / "start.sh").exists()
    assert (ROOT / "scripts" / "stop.sh").exists()
    assert (ROOT / "scripts" / "backup.sh").exists()


def test_start_script_uses_waitress_and_pid_file():
    script = (ROOT / "scripts" / "start.sh").read_text(encoding="utf-8")

    assert "waitress-serve" in script
    assert "cast-panel.pid" in script
    assert "kill -0" in script
    assert "TMPDIR" in script
    assert "nohup" in script


def test_stop_script_uses_pid_file_without_process_grep():
    script = (ROOT / "scripts" / "stop.sh").read_text(encoding="utf-8")

    assert "cast-panel.pid" in script
    assert "kill" in script
    assert "grep" not in script


def test_backup_script_includes_config_and_database():
    script = (ROOT / "scripts" / "backup.sh").read_text(encoding="utf-8")

    assert "instance/config.json" in script
    assert "instance/app.sqlite3" in script
    assert "instance/presets.json" in script
    assert "tar -czf" in script


def test_deployment_docs_describe_script_based_run():
    docs = (ROOT / "docs" / "SCRIPT_DEPLOYMENT.md").read_text(encoding="utf-8")

    assert "Script-Based Deployment" in docs
    assert "Autostart" in docs
    assert "scripts/start.sh" in docs
    assert "scripts/stop.sh" in docs
    assert "scripts/backup.sh" in docs
