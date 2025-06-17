import streamlit as st
import pandas as pd
import io

# Import the refactored, AI-powered tool functions
from Tools.tmx_cleaner_tool import clean_tmx_content
# Placeholder for other tools to be added later
# from Tools.mqxliff_splitter_tool import split_mqxliff_content
from Tools.terminology_fixer_tool import fix_terminology

# --- Page Configuration ---
st.set_page_config(
    page_title="Anova QA Toolkit",
    page_icon="🛠️",
    layout="wide"
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
        "Terminology QA Fixer (AI)",
        # "MQXLIFF Error Splitter", # Add back when function is ready
        # "General QA Resolver",    # Add back when function is ready
    ]
)

# --- Tool Interfaces ---

if tool_selection == "--- Select a Tool ---":
    st.info("Welcome! Please select a tool from the left sidebar to begin.")

# --- 1. TMX Cleaner Tool ---
elif tool_selection == "TMX Cleaner (Semantic)":
    st.header("TMX Cleaner with Semantic Analysis")
    st.write("This tool removes duplicate segments and cleans misaligned translation units from a .tmx file based on semantic similarity.")
    
    similarity_threshold = st.slider("Similarity Threshold", 0.1, 1.0, 0.6, 0.05, help="Segments with a similarity score below this value will be removed.")
    
    uploaded_file = st.file_uploader("Upload your .tmx file", type=["tmx"])

    if uploaded_file is not None:
        if st.button("Clean TMX File"):
            with st.spinner("Processing file with semantic analysis... This may take a moment."):
                tmx_content_str = uploaded_file.getvalue().decode("utf-8")
                cleaned_content, report = clean_tmx_content(tmx_content_str, similarity_threshold)
                st.success("TMX file has been processed!")

                st.subheader("Processing Report")
                st.text_area("Report", report, height=200)

            st.download_button(
               label="Download Cleaned TMX File",
               data=cleaned_content,
               file_name=f"cleaned_{uploaded_file.name}",
               mime="application/xml"
            )

# --- 2. Terminology QA Fixer Tool ---
elif tool_selection == "Terminology QA Fixer (AI)":
    st.header("AI-Powered Terminology QA Fixer")
    st.write("This tool analyzes an XLIFF file against a termbase and uses an AI model to automatically correct terminology errors.")

    col1, col2 = st.columns(2)
    with col1:
        xliff_file = st.file_uploader("Upload your XLIFF file (.xliff, .sdlxliff)", type=["xliff", "sdlxliff"])
    with col2:
        termbase_file = st.file_uploader("Upload your Termbase file (.xlsx)", type=["xlsx"])

    if xliff_file and termbase_file:
        if "OPENAI_API_KEY" not in st.secrets:
            st.error("OpenAI API key is not configured. Please add it to your Streamlit secrets.")
        else:
            if st.button("Find & Fix Terminology Errors"):
                with st.spinner("AI is analyzing your file... This might take some time depending on file size."):
                    xliff_content_str = xliff_file.getvalue().decode("utf-8")
                    termbase_df = pd.read_excel(termbase_file)

                    # Ensure termbase has 'source' and 'target' columns
                    if 'source' not in termbase_df.columns or 'target' not in termbase_df.columns:
                        st.error("Termbase Excel must contain 'source' and 'target' columns.")
                    else:
                        fixed_content, report = fix_terminology(xliff_content_str, termbase_df)
                        st.success("Terminology QA check complete!")

                        st.subheader("AI Correction Report")
                        st.text_area("Report", report, height=200)

                        st.download_button(
                            label="Download Corrected XLIFF File",
                            data=fixed_content,
                            file_name=f"terminology_fixed_{xliff_file.name}",
                            mime="application/xml"
                        )
