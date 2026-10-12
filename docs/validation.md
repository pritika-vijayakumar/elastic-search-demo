# Validation status

Local validation completed on 2026-10-11:

- Python 3.11.9 virtual environment created and project dependencies installed.
- 18 offline tests passed, including Streamlit catalog rendering, submitted search and
  answer rendering, empty-retrieval generation, generation-failure evidence retention,
  nested variant eligibility, currency constraints, context selection, citation/quote
  rejection, and actual OpenAI SDK structured-response parsing with mocked HTTP.
- Ruff checks passed and Python source was formatted.
- pip dependency checks found no broken requirements.
- Generated and validated 60 fictional products and 15 evaluation cases.
- Setup command correctly reports missing configuration rather than attempting requests
  with placeholders.

Live Elasticsearch endpoint identity, ingestion, retriever/highlighter compatibility,
OpenAI generation access, retrieval rankings, and answer quality have **not** been verified:
Elastic and OpenAI credentials were not configured. Run the README setup sequence and
evaluation against the provisioned project before recording. No cloud project was provisioned,
no catalog was ingested remotely, and no real model call was made during local validation.

Windows Application Control blocked pandas' ccalendar DLL during catalog rendering, even
outside the sandbox. The application uses a Markdown catalog table, which passed the UI
test and does not need that component. Security policy was not changed.
