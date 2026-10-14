"""The triage prompt eval: run the golden set against one prompt version, then decide by policy."""

import asyncio
import os

import mlflow
from core.adapters.http_gateway import HttpGateway
from core.adapters.mlflow_prompt_store import MlflowPromptStore
from enzo.bootstrap import build_identity_provider
from enzo.config import Settings as AgentSettings
from mlflow.genai.scorers import Scorer

from evals import golden, policy
from evals.policy import Gate
from evals.settings import Settings
from evals.triage.judge import make_judge
from evals.triage.predict import make_predict
from evals.triage.scorers import code_scorers

JUDGE_RULE = ("judge-explains-first", "1")  # pinned: changing the rule is a new eval, not a silent drift
PRODUCTION = "production"


def evaluate_prompt(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    prompt: str, version: int, promote: bool, settings: Settings, agent: AgentSettings
) -> list[Gate]:
    """Run the golden set through the real agent with one prompt version, decide by policy, and maybe promote.

    Args:
        prompt: Name of the prompt under test.
        version: Version number of the prompt under test.
        promote: If the version is certified, point the production alias at it.
        settings: Eval settings.
        agent: The agent's own settings, the base of the agent under test.

    Returns:
        One outcome per gate; the run is tagged certified only if they all pass, and promoted if it moved the alias.
    """
    os.environ["MLFLOW_GENAI_EVAL_MAX_WORKERS"] = "1"  # one local model: parallel cases would only queue and time out
    os.environ["MLFLOW_GENAI_EVAL_SKIP_TRACE_VALIDATION"] = "true"  # skip MLflow's extra trial call of the agent
    folder = settings.dir / "triage"
    rules = policy.load(folder / "policy.yaml")
    predict = make_predict(agent, prompt, version, settings.experiment)  # also points MLflow at the experiment
    experiment_id = mlflow.get_experiment_by_name(settings.experiment).experiment_id  # type: ignore[union-attr]
    dataset = golden.register(f"triage-golden-{rules.golden}", golden.load(folder, int(rules.golden[1:])),
                              experiment_id)
    with mlflow.start_run(run_name=f"{prompt} v{version}"):
        mlflow.log_params({"prompt": prompt, "prompt_version": version, "golden": rules.golden,
                           "judge_rule": "/".join(JUDGE_RULE), "judge_alias": settings.judge_alias})
        mlflow.log_dict(rules.model_dump(), "policy.yaml")
        result = mlflow.genai.evaluate(data=dataset, predict_fn=predict, scorers=_scorers(settings, agent))
        gates = policy.decide(rules, result.metrics)
        failed = [gate.name for gate in gates if not gate.passed]
        mlflow.set_tags({"decision": "blocked" if failed else "certified", "failed_gates": ",".join(failed)})
        if promote and not failed:
            mlflow.genai.set_prompt_alias(prompt, PRODUCTION, version)  # the agent picks it up within a minute
            mlflow.set_tag("promoted", f"{prompt}@{PRODUCTION} -> v{version}")
    return gates


def _scorers(settings: Settings, agent: AgentSettings) -> list[Scorer]:
    """Build the four gates: three code scorers and the LLM judge, with its pinned rule and its own identity.

    Args:
        settings: Eval settings, with the judge's alias and identity.
        agent: The agent's settings, for the identity provider.

    Returns:
        The scorers, named after their gates.
    """
    rule = asyncio.run(MlflowPromptStore().load(*JUDGE_RULE)).text
    identity = build_identity_provider(agent).login(settings.judge_user, settings.judge_agent)
    gateway = HttpGateway(settings.gateway_url, settings.judge_alias)
    return [*code_scorers(), make_judge("explains_first", rule, gateway, identity)]
