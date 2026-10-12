# Elasticsearch shopping assistant demo

A recording-ready demonstration of selecting useful model context: fictional shoe catalog
→ Elasticsearch semantic/keyword/hybrid retrieval → structured constraints → relevant
passages → **mandatory OpenAI answer generation**. The application calls OpenAI on each
submitted search, including empty results. It never substitutes a canned answer.

## Prerequisites

- Python 3.11 or newer (3.11.9 was available during development).
- An Elastic Cloud Serverless **Vector Database** project, its HTTPS Elasticsearch
  endpoint, and a project API key. This is different from an organization Cloud API key.
- A provisioned **Jina text_embedding endpoint through Elastic Inference Service**.
  Confirm its exact endpoint ID and model in Kibana; the sample ID is a placeholder
  assumption to verify, not an endpoint the application provisions.
- An OpenAI API key with billing/quota and access to a Responses API structured-output
  model. `gpt-4o-mini` is the configurable starting model, not a claim that it is the newest.
- Outbound HTTPS to your Elastic project, OpenAI, and PyPI for installation.

No local Elasticsearch, Java, Docker, embedding server, or GPU is required. Cloud setup
and model inference can incur charges. Set budgets in both providers before rehearsal.

The setup key needs index creation, document creation, refresh, read, and index metadata
access for the dedicated index, plus inference endpoint inspection/access as required by
your project. Start from project-provided access and scope it using Elastic's API-key UI.
For regular searches, use a key scoped to index reading and the inference access needed
by semantic search. The diagnostics view additionally requires metadata/endpoint access;
do not grant an application key administrative rights merely to make diagnostics work.

## Install on Windows PowerShell

Run from `C:\Projects\elastic-search`. Activation is optional; these commands avoid
PowerShell execution-policy changes:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
Copy-Item -LiteralPath .env.example -Destination .env
```

Copy the example only if `.env` does not already exist. Edit `.env` locally:

```dotenv
ES_URL=https://YOUR-ACTUAL-PROJECT-ENDPOINT:443
ES_API_KEY=YOUR-ELASTIC-PROJECT-KEY
ES_INDEX=shopping-demo-products
ES_INFERENCE_ID=YOUR-CONFIRMED-JINA-ENDPOINT-ID
OPENAI_API_KEY=YOUR-OPENAI-KEY
OPENAI_MODEL=gpt-4o-mini
REQUEST_TIMEOUT=60
```

Never put keys in code, screenshots, or recordings. `.env` is ignored by Git. Existing
environment variables take precedence over `.env`; restart the app after changing settings.

## Create and run the demo

The checked-in data is ready to use. `scripts.generate_catalog` can regenerate it locally.

```powershell
.\.venv\Scripts\python.exe -m scripts.check_setup
.\.venv\Scripts\python.exe -m scripts.create_index
.\.venv\Scripts\python.exe -m scripts.ingest
.\.venv\Scripts\python.exe -m scripts.check_setup --live-answer
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Open the local URL printed by Streamlit (normally `http://127.0.0.1:8501`). The setup
check confirms endpoint identity and OpenAI model visibility; `--live-answer` additionally
makes a small billable generation call to verify the real Responses integration.

Index creation refuses to overwrite an existing index. Ingestion uses `create` operations
with stable product IDs: rerunning it reports HTTP 409 conflicts rather than overwriting
records. After an interrupted ingestion, a rerun creates missing records and reports conflicts
for existing ones; check the index count and evaluation results. For a clean restart, choose
a new `ES_INDEX`. There is no automatic delete/reset command.

## Run the Jupyter notebook

The [preparation, retrieval, and answer notebook](notebooks/retrieval_and_answer.ipynb)
validates the local catalog, previews searchable documents and the index mapping, then
uses the same retrieval and answering modules as the app. Index creation and ingestion
are optional and disabled by default for your existing index. Brief Markdown introductions
explain each group of cells.

From the project folder, install the optional notebook dependency:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[notebook]'
```

Install the **Jupyter** and **Python** extensions in VS Code. Open the notebook, click
**Select Kernel**, choose **Python Environments**, and select the project's
`.venv\Scripts\python.exe`. If it is missing, use **Python: Select Interpreter** in the
Command Palette to select that interpreter, then select the notebook kernel again.
Virtual-environment activation is unnecessary when that kernel is selected.

Run cells from top to bottom. Leave the group 5 creation/upload flags disabled for your
already-ingested index. Edit the question, mode, budget, and size in group 7.
Groups 8 and 10 make real retrieval and OpenAI calls. The optional comparison is disabled
by default; enable its flag to run three extra searches without answer generation.
After editing inputs, rerun groups 7 through 11. Keep credentials in `.env`, never in cells.
Clear all notebook outputs before committing or sharing if they contain private information.
The checked-in notebook has no saved outputs and has not made live API calls.

## Use the interface

1. Inspect the local **Catalog** and a product's size-specific variants.
2. In **Search and answer**, select the city-walking example and semantic retrieval.
3. To demonstrate the budget step, first clear **Apply budget**, search, then enable it
   at $100. Select US size 9 and **In stock only**.
4. Search `WalkLite 200` with keyword and hybrid modes. Each submitted run also generates
   a real OpenAI answer. Compare submitted runs manually; scores across modes are not comparable.
5. Inspect **Retrieved evidence**, **Model context**, **OpenAI answer**, and the actual request.
6. Try the missing-waterproofing and long-guide examples.
7. Use **Elastic configuration** to verify endpoint/model and index settings before recording.

Budget and size are controlled explicitly. The application does not automatically extract
arbitrary constraints from the question. Keep the controls consistent with your wording;
the prompt asks for clarification on conflicts. The submitted filters are always displayed.
Old results remain labeled with their submitted question and controls until a new submission.

## Data and architecture

The dataset contains 60 fictional shoes: 12 base listings and four named edition groups,
with price and inventory variations. Three base listings have longer care/use guides.
Waterproofing can be true, false, or unknown. Variant stock is nested by US size. Names,
descriptions, and guides form `searchable_content`; Elasticsearch creates its chunks and
embeddings. Structured money and stock facts are never inferred from vectors.

Keyword and semantic branches receive identical filters before RRF combines their ranks.
The application then sends up to the selected result count as context; the model returns
at most three recommendations. It cites product IDs and copies an evidence quote. Price
and stock shown next to recommendations come directly from the evidence, not generated text.

The application rejects unknown/duplicate product citations and quotes absent from the
cited passages. This validates citation identity and quote provenance; it does **not**
prove that every generated explanation follows logically from the evidence. Read answers
before recording. Incomplete/refused/invalid responses are errors, never shown as success.
When generation fails, retrieved evidence remains visible and retry requires submission.

`store=False` disables OpenAI response storage for these requests; it is not a statement
that all provider retention is disabled. Each search is an independent question with no
conversation history. No purchasing or stock reservation is implemented.

## Validate

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m scripts.evaluate
# Optional: also generate an OpenAI answer for every evaluation case (billable).
.\.venv\Scripts\python.exe -m scripts.evaluate --answers
```

Offline tests cover the catalog, nested size-stock constraints, currency, incomplete
retrieval, context selection, and structured-answer handling. They use mocked providers;
they do not prove live Elasticsearch compatibility or live answer quality.

The catalog uses a Markdown table to avoid a pandas native DLL blocked by Windows
Application Control on this development machine. Streamlit still installs its normal
dependencies; the application does not use pandas dataframes.

Evaluation writes `reports/evaluation.json` with curated relevance judgments, precision
over returned results (up to five), recall, constraints, and latency. Empty-result cases have
an explicit expectation; relevance metrics are null where undefined. These judgments are
illustrative and should be refined after manually inspecting actual retrieval.

## Troubleshooting

| Symptom | Check |
|---|---|
| Missing configuration | Fill `.env`; remove stale environment-variable overrides |
| HTTP 401 / 403 | Correct service key, project permissions, inference access, billing |
| Endpoint rejected | Must be Jina `text_embedding` on EIS with `service: elastic` |
| HTTP 400 during search | Project support for vector mode, semantic_text, RRF, and semantic highlighting; inspect the displayed request in Kibana |
| HTTP 404 | Correct index, inference ID, project URL, or OpenAI model ID |
| HTTP 429 | Provider quota/rate limits; inspect billing and wait before retrying |
| Ingestion 409 | IDs already exist; inspect count or use a new index |
| Quote validation failure | Model did not copy exact evidence; submit again and inspect the evidence |
| No matches | Budget/size/stock filters may exclude all candidates; inspect source catalog |

Default chunking and vector optimizations are the starting point. Do not force merges or
enable calibration simply for the recording. A 60-product demo is not a benchmark of scale.

## Project map and references

- `src/`: configuration, catalog validation, retrieval, context, mandatory answering, diagnostics.
- `config/`: explicit Elasticsearch mappings.
- `data/`: reproducible fictional catalog and evaluation questions.
- `scripts/`: checks, index creation, ingestion, generation of data, and evaluation.
- `prompts/`: grounding instructions.
- `notebooks/`: step-by-step retrieval and answer workflow using the existing index.
- `tests/`: offline behavior checks.
- `docs/`: architecture, recording walkthrough, Kibana requests.
- `reports/`: generated local evaluation reports (ignored by Git).

See [architecture](docs/architecture.md), [recording walkthrough](docs/recording-walkthrough.md),
and [Kibana requests](docs/kibana-requests.http).

Official references:
- [Elastic Vector Database setup](https://www.elastic.co/docs/solutions/vector-database/get-started)
- [semantic_text configuration](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/semantic-text-reference)
- [Semantic passage retrieval](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/semantic-text-search-retrieval)
- [RRF](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)

