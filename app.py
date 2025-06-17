import streamlit as st
import pandas as pd
import io

# Import all functions from the single toolkit file
try:
    from Tools.toolkit_functions import (
        clean_tmx_content, 
        split_mqxliff_content,
        run_full_qa
    )
except ImportError as e:
    st.error(f"""
    **Error loading tool modules: {e}**
    This usually means the `Tools` folder or its `__init__.py` file is missing from your GitHub repository.
    Please ensure your repository structure is correct.
    """)
    st.stop()

# --- Page Configuration ---
st.set_page_config(
    page_title="Anova QA Toolkit",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Main Title ---
st.title("🛠️ Anova QA & Translation Toolkit")
st.markdown("A centralized panel for automated translation and Quality Assurance tasks.")

# --- Sidebar for Tool Selection ---
st.sidebar.title("Available Tools")
tool_selection = st.sidebar.selectbox(
    "Please select a tool to use:",
    [
        "--- Select a Tool ---",
        "TMX Cleaner (Semantic)",
        "MQXLIFF Error Splitter",
        "General QA Resolver",
        "Advanced QA Toolkit (AI)"
    ],
    key="tool_selector"
)

# --- Tool Interfaces ---

if tool_selection == "--- Select a Tool ---":
    st.info("Welcome! Please select a tool from the left sidebar to begin.")

# --- 1. TMX Cleaner Tool ---
elif tool_selection == "TMX Cleaner (Semantic)":
    st.header("TMX Cleaner with Semantic Analysis")
    st.write("Cleans duplicate and semantically misaligned translation units from a .tmx file.")
    
    similarity_threshold = st.slider("Similarity Threshold", 0.1, 1.0, 0.6, 0.05, help="Segments with a similarity score below this value will be removed.")
    uploaded_file = st.file_uploader("Upload your .tmx file", type=["tmx"], key="tmx_uploader")

    if uploaded_file:
        if st.button("Clean TMX File", key="tmx_clean_button"):
            # DO NOT DECODE HERE. Pass the raw buffer to the function.
            with st.spinner("Processing file..."):
                cleaned_content, report = clean_tmx_content(uploaded_file, similarity_threshold)
                st.success("TMX file processed!")
                st.subheader("Processing Report")
                st.text_area("Report", report, height=200)

            st.download_button("Download Cleaned TMX", cleaned_content, f"cleaned_{uploaded_file.name}", "application/xml")

# --- 2. MQXLIFF Error Splitter Tool ---
elif tool_selection == "MQXLIFF Error Splitter":
    st.header("MQXLIFF Error Splitter")
    st.write("Splits a .mqxliff file by error codes into a ZIP archive.")

    uploaded_file = st.file_uploader("Upload your .mqxliff file", type=["mqxliff"], key="mqxliff_uploader")

    if uploaded_file:
        if st.button("Split File by Errors", key="mqxliff_split_button"):
            with st.spinner("Processing MQXLIFF and creating ZIP archive..."):
                # Pass the raw buffer directly
                zip_bytes, report = split_mqxliff_content(uploaded_file)
                if zip_bytes:
                    st.success("File successfully split!")
                    st.subheader("Processing Report")
                    st.text_area("Report", report, height=200)
                    st.download_button("Download Split Files (.zip)", zip_bytes, f"split_{uploaded_file.name.replace('.mqxliff', '.zip')}", "application/zip")
                else:
                    st.error(report)

# --- 3. General QA Resolver ---
elif tool_selection == "General QA Resolver":
    st.header("General QA Resolver")
    st.write("Automatically fixes common mechanical errors in text-based files.")

    uploaded_file = st.file_uploader("Upload your text or XLIFF file", type=["txt", "xliff", "sdlxliff", "mqxliff"])
    
    fix_spaces = st.checkbox("Condense consecutive spaces", value=True)
    
    if uploaded_file:
        if st.button("Apply QA Fixes"):
            options = {"fix_double_spaces": fix_spaces}
            with st.spinner("Applying QA rules..."):
                # Pass the raw buffer directly
                resolved_content, report = run_full_qa(uploaded_file, options)
                st.success("Automated QA fixes complete!")
                st.subheader("Changes Report")
                st.text_area("Report", report, height=150)
            st.download_button("Download Resolved File", resolved_content, f"qa_resolved_{uploaded_file.name}", "text/plain")

# --- 4. Advanced QA Toolkit ---
elif tool_selection == "Advanced QA Toolkit (AI)":
    st.header("Advanced QA Toolkit (AI-Powered)")
    st.write("Applies multiple QA checks, including AI-powered terminology fixing.")
    
    xliff_file = st.file_uploader("Upload your XLIFF file", type=["xliff", "sdlxliff", "mqxliff"])
    termbase_file = st.file_uploader("Upload your Terminology file (.xlsx)", type=["xlsx"])
    
    if xliff_file and termbase_file:
        if "OPENAI_API_KEY" not in st.secrets:
            st.error("OpenAI API key is not configured in your Streamlit secrets.")
        else:
            if st.button("Run Advanced QA"):
                with st.spinner("Running full QA suite with AI..."):
                    termbase_df = pd.read_excel(termbase_file)
                    if 'source' not in termbase_df.columns or 'target' not in termbase_df.columns:
                        st.error("Termbase Excel must contain 'source' and 'target' columns.")
                    else:
                        options = {"run_terminology_qa": True, "termbase_df": termbase_df}
                        final_content, final_report = run_full_qa(xliff_file, options)
                        st.success("Advanced QA complete!")
                        st.subheader("Consolidated Report")
                        st.text_area("Report", final_report, height=250)
                        st.download_button("Download Final QA'd File", final_content, f"toolkit_qa_{xliff_file.name}", "application/xml")
