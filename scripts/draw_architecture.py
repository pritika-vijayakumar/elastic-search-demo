"""Render the report architecture as a high-resolution PNG using Pillow."""
from pathlib import Path
from math import atan2, cos, sin

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 2700, 2790
im = Image.new("RGB", (W, H), "#F5F7FB")
d = ImageDraw.Draw(im)
FONT = Path("C:/Windows/Fonts")


def font(size, bold=False):
    return ImageFont.truetype(str(FONT / ("segoeuib.ttf" if bold else "segoeui.ttf")), size)


def text(x, y, value, size=29, color="#344054", bold=False):
    d.multiline_text((x, y), value, font=font(size, bold), fill=color, spacing=13)


def arrow(points, color="#667085", width=5):
    d.line(points, fill=color, width=width, joint="curve")
    a, b = points[-2:]
    angle = atan2(b[1] - a[1], b[0] - a[0])
    tips = [(b[0] - 19 * cos(angle - delta), b[1] - 19 * sin(angle - delta))
            for delta in (-0.5, 0.5)]
    d.polygon([b, *tips], fill=color)


def card(x, y, title, subtitle, lines, color, height=390):
    d.rounded_rectangle((x, y, x + 590, y + height), radius=20,
                        fill="white", outline="#D9E0EA", width=2)
    d.rounded_rectangle((x, y, x + 590, y + 10), radius=4, fill=color)
    text(x + 24, y + 32, title, 34, "#172B4D", True)
    text(x + 24, y + 90, subtitle, 25, color, True)
    for n, line in enumerate(lines):
        text(x + 24, y + 151 + n * 48, line, 28)


def lane(y, number, title, description, color):
    d.rounded_rectangle((60, y, 116, y + 56), radius=12, fill=color)
    text(77, y + 6, str(number), 30, "white", True)
    text(135, y - 2, title, 40, "#172B4D", True)
    text(135, y + 61, description, 27)


xs = [60, 725, 1390, 2055]
blue, teal, purple = "#2563EB", "#008578", "#7552C5"
text(60, 45, "Elasticsearch Shopping Assistant", 62, "#172B4D", True)
text(60, 135, "Detailed implementation architecture  |  Semantic + hybrid retrieval with mandatory OpenAI answers", 31)
text(60, 194, "Solid arrows: data flow     •     Blue: preparation     •     Teal: retrieval     •     Purple: answering", 27)

lane(290, 1, "Preparing the data", "One-time setup and ingestion • embeddings are generated inside the managed Elastic workflow", blue)
y = 415
card(xs[0], y, "Fictional product catalog", "data/products.jsonl", [
    "60 shoes with stable product IDs",
    "Names, descriptions and guides",
    "Price + USD currency",
    "US-size variants + stock",
    "Waterproof: true / false / unknown"], blue, 430)
card(xs[1], y, "Validate and bulk ingest", "src/catalog.py • scripts/ingest.py", [
    "Pydantic schema validation",
    "Reject duplicate IDs / variants",
    "Assemble searchable_content",
    "Bulk create with stable IDs",
    "Existing records are not overwritten"], blue, 430)
card(xs[2], y, "Chunk and embed", "Elasticsearch semantic_text + EIS", [
    "Default managed text chunking",
    "Configured inference endpoint",
    "Jina text embedding model",
    "Managed inference infrastructure",
    "No application model server"], blue, 430)
card(xs[3], y, "Product index", "config/products-index.json", [
    "shopping-demo-products",
    "Text + internal passage vectors",
    "Structured price and currency",
    "Nested size-and-stock variants",
    "index.mode: vectordb_document"], blue, 430)
for i in range(3):
    arrow([(xs[i] + 590, y + 210), (xs[i + 1], y + 210)], blue)

# The search engine reads the prepared index; the route stays outside the cards.
arrow([(2350, 845), (2350, 905), (1685, 905), (1685, 1055)], blue)
text(1880, 917, "Prepared index used by search", 24, blue)
lane(935, 2, "Finding relevant evidence", "Every submitted question • constraints are applied inside retrieval, before hybrid ranks are combined", teal)
y = 1065
card(xs[0], y, "User / Streamlit interface", "app.py • local or hosted Streamlit", [
    "Free-form question",
    "Keyword / semantic / hybrid mode",
    "Budget and size controls",
    "In-stock filter; result count",
    "Examples only fill the question"], teal, 430)
card(xs[1], y, "Build search request", "src/search.py • elastic_client.py", [
    "Authenticate with Elastic API key",
    "Currency + price filters",
    "Size and stock in SAME variant",
    "Same filters in both branches",
    "One Elasticsearch search request"], teal, 430)
card(xs[2], y, "Elasticsearch retrieval", "Managed Elastic Cloud Serverless", [
    "Keyword: multi_match / BM25",
    "Semantic: match on semantic_text",
    "Query embedding via EIS / Jina",
    "Hybrid: reciprocal rank fusion",
    "Return top products + passages"], teal, 430)
card(xs[3], y, "Select model context", "src/search.py → src/context.py", [
    "Reject partial / ineligible results",
    "Relevant semantic fragments",
    "Description fallback for keywords",
    "IDs, prices, eligible variants",
    "Unknown attributes stay unknown"], teal, 430)
for i in range(3):
    arrow([(xs[i] + 590, y + 210), (xs[i + 1], y + 210)], teal)
arrow([(2350, 1495), (2350, 1555), (25, 1555), (25, 1965), (60, 1965)], teal)
text(970, 1570, "Selected evidence + question + active constraints", 26, teal)

lane(1625, 3, "Generate and validate the answer", "Mandatory OpenAI call after successful retrieval, including no-match cases • no canned-answer fallback", purple)
y = 1755
card(xs[0], y, "Grounding instructions", "prompts/answer.txt • src/context.py", [
    "Use only supplied evidence",
    "Catalog text is untrusted data",
    "Do not invent missing attributes",
    "Clarify conflicting constraints",
    "No matches → no recommendations"], purple, 430)
card(xs[1], y, "OpenAI answer generation", "src/answer.py • Responses API", [
    "OPENAI_MODEL (configurable)",
    "Default: gpt-4o-mini",
    "Structured Pydantic output",
    "Response storage: store=False",
    "Answer + recommendations + gaps"], purple, 430)
card(xs[2], y, "Validate returned answer", "src/answer.py • validate_grounding", [
    "Require completed response",
    "At most 3 recommendations",
    "Known, unique product citations",
    "Exact quote in cited passage",
    "Invalid answer → visible error"], purple, 430)
card(xs[3], y, "Display reviewable output", "app.py • Streamlit session state", [
    "Evidence and generated answer",
    "Prices / stock from source facts",
    "Context and request inspection",
    "Timing and OpenAI token usage",
    "Keep evidence if generation fails"], purple, 430)
for i in range(3):
    arrow([(xs[i] + 590, y + 210), (xs[i + 1], y + 210)], purple)

text(60, 2250, "Cross-cutting configuration, operations and evaluation", 37, "#172B4D", True)
for x, title, body in [
    (60, "Configuration and access", "src/config.py • .env locally / Cloud Secrets\nElastic + OpenAI keys remain server-side\nPrivate review access configured at hosting\nTimeouts and retries; no secrets in this figure"),
    (945, "Setup and evaluation", "check_setup → create_index → ingest\nsrc/diagnostics.py inspects real settings\n15 curated retrieval evaluation cases\nreports/evaluation.json + offline tests"),
    (1830, "Managed vector capabilities", "Vector mode configured; field defaults apply\nBBQ / DiskBBQ: deployment-dependent\nDiskBBQ not explicitly selected by this app\nauto_calibrate is not enabled in this project"),
]:
    d.rounded_rectangle((x, 2320, x + 815, 2615), radius=18, fill="#EAF0F8")
    text(x + 24, 2345, title, 31, "#172B4D", True)
    text(x + 24, 2408, body, 26)
text(60, 2660, "Limits: indexed availability is not a reservation. Citation checks verify provenance, not complete factual entailment.", 27)
text(60, 2710, "The 60-product demo does not benchmark scale, quantization savings, or production recall. Hosting is optional; retrieval stays in Elastic.", 25)

out = ROOT / "docs" / "assets" / "elasticsearch-project-architecture.png"
out.parent.mkdir(parents=True, exist_ok=True)
im.save(out, dpi=(300, 300))
print(out)
