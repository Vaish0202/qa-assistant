"""Read and write dataset files, and turn records into pipeline inputs."""
import json
import os

DATASETS_DIR = os.path.dirname(os.path.abspath(__file__))


def dataset_path(name: str) -> str:
    """'v1' -> evaluation/datasets/v1.jsonl"""
    return name if name.endswith(".jsonl") else os.path.join(DATASETS_DIR, f"{name}.jsonl")


def load(name: str, split: str = None) -> list:
    records = []
    with open(dataset_path(name), encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{name} line {line_no}: invalid JSON ({e})")
    if split:
        records = [r for r in records if r.get("split") == split]
    return records


def save(name: str, records: list) -> str:
    path = dataset_path(name)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def to_pipeline_input(record: dict) -> dict:
    """Map a dataset record to run_analysis() arguments."""
    logs = record["log"]
    if record.get("stacktrace"):
        logs = f"{logs}\n{record['stacktrace']}"
    return {
        "testcase_logs": logs,
        "testcase_description": record.get("description", ""),
        "testcase_code": record["code_snippet"],
    }