<p align="center">
    <img src="data/resources/images/flask.png" width="120"/>
</p>

<h1 align="center"> Enzo </h1>

<p align="center"><b>A small, real slice of a vendor-neutral agent plane: field service triage.</b><br/>
Fully local · no API keys · synthetic data only</p>

---

## What it is

A service engineer asks why an instrument shows a fault. The **triage agent** gathers evidence from three **MCP
skills** (telemetry, service history, manuals), proposes a part, and hands the order to a **parts agent over A2A**,
which asks the engineer to approve it. Around that agent sits the **harness**:

| Brief requirement | Where to see it |
|---|---|
| Distinct MCP skills | `services/mcp-telemetry`, `mcp-history`, `mcp-manuals`: one data product each |
| Model gateway, two providers | `services/gateway`: OpenAI- and Anthropic-format adapters; the swap is one line of `gateway.yaml` |
| Identity that survives the hop | a signed **user** token and **agent** token on every call, checked at each data source |
| Audit and lineage | every question is one MLflow trace across agent, gateway and services, linked to the prompt version used |
| Eval harness with gates | `uv run evals …`: golden sets, gates, a policy file, promotion of the `production` prompt |
| A2A hand-off | `services/parts-agent`: proposes an order, waits for the engineer's approval |
| Deliberate stubs | marked `# STUB:` / `# MOCK:` in the code |

```
            ┌──────────────► Ollama  (qwen3:4b, called in OpenAI and Anthropic format)
enzo ──► gateway ──────────► mcp-telemetry · mcp-history · mcp-manuals
(shell)     └──────────────► parts-agent (A2A, asks for approval)
        MLflow: traces · prompt registry · eval datasets and runs
```

## Install

Needs only **git, [uv](https://docs.astral.sh/uv/), Python 3.13 and Docker Compose**.

```bash
git clone https://github.com/chrisPiemonte/enzo.git && cd enzo
cp .env.template .env
docker compose up -d --build     # first run: builds the images and downloads the model (~2.5 GB)
uv sync
```

Check that everything is up (the `ollama-pull` and `prompts-sync` jobs exit with code 0 when done):

```bash
docker compose ps -a
```

> **Speed.** By default the model runs in the Ollama container, on CPU: it works anywhere but takes ~30 s to 2 min
> per model turn. With [Ollama](https://ollama.com) installed natively (much faster, e.g. on a Mac's GPU), run
> `ollama pull qwen3:4b`, set `GATEWAY_DOCKER_OLLAMA_URL=http://host.docker.internal:11434` in `.env`
> (on Linux, also map `host.docker.internal` to `host-gateway`), then `docker compose up -d gateway`.

## Use

```bash
uv run enzo                      # the triage shell
AGENT_GATEWAY=mock uv run enzo   # the same shell fully offline, with a scripted model
```

Type a question, or a command: `/login <user>`, `/agent <agent>`, `/help`, `/exit`.
Users and agents are in `data/context/identity.yaml`.

| Try | What happens |
|---|---|
| `SN-1001 keeps showing error E42. What is wrong?` | telemetry, history and manual are read; part P-123; the parts agent asks *approve or reject* |
| `/login tom`, then the same question | **denied**: Tom's account is Bluefen, SN-1001 belongs to Novacrest |
| `/agent intern`, then any question | **denied**: the intern agent may read manuals only. Permission = user ∩ agent |

**Traces:** http://localhost:5001, experiment `enzo`. Each question shows every hop and the prompt version used.

**Provider swap:** in `services/gateway/gateway.yaml`, change the `provider` of `triage-default` from
`ollama-openai` to `ollama-anthropic`, then `docker compose restart gateway`. Nothing else changes.

## Evals

```bash
uv run evals skills                                     # is the skill registry sound?           (~1–5 min)
uv run evals skills --candidate get_instrument_status   # may this new skill join the registry?
uv run evals prompt triage-system 5                     # is prompt v5 fit for production?       (~10–30 min)
uv run evals prompt triage-system 5 --promote           # ...and if certified, make it production
```

- **Skills eval.** 13 labelled requests; the model picks a tool from the descriptions alone. Gates: **accuracy**,
  **separation** (no two skills confused) and **coverage** (no useless skill). The candidate `get_instrument_status`
  overlaps telemetry and is **blocked**: the confusion matrix shows why.
- **Prompt eval.** 5 golden questions through the real agent. Gates: **grounding** (the right part *for this model*:
  P-456 is a real part that fits the other model), **evidence**, **history** use, and **explains_first**, an LLM judge
  that also goes through the gateway. The decision comes from `policy.yaml`, not from a person.
- Results: MLflow, experiment `evals` → *Evaluation runs* (one row per case, with each gate's reason).
- Everything is versioned in `data/context/`: prompts (synced to the MLflow prompt registry), golden sets, policies.

> These are single runs of a small, non-deterministic model: read a result as a sample, not a measurement. The
> current prompt versions are blocked on purpose by gates they fail; that is the point of the demo.

## Layout

| Folder | Contents |
|---|---|
| `enzo/` | the triage agent (build context → think → act) and its shell |
| `core/` | shared models, ports, adapters, signed identities, tracing |
| `services/` | `gateway`, `mcp-*`, `parts-agent`, `prompts-sync` (each its own container) |
| `evals/` | the eval harness |
| `data/context/` | prompts, golden sets, policies, identities |

## Known limits

- The identity provider is a **stub**: anyone may log in as anyone, and tokens never expire.
- MCP tool bodies return canned records (`# MOCK:`); manual search is a substring match, not retrieval.
- The audit log lives in memory and `/replay` is not built yet; MLflow traces are the record today.
- A small local model is slow and sometimes takes a different path for the same question.
