from pathlib import Path

import streamlit as st

from manuscript_parser import (
    read_manuscript,
    split_chapters_into_passages,
    split_into_chapters,
)
from qa import answer_question, has_api_key
from retriever import build_index, keyword_search, search_index
from storage import list_projects, load_project, save_project


st.set_page_config(
    page_title="Story Thread Tracker",
    page_icon=":material/menu_book:",
    layout="wide",
)


def set_active_project(project):
    st.session_state["active_project"] = project


def get_active_project():
    return st.session_state.get("active_project")


st.title("Story Thread Tracker")
st.write(
    "Upload a manuscript, build local story memory, ask questions, "
    "and inspect the exact chapter passages behind each answer."
)

with st.sidebar:
    st.header("Saved projects")
    projects = list_projects()

    if not projects:
        st.caption("No saved projects yet.")
    else:
        project_options = {
            f"{project['project_name']} ({project['chapter_count']} chapters)": project[
                "project_id"
            ]
            for project in projects
        }
        selected_label = st.selectbox("Open a project", list(project_options.keys()))

        if st.button("Load project"):
            set_active_project(load_project(project_options[selected_label]))
            st.success("Project loaded.")

    st.divider()
    if has_api_key():
        st.success("AI answers enabled")
    else:
        st.info("No API key found. Search still works locally.")

uploaded_file = st.file_uploader(
    "Upload your manuscript",
    type=["docx", "txt"],
)

if uploaded_file is not None:
    default_name = Path(uploaded_file.name).stem.replace("_", " ").title()
    project_name = st.text_input("Project name", value=default_name)

    if st.button("Build story memory", type="primary"):
        try:
            manuscript_text = read_manuscript(uploaded_file, uploaded_file.name)

            if not manuscript_text.strip():
                st.error("The manuscript appears to be empty.")
                st.stop()

            chapters = split_into_chapters(manuscript_text)
            passages = split_chapters_into_passages(chapters)

            semantic_index = None
            with st.spinner("Building local search memory..."):
                try:
                    semantic_index = build_index(passages)
                    st.success("Semantic search index built locally.")
                except Exception as error:
                    st.warning(
                        "Semantic search could not be built, so this project "
                        "will use keyword search for now."
                    )
                    st.caption(str(error))

            metadata = save_project(
                project_name=project_name,
                manuscript_filename=uploaded_file.name,
                chapters=chapters,
                passages=passages,
                index=semantic_index,
            )

            set_active_project(
                {
                    "metadata": metadata,
                    "chapters": chapters,
                    "passages": passages,
                    "index": semantic_index,
                }
            )

        except Exception as error:
            st.error(f"Could not read this manuscript: {error}")

project = get_active_project()

if project is None:
    st.caption("Upload a Word or text manuscript, then build story memory.")
    st.stop()

metadata = project["metadata"]
chapters = project["chapters"]
passages = project["passages"]
index = project["index"]

st.success(
    f"Loaded {metadata['project_name']}: "
    f"{metadata['chapter_count']} chapter(s), "
    f"{metadata['passage_count']} searchable passage(s)."
)

metric_columns = st.columns(3)
metric_columns[0].metric("Chapters", metadata["chapter_count"])
metric_columns[1].metric("Passages", metadata["passage_count"])
metric_columns[2].metric(
    "Search mode",
    "Semantic" if metadata.get("has_semantic_index") else "Keyword",
)

st.subheader("Ask a question")
question = st.text_input(
    "What do you want to know?",
    placeholder="Example: Which chapter mentions the ancient god?",
)

if question.strip():
    top_k = st.slider("Evidence passages to retrieve", min_value=3, max_value=10, value=5)

    with st.spinner("Searching the manuscript..."):
        if index is not None:
            results = search_index(index, question, top_k=top_k)
        else:
            results = keyword_search(passages, question, top_k=top_k)

    if not results:
        st.warning(
            "I could not find matching evidence. Try a character name, place, "
            "object, event, or exact phrase from the manuscript."
        )
    else:
        if has_api_key():
            with st.spinner("Writing an evidence-based answer..."):
                try:
                    ai_answer = answer_question(question, results)
                    if ai_answer:
                        st.markdown("### Answer")
                        st.write(ai_answer)
                except Exception as error:
                    st.warning("AI answering failed, but the evidence is still shown below.")
                    st.caption(str(error))
        else:
            st.info(
                "Add an OpenAI API key in `.env` to generate a written answer. "
                "For now, here are the best matching passages."
            )

        st.markdown("### Supporting passages")
        for result in results:
            label = (
                f"[{result.source_id}] {result.chapter_title} "
                f"- passage {result.passage_number} "
                f"- score {result.score}"
            )
            with st.expander(label):
                st.write(result.text)

st.subheader("Browse manuscript")

for chapter in chapters:
    label = f"{chapter['title']} - {chapter['word_count']} words"
    with st.expander(label):
        st.text(str(chapter["text"])[:5000])
        if len(str(chapter["text"])) > 5000:
            st.caption("Only the first 5,000 characters are shown.")
