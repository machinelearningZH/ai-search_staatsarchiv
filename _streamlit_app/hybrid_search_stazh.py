import streamlit as st
import time
from datetime import datetime
import os
import weaviate
import weaviate.classes as wvc
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(
    filename="app.log",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.WARNING,
)

st.set_page_config(
    page_title="Zentrale Serien des Kantons Zürich - hybride Suche",
    page_icon="_imgs/wappen.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Suppress Hugginface warning about tokenizers.
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ---------------------------------------------------------------
# Constants

SEARCH_MODE = ("nach Begriffen", "mit Referenzdokument")


# ---------------------------------------------------------------
# Functions


def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("style.css")

# Delete red/yellowish line.
hide_decoration_bar_style = """
    <style>
        header {visibility: hidden;}
    </style>
"""
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)


@st.cache_resource
def get_project_info():
    """Get project info."""
    with open("projectinfo.md") as f:
        return f.read()


@st.cache_resource
def create_project_info(project_info):
    """Create expander for project info."""
    with st.expander("Informationen zum Projekt"):
        st.markdown(project_info, unsafe_allow_html=True)


@st.cache_resource
def instantiate_client():
    """Instantiate Weaviate client."""
    # Set this path to the path where the index is stored.
    # client = weaviate.connect_to_embedded(persistence_data_path="/data01/weaviate_index")

    # Use this line for local testing where the index is stored in the default path.
    client = weaviate.connect_to_embedded()
    return client.collections.get("stazh")


@st.cache_resource
def load_model():
    """Load sentence transformers language model."""
    model_path = "jinaai/jina-embeddings-v2-base-de"
    model = SentenceTransformer(
        model_path,
        trust_remote_code=True,
    )
    model.max_seq_length = 512
    return model


def embed_query(query):
    return model.encode(query, convert_to_tensor=False, normalize_embeddings=True)


def log_interaction(start_time, raw_search_terms):
    """Log interaction."""
    end_time = time.time()
    logging.warning(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\t{end_time - start_time:.3f}\t{raw_search_terms}"
    )


def list_results(final_results):
    """List search results."""
    if sort_by_date:
        final_results = sorted(final_results, key=lambda x: x.properties["date"])

    for result in final_results:
        result = result.properties
        zszh_link = result["link"].replace(
            "www.zentraleserien.zh.ch", "www.zentraleserien.zh.ch/documents"
        )
        if zszh_link.endswith("_t"):
            zszh_link = zszh_link[:-2]
        st.markdown(
            f"**{result['stazh_ident']}** vom **{result['date'].strftime('%d.%m.%Y')}**  ({result['series'].upper()})<br>"
            f'<a href="{zszh_link}" style="color: #00A0E0;">{result["title"]}</a>',
            unsafe_allow_html=True,
        )


def search_by_terms():
    """Search by search terms."""
    start_time = time.time()

    raw_search_terms = []
    search_terms = []

    if search_box != "":
        raw_search_terms = search_box

    if raw_search_terms != []:
        search_terms = raw_search_terms

        vector = embed_query(search_terms)

        response = collection.query.hybrid(
            query=search_terms,
            query_properties=["title", "chunk_text"],
            vector=list(vector),
            limit=top_k,
            alpha=hybrid_balance,
            fusion_type=wvc.query.HybridFusion.RELATIVE_SCORE,
            filters=wvc.query.Filter.by_property("year").greater_or_equal(sl_year[0])
            & wvc.query.Filter.by_property("year").less_or_equal(sl_year[1])
            & wvc.query.Filter.by_property("series").contains_any(include_series),
        )

        seen = []
        final_results = []
        if response.objects is not None:
            for result in response.objects:
                if result.properties["identifier"] in seen:
                    continue
                final_results.append(result)
                seen.append(result.properties["identifier"])

        list_results(final_results)
        log_interaction(start_time, raw_search_terms)


def search_by_reference_document():
    start_time = time.time()

    response = collection.query.fetch_objects(
        filters=wvc.query.Filter.by_property("stazh_ident").equal(signature)
    )

    if response.objects == []:
        st.markdown(
            f"Es existiert kein Dokument mit Signatur **{signature}** in der Datenbank."
        )
        return

    uuid = response.objects[0].uuid

    result = response.objects[0].properties

    st.subheader("Suche mit Referenzdokument")
    st.markdown(
        f'<span style="color: #00A0E0; font-size: 18px;">Referenzdokument:</span>',
        unsafe_allow_html=True,
    )
    zszh_link = result["link"].replace(
        "www.zentraleserien.zh.ch", "www.zentraleserien.zh.ch/documents"
    )
    if zszh_link.endswith("_t"):
        zszh_link = zszh_link[:-2]
    st.markdown(
        f"**{result['stazh_ident']}** vom **{result['date'].strftime('%d.%m.%Y')}**  ({result['series'].upper()})<br>"
        f'<a href="{zszh_link}" style="color: #00A0E0;">{result["title"]}</a>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    response = collection.query.near_object(
        near_object=uuid,
        limit=top_k,
        filters=wvc.query.Filter.by_property("year").greater_or_equal(sl_year[0])
        & wvc.query.Filter.by_property("year").less_or_equal(sl_year[1])
        & wvc.query.Filter.by_property("series").contains_any(include_series),
    )

    # The first result is the reference document itself.
    responses = response.objects[1:]

    seen = []
    final_results = []
    for result in responses:
        if result.properties["stazh_ident"] in seen:
            continue
        final_results.append(result)
        seen.append(result.properties["stazh_ident"])

    list_results(final_results)
    log_interaction(start_time, signature)


# ---------------------------------------------------------------
# Main

model = load_model()
collection = instantiate_client()
project_info = get_project_info()


# Create sidebar.
with st.sidebar:
    st.image("_imgs/ktzh_StAZH_stempel_2-zeilig.png", width=250)
    st.markdown(
        "<h3 style='font-size:21px;'>Zentrale Serien des Kantons Zürich (19. und 20. Jahrhundert)</h3>",
        unsafe_allow_html=True,
    )
    create_project_info(project_info)
    search_mode = st.radio("Suche...", SEARCH_MODE)
    st.markdown("---")

    if search_mode == SEARCH_MODE[0]:
        # st.markdown("---")
        hybrid_balance = st.slider(
            "Balance lexikalisch / semantisch",
            value=0.7,
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            help="Verhältnis zwischen semantischer und lexikalischer Suche. Je höher der Wert, desto mehr semantische Ergebnisse werden angezeigt. Ein guter Standardwert ist 0.75",
        )
    else:
        signature = st.text_input(
            "Signatur des Referenzdokuments:", "StAZH MM 1.5 RRB 1804/0001"
        )
    st.markdown("---")
    sl_year = st.slider(
        "Publikationsjahr", value=[1803, 2001], min_value=1803, max_value=2001
    )
    st.markdown("---")
    include_os = st.toggle(
        "Gesetzessammlung (OS)",
        value=True,
    )
    include_abl = st.toggle(
        "Amtsblatt (ABL)",
        value=True,
    )
    include_krp = st.toggle(
        "Kantonsratsprotokolle (KRP)",
        value=True,
    )
    include_rrb = st.toggle(
        "Regierungsratsbeschlüsse (RRB)",
        value=True,
    )

    st.markdown("---")
    top_k = st.slider(
        "Anzahl Suchergebnisse",
        value=50,
        min_value=5,
        max_value=200,
        help="Anzahl der Suchergebnisse, die angezeigt werden.",
    )
    sort_by_date = st.toggle(
        "Nach Datum sortieren",
        value=False,
        help="Dieser Modus sortiert die Suchergebnisse nach Datum.",
    )

include_series = []
if include_krp:
    include_series.append("krp")
if include_rrb:
    include_series.append("rrb")
if include_os:
    include_series.append("os")
if include_abl:
    include_series.append("abl")
if include_series == []:
    st.error(
        "Bitte mindestens eine Serie in den Einstellungen auswählen (Gesetzessammlung, Amtsblatt, Kantonsratsprotokolle, Regierungsratsbeschlüsse)."
    )
    st.stop()

# Search either by terms or reference document.
if search_mode == SEARCH_MODE[0]:
    st.subheader("Hybride Suche nach Begriffen")
    search_box = st.text_input(
        "Suchbegriffe oder ganze Suchsätze eingeben...",
        value="Was hat der Kantonsrat zu den Themen 'Schulhaus' und 'Schulraum' beschlossen?",
        max_chars=5000,
    )
    st.markdown("---")

if search_mode == "nach Begriffen":
    search_by_terms()
else:
    search_by_reference_document()
