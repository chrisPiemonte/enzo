"""The skills eval: route the golden requests over the catalogue, then decide by policy if the registry is sound."""

import asyncio
import os
from pathlib import Path
from typing import Any

import mlflow
import yaml
from core.adapters.http_gateway import HttpGateway
from core.adapters.mlflow_prompt_store import MlflowPromptStore
from core.models.chat import SkillSpec
from core.models.identity import Identity
from core.tracing import setup as setup_tracing
from enzo.bootstrap import build_identity_provider
from enzo.config import Settings as AgentSettings

from evals import golden, policy
from evals.policy import Gate
from evals.settings import Settings
from evals.skills.predict import NONE, Predict, make_predict
from evals.skills.scorers import Confusion, case_scorers, coverage, separation

ROUTER_RULE = ("skill-router", "1")  # pinned, like the judge's rule


def evaluate_skills(candidate: str | None, settings: Settings, agent: AgentSettings) -> tuple[list[Gate], Confusion]:
    """Run the golden requests through one routing call each, logging an MLflow eval run with the confusion matrix.

    Args:
        candidate: Name of a skill from candidates.yaml to add to the catalogue for this run, if any.
        settings: Eval settings.
        agent: The agent's settings, for the identity provider.

    Returns:
        One outcome per gate, and the confusion counts (expected, picked).
    """
    os.environ["MLFLOW_GENAI_EVAL_MAX_WORKERS"] = "1"  # one local model: parallel cases would only queue
    os.environ["MLFLOW_GENAI_EVAL_SKIP_TRACE_VALIDATION"] = "true"  # skip MLflow's extra trial call
    setup_tracing(settings.mlflow_url, settings.experiment, async_logging=False)  # the eval reads its traces back
    folder = settings.dir / "skills"
    rules = policy.load(folder / "policy.yaml")
    cases = golden.load(folder, int(rules.golden[1:]))
    catalogue = _catalogue(candidate, folder, settings, agent)
    picks: dict[str, str] = {}
    predict = _recording(_predict(catalogue, settings, agent), picks)
    experiment_id = mlflow.get_experiment_by_name(settings.experiment).experiment_id  # type: ignore[union-attr]
    with mlflow.start_run(run_name="skills" + (f" + {candidate}" if candidate else "")):
        mlflow.log_params({"golden": rules.golden, "candidate": candidate or "", "router_alias": settings.router_alias,
                           "router_rule": "/".join(ROUTER_RULE)})
        mlflow.log_dict({skill.name: skill.description for skill in catalogue}, "catalogue.yaml")
        result = mlflow.genai.evaluate(data=golden.register(f"skills-golden-{rules.golden}", cases, experiment_id),
                                       predict_fn=predict, scorers=case_scorers())
        confusion = Confusion((case["expectations"]["skill"], picks[case["inputs"]["request"]]) for case in cases.cases)
        gates = policy.decide(rules, {**result.metrics, **_log_confusion(confusion, [s.name for s in catalogue])})
        failed = [gate.name for gate in gates if not gate.passed]
        mlflow.set_tags({"decision": "blocked" if failed else "certified", "failed_gates": ",".join(failed)})
    return gates, confusion


def _catalogue(candidate: str | None, folder: Path, settings: Settings, agent: AgentSettings) -> list[SkillSpec]:
    """List the registered skills from the gateway, plus the candidate if one is given.

    Args:
        candidate: Candidate skill name, or None.
        folder: The skills eval folder, holding candidates.yaml.
        settings: Eval settings.
        agent: The agent's settings.

    Returns:
        The catalogue offered to the router.
    """
    skills = asyncio.run(_gateway(settings).list_tools(_identity(settings, agent)))
    if candidate:
        spec = yaml.safe_load((folder / "candidates.yaml").read_text())[candidate]
        skills.append(SkillSpec(name=candidate, **spec))
    return skills


def _predict(catalogue: list[SkillSpec], settings: Settings, agent: AgentSettings) -> Predict:
    """Build the routing predict function with the pinned router rule.

    Args:
        catalogue: The skills offered as tools.
        settings: Eval settings.
        agent: The agent's settings.

    Returns:
        The predict function.
    """
    rule = asyncio.run(MlflowPromptStore().load(*ROUTER_RULE)).text
    return make_predict(_gateway(settings), _identity(settings, agent), rule, catalogue)


def _recording(predict: Predict, picks: dict[str, str]) -> Predict:
    """Wrap a predict function so each request's pick is kept for the confusion matrix.

    Args:
        predict: The routing predict function.
        picks: Filled with request -> picked skill.

    Returns:
        A predict function with the same signature.
    """

    def recorded(request: str) -> dict[str, Any]:
        """Route one request and remember the pick.

        Args:
            request: The engineer's request.

        Returns:
            The picked skill.
        """
        output = predict(request)
        picks[request] = output["skill"]
        return output

    return recorded


def _log_confusion(confusion: Confusion, skills: list[str]) -> dict[str, float]:
    """Log the confusion matrix as a table, and separation and coverage as metrics of the current run.

    Args:
        confusion: Counts of (expected, picked).
        skills: Every skill in the catalogue.

    Returns:
        The run-wide metrics.
    """
    metrics = {"separation": separation(confusion, skills), "coverage": coverage(confusion, skills)}
    mlflow.log_metrics(metrics)
    mlflow.log_table(_matrix(confusion, [*skills, NONE]), "confusion_matrix.json")
    return metrics


def _matrix(confusion: Confusion, labels: list[str]) -> dict[str, list[Any]]:
    """Lay the confusion counts out as a table: one row per expected skill, one column per picked skill.

    Args:
        confusion: Counts of (expected, picked).
        labels: Row and column labels, in order.

    Returns:
        Columns for mlflow.log_table.
    """
    return {"expected": labels, **{picked: [confusion[(expected, picked)] for expected in labels] for picked in labels}}


def _gateway(settings: Settings) -> HttpGateway:
    """The gateway adapter, bound to the model alias that routes in production.

    Args:
        settings: Eval settings.

    Returns:
        The adapter.
    """
    return HttpGateway(settings.gateway_url, settings.router_alias)


def _identity(settings: Settings, agent: AgentSettings) -> Identity:
    """The eval harness's own identity: it calls models and lists tools, and reads no data.

    Args:
        settings: Eval settings.
        agent: The agent's settings, for the identity provider.

    Returns:
        The signed identity.
    """
    return build_identity_provider(agent).login(settings.judge_user, settings.judge_agent)
