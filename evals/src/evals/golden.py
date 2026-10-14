"""Golden sets: versioned YAML files of cases, registered once as MLflow evaluation datasets."""

from pathlib import Path
from typing import Any

import mlflow.genai.datasets
import yaml
from mlflow.genai.datasets import EvaluationDataset
from pydantic import BaseModel


class GoldenSet(BaseModel):
    """One version of a golden set: cases in MLflow's record shape (inputs + expectations)."""

    version: int
    description: str
    cases: list[dict[str, Any]]


def load(folder: Path, version: int) -> GoldenSet:
    """Read one golden set version.

    Args:
        folder: The eval's folder, holding v<n>.yaml files.
        version: Version number.

    Returns:
        The golden set.
    """
    return GoldenSet.model_validate(yaml.safe_load((folder / f"v{version}.yaml").read_text()))


def register(name: str, golden: GoldenSet, experiment_id: str) -> EvaluationDataset:
    """Register a golden set as an MLflow evaluation dataset, or reuse it if that version is already there.

    Args:
        name: Dataset name, including the version, e.g. triage-golden-v1.
        golden: The golden set.
        experiment_id: Experiment the dataset is attached to.

    Returns:
        The MLflow dataset.
    """
    if found := mlflow.genai.datasets.search_datasets(experiment_id, filter_string=f"name = '{name}'"):
        return found[0]
    dataset: EvaluationDataset = mlflow.genai.datasets.create_dataset(  # typed Any by mlflow
        name=name, experiment_id=experiment_id, tags={"description": golden.description}
    )
    dataset.merge_records(golden.cases)
    return dataset
