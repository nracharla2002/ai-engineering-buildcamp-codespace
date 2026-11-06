import glob
import json
import os

import streamlit as st

from recipe_agent import instructions as agent_instructions


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_labeled_path(input_path):
    base, ext = os.path.splitext(input_path)
    return f"{base}_labeled{ext}"


def find_next_unlabelled(data, start_index):
    for offset in range(1, len(data)):
        index = (start_index + offset) % len(data)
        if data[index].get("label") is None:
            return index
    return None


st.set_page_config(layout="wide", page_title="Recipe Evaluation Labeling")
st.markdown('<div id="scroll-top-anchor"></div>', unsafe_allow_html=True)

if st.session_state.get("_scroll_top", False):
    st.session_state._scroll_top = False
    st.components.v1.html(
        """<script>
        window.parent.document.getElementById('scroll-top-anchor')?.scrollIntoView(
          {behavior: 'instant', block: 'start'});
        </script>""",
        height=0,
    )

# Only offer runner output files, not recipes.json or previously labeled copies.
result_files = sorted(
    path
    for path in glob.glob(os.path.join(CURRENT_DIR, "results*.json"))
    if not path.endswith("_labeled.json")
)

st.sidebar.header("📂 File Selection")
if not result_files:
    st.error("No results*.json files found. Run run_scenarios.py first.")
    st.stop()

selected_file = st.sidebar.selectbox(
    "Select evaluation results",
    result_files,
    format_func=os.path.basename,
    key="file_selector",
)
labeled_file = get_labeled_path(selected_file)

if st.session_state.get("selected_file") != selected_file:
    st.session_state.selected_file = selected_file
    st.session_state.data = load_data(
        labeled_file if os.path.exists(labeled_file) else selected_file
    )
    for item in st.session_state.data:
        item.setdefault("label", None)
        item.setdefault("comments", "")
    st.session_state.current_index = next(
        (i for i, item in enumerate(st.session_state.data) if item["label"] is None),
        0,
    )

if not st.session_state.data:
    st.error(f"No evaluation results found in {os.path.basename(selected_file)}.")
    st.stop()

st.sidebar.header("🧭 Navigation")
selection = st.sidebar.selectbox(
    "Select result",
    range(len(st.session_state.data)),
    index=st.session_state.current_index,
    format_func=lambda i: (
        f"{'✅' if st.session_state.data[i].get('label') == 'good' else '❌' if st.session_state.data[i].get('label') == 'bad' else '⬜'} "
        f"Run {i + 1}: {st.session_state.data[i].get('question', 'No question')[:40]}..."
    ),
)

if selection != st.session_state.current_index:
    st.session_state.current_index = selection
    st.session_state._scroll_top = True
    st.rerun()

labeled_count = sum(item.get("label") is not None for item in st.session_state.data)
st.sidebar.progress(labeled_count / len(st.session_state.data))
st.sidebar.text(f"Labeled: {labeled_count} / {len(st.session_state.data)}")

if labeled_count == len(st.session_state.data):
    st.success("🎉 Everything is labeled!")

item = st.session_state.data[st.session_state.current_index]
st.title(f"Run {st.session_state.current_index + 1} / {len(st.session_state.data)}")

st.subheader("❓ User Question")
st.chat_message("user").write(item.get("question", "No question found."))

st.subheader("📝 Agent Answer")
st.chat_message("assistant").markdown(item.get("output", "No answer found."))

meta1, meta2, meta3, meta4 = st.columns(4)
meta1.metric("Category", item.get("category", "N/A"))
meta2.metric("Scenario type", item.get("type", "N/A"))
meta3.metric("Execution time", f"{item.get('execution_time', 0)} s")
meta4.metric("Estimated cost", f"${item.get('cost', 0):.6f}")

tokens = item.get("tokens", {})
if tokens:
    st.caption(
        f"Tokens — input: {tokens.get('input_tokens', 0)}, "
        f"output: {tokens.get('output_tokens', 0)}, "
        f"total: {tokens.get('total_tokens', 0)}"
    )

st.subheader("📋 Agent Instructions")
with st.expander("View system instructions"):
    st.markdown(agent_instructions)

st.divider()
st.subheader("⚖️ Labeling Decision")
label_col, comments_col = st.columns([1, 2])

with label_col:
    choices = ["Not Selected", "Good", "Not Good"]
    current_label = item.get("label")
    selected_choice = {"good": "Good", "bad": "Not Good"}.get(
        current_label, "Not Selected"
    )
    decision = st.radio(
        "Is this run good?",
        choices,
        index=choices.index(selected_choice),
        key=f"radio_{st.session_state.current_index}",
    )

with comments_col:
    comments = st.text_area(
        "Comments",
        value=item.get("comments", ""),
        height=100,
        key=f"comments_{st.session_state.current_index}",
    )

if st.button("💾 Save Label & Next", type="primary"):
    item["label"] = {"Good": "good", "Not Good": "bad"}.get(decision)
    item["comments"] = comments
    save_data(st.session_state.data, labeled_file)

    next_index = find_next_unlabelled(
        st.session_state.data, st.session_state.current_index
    )
    if next_index is not None:
        st.session_state.current_index = next_index
    st.session_state._scroll_top = True
    st.rerun()

st.sidebar.divider()
if st.sidebar.button("RESET LABELS"):
    if os.path.exists(labeled_file):
        os.remove(labeled_file)
    st.session_state.pop("data", None)
    st.session_state.pop("current_index", None)
    st.session_state.pop("selected_file", None)
    st.rerun()
