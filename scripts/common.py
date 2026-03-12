from __future__ import annotations

import json
import logging
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


DEFAULT_PROJECT_STATE = {
    "project": "astro1",
    "status": "initialized",
    "summary": "",
    "current_phase": None,
    "phases": {
        "data_collection": {"status": "pending"},
        "preprocessing": {"status": "pending"},
        "embedding": {"status": "pending"},
        "anomaly_detection": {"status": "pending"},
        "raw_object_scan": {"status": "pending"},
    },
}

DEFAULT_DATASET_STATE = {
    "source": "SDSS_DR19_SkyServer",
    "selection_criteria": {
        "object_type": "galaxy",
        "photoobj_flags": "CLEAN",
        "sample_size_target": 5000,
    },
    "fields": ["ra", "dec", "objid", "petroMag_r", "petroR50_r"],
    "download_batches": [],
    "validation_passed": False,
    "total_downloaded": 0,
}

DEFAULT_METHOD_STATE = {
    "embedding_method": None,
    "anomaly_detection": {},
}


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_config_path(project_root: Path | None = None) -> Path:
    root = project_root or get_project_root()
    env_path = os.environ.get("ASTRO1_CONFIG")
    if not env_path:
        return root / "config.yaml"
    path = Path(env_path)
    if path.is_absolute():
        return path
    return root / path


def load_config(project_root: Path | None = None) -> tuple[Path, dict[str, Any]]:
    root = project_root or get_project_root()
    config_path = get_config_path(root)
    with open(config_path, "r") as f:
        return root, yaml.safe_load(f)


def setup_logger(script_path: str | Path, config: dict[str, Any], project_root: Path) -> logging.Logger:
    script_name = Path(script_path).stem
    log_dir = project_root / config["paths"]["logs"]
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / f"{script_name}.log"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(script_name)


def ensure_json(path: Path, default_data: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    data = deepcopy(default_data)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return data


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def ensure_project_state(memory_dir: Path) -> dict[str, Any]:
    return ensure_json(memory_dir / "project_state.json", DEFAULT_PROJECT_STATE)


def ensure_dataset_state(memory_dir: Path) -> dict[str, Any]:
    return ensure_json(memory_dir / "dataset_state.json", DEFAULT_DATASET_STATE)


def ensure_method_state(memory_dir: Path) -> dict[str, Any]:
    return ensure_json(memory_dir / "method_state.json", DEFAULT_METHOD_STATE)


def update_project_state(memory_dir: Path, phase: str, status: str) -> dict[str, Any]:
    project_state = ensure_project_state(memory_dir)
    project_state.setdefault("phases", {})
    project_state["phases"].setdefault(phase, {})
    project_state["phases"][phase]["status"] = status
    if status == "in_progress":
        project_state["current_phase"] = phase
        project_state["status"] = "running"
    elif status == "completed":
        phases = project_state.get("phases", {})
        if phases and all(item.get("status") == "completed" for item in phases.values()):
            project_state["status"] = "completed"
    save_json(memory_dir / "project_state.json", project_state)
    return project_state
