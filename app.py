import streamlit as st

from src.answer import generate_answer
from src.catalog import load_catalog
from src.config import ROOT, load_settings
from src.context import build_context
from src.diagnostics import error_message, inspect_project
from src.elastic_client import create_client
from src.search import Constraints, run_search

st.set_page_config(
    page_title="Find the evidence | Elastic shopping demo", page_icon="👟", layout="wide"
)
st.title("Find the evidence. Then answer.")
st.caption("Fictional shoe catalog · Elasticsearch retrieval · OpenAI answer generation")

with st.sidebar:
    st.header("Demo walkthrough")
    page = st.radio("View", ["Search and answer", "Catalog", "Elastic configuration"])
    st.caption("Searches use indexed availability. This demo does not reserve or purchase stock.")

if page == "Catalog":
    products = load_catalog(ROOT / "data" / "products.jsonl")
    st.subheader(f"{len(products)} fictional products")
    rows = ["| ID | Name | Price (USD) | Category | Waterproof |", "|---|---|---:|---|---|"]
    for p in products:
        weather = (
            "Unknown"
            if p.attributes.waterproof is None
            else ("Yes" if p.attributes.waterproof else "No")
        )
        rows.append(f"| {p.product_id} | {p.name} | {p.price:.2f} | {p.category} | {weather} |")
    with st.expander("Browse the full catalog", expanded=True):
        st.markdown("\n".join(rows))
    selected = st.selectbox("Inspect a product", products, format_func=lambda p: p.name)
    st.json(selected.model_dump())
    st.caption(
        "This view reads the local source catalog. Search uses the ingested Elasticsearch index."
    )
elif page == "Elastic configuration":
    st.subheader("Inspect the actual deployment")
    st.write("Confirm the Jina endpoint and index settings before recording infrastructure claims.")
    if st.button("Inspect configuration"):
        try:
            settings = load_settings()
            with create_client(settings) as client:
                info = inspect_project(client, settings)
            st.json(info)
            st.write(f"Answer provider: OpenAI · configured model: {settings.openai_model}")
            st.caption(
                "Configuration inspection does not prove compression savings or generation access."
            )
        except Exception as exc:
            st.error(error_message(exc))
else:
    examples = {
        "City walking": "Comfortable shoes for walking around New York all day",
        "Specific product": "WalkLite 200",
        "Waterproof shoes": "Which comfortable city walking shoes are waterproof?",
        "Product care": (
            "How should I clean the CityStride Comfort insoles after a long city walk?"
        ),
    }
    st.session_state.setdefault(
        "shopping_question", "Comfortable shoes for walking around New York all day"
    )

    def select_example(example_question):
        st.session_state["shopping_question"] = example_question

    with st.expander("Try an example", expanded=False):
        st.caption("Choose an example to fill the question box, or type your own question below.")
        columns = st.columns(2)
        for index, (label, example_question) in enumerate(examples.items()):
            with columns[index % 2]:
                st.button(
                    label,
                    key=f"example_{index}",
                    on_click=select_example,
                    args=(example_question,),
                )

    with st.form("search"):
        question = st.text_input(
            "What are you looking for?",
            key="shopping_question",
            placeholder="Ask about a product, its features, or care instructions",
        )
        left, middle, right = st.columns(3)
        with left:
            mode = st.selectbox("Retrieval mode", ["semantic", "keyword", "hybrid"])
            limit = st.slider("Products to retrieve", 1, 10, 5)
        with middle:
            budget_on = st.checkbox("Apply budget", True)
            budget = st.number_input("Maximum price (USD)", min_value=0.0, value=100.0, step=5.0)
        with right:
            size = st.selectbox("US size", ["Any", "7", "8", "9", "10", "11", "12"], index=3)
            in_stock = st.checkbox("In stock only", True)
        st.caption(
            "Budget and size come from these controls. Align them with any constraints in your question."
        )
        submitted = st.form_submit_button("Search and generate answer", type="primary")
    if submitted:
        st.session_state.pop("demo_result", None)
        try:
            settings = load_settings()
            constraints = Constraints(
                budget if budget_on else None,
                size=None if size == "Any" else size,
                in_stock=in_stock,
            )
            with st.spinner("Retrieving products from Elasticsearch…"):
                with create_client(settings) as client:
                    result = run_search(
                        client, settings.es_index, question, mode, constraints, limit
                    )
            context = build_context(result)
            st.session_state["demo_result"] = {"result": result, "context": context}
            with st.spinner("Generating a grounded answer with OpenAI…"):
                generated = generate_answer(settings, context)
            st.session_state["demo_result"]["generated"] = generated
        except Exception as exc:
            st.error(error_message(exc))
            if "demo_result" in st.session_state:
                st.warning(
                    "Retrieval succeeded, but answer generation failed. Submit again to retry."
                )
    saved = st.session_state.get("demo_result")
    if saved:
        result, context = saved["result"], saved["context"]
        st.caption(
            f"Showing submitted question: {result['question']} · mode: {result['mode']} · "
            f"filters: {result['constraints']}"
        )
        evidence_tab, answer_tab, context_tab, request_tab = st.tabs(
            ["Retrieved evidence", "OpenAI answer", "Model context", "Elasticsearch request"]
        )
        with evidence_tab:
            st.caption(
                f"Elasticsearch took: {result['es_took_ms']} ms · client elapsed: {result['elapsed_ms']} ms"
            )
            if not result["products"]:
                st.info("No products retrieved under these constraints.")
            for p in result["products"]:
                with st.container(border=True):
                    st.subheader(p["name"])
                    st.write(f"{p['currency']} {p['price']:.2f} · {p['product_id']}")
                    for passage in p["passages"] or [p["description"]]:
                        st.write(passage)
                    st.caption(
                        f"Ranking score: {p['score']}. Scores are not confidence probabilities."
                    )
                    st.json(
                        {"variants": p["variants"], "attributes": p["attributes"]}, expanded=False
                    )
        with answer_tab:
            if "generated" in saved:
                generated = saved["generated"]
                answer = generated["answer"]
                st.write(answer["explanation"])
                sources = {p["product_id"]: p for p in context["products"]}
                for rec in answer["recommendations"]:
                    p = sources[rec["product_id"]]
                    st.subheader(f"{p['name']} · {p['currency']} {p['price']:.2f}")
                    st.write(rec["reason"])
                    st.write(f"Evidence [{rec['product_id']}]: {rec['evidence_quote']}")
                    st.caption(f"Eligible inventory: {p['eligible_variants']}")
                if answer["missing_information"]:
                    st.write("Missing information:")
                    for item in answer["missing_information"]:
                        st.write(f"• {item}")
                st.caption(
                    f"Model: {generated['model']} · generation: {generated['elapsed_ms']} ms"
                )
                with st.expander("Token usage"):
                    st.json(generated["usage"])
            else:
                st.warning(
                    "No generated answer is available. Retry the search after fixing the service error."
                )
        with context_tab:
            st.json(context)
            with st.expander("Answering instructions"):
                st.text((ROOT / "prompts" / "answer.txt").read_text(encoding="utf-8"))
        with request_tab:
            st.json(result["request"])
