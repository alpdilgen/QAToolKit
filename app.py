import streamlit as st
import pandas as pd
import io

# Tüm araç fonksiyonlarını import ediyoruz
try:
    from Tools.tmx_cleaner_tool import clean_tmx_content
    from Tools.qa_tools import fix_terminology_and_consistency
    from Tools.mqxliff_splitter_tool import split_mqxliff_content
    # from Tools.qa_resolver_tool import resolve_qa_issues # Bu araç henüz eklenmedi
except ImportError as e:
    st.error(f"Error loading modules from 'Tools' folder: {e}. Please ensure the folder and its `__init__.py` file exist in your GitHub repository.")
    st.stop()


# --- Sayfa Ayarları ve Başlık ---
st.set_page_config(
    page_title="Anova QA Toolkit",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛠️ Anova QA & Translation Toolkit")
st.markdown("A centralized panel for automated translation and Quality Assurance tasks.")

# --- KENAR ÇUBUĞU - ARAÇ SEÇİM MENÜSÜ (Tümü Dahil) ---
st.sidebar.title("Available Tools")
tool_selection = st.sidebar.selectbox(
    "Please select a tool to use:",
    [
        "--- Select a Tool ---",
        "TMX Cleaner (Semantic)",
        "Terminology & Consistency QA (AI)",
        "MQXLIFF Error Splitter",
    ],
    key="tool_selector"
)

# --- ANA EKRAN ---

if tool_selection == "--- Select a Tool ---":
    st.info("Welcome! Please select a tool from the left sidebar to begin.")

# --- 1. TMX Temizleyici Arayüzü ---
elif tool_selection == "TMX Cleaner (Semantic)":
    st.header("TMX Cleaner with Semantic Analysis")
    st.write("This tool removes duplicate segments and cleans misaligned translation units from a .tmx file based on semantic similarity.")
    
    similarity_threshold = st.slider("Similarity Threshold", 0.1, 1.0, 0.6, 0.05, help="Segments with a similarity score below this value will be removed.")
    uploaded_file = st.file_uploader("Upload your .tmx file", type=["tmx"], key="tmx_uploader")

    if uploaded_file:
        if st.button("Clean TMX File", key="tmx_clean_button"):
            with st.spinner("Processing file... This may take a moment."):
                tmx_content_str = uploaded_file.getvalue().decode("utf-8")
                cleaned_content, report = clean_tmx_content(tmx_content_str, similarity_threshold)
                st.success("TMX file processed!")
                st.subheader("Processing Report")
                st.text_area("Report", report, height=200)

            st.download_button("Download Cleaned TMX File", cleaned_content, f"cleaned_{uploaded_file.name}", "application/xml")

# --- 2. Terminoloji & Tutarlılık QA Aracı ---
elif tool_selection == "Terminology & Consistency QA (AI)":
    st.header("AI-Powered Terminology & Consistency QA")
    st.write("This tool analyzes an XLIFF file against a termbase and uses an AI model to automatically correct terminology and consistency errors.")

    col1, col2 = st.columns(2)
    with col1:
        xliff_file = st.file_uploader("Upload your XLIFF file", type=["xliff", "sdlxliff", "mqxliff"], key="xliff_uploader")
    with col2:
        termbase_file = st.file_uploader("Upload your Termbase file (.xlsx)", type=["xlsx"], key="termbase_uploader")

    if xliff_file and termbase_file:
        if "OPENAI_API_KEY" not in st.secrets:
            st.error("OpenAI API key is not configured. Please add it to your Streamlit secrets.")
        else:
            if st.button("Find & Fix Errors", key="term_fix_button"):
                with st.spinner("AI is analyzing your file... This can take some time."):
                    xliff_content_str = xliff_file.getvalue().decode("utf-8")
                    termbase_df = pd.read_excel(termbase_file)

                    if 'source' not in termbase_df.columns or 'target' not in termbase_df.columns:
                        st.error("Termbase Excel must contain 'source' and 'target' columns.")
                    else:
                        fixed_content, report = fix_terminology_and_consistency(xliff_content_str, termbase_df)
                        st.success("QA check complete!")
                        st.subheader("AI Correction Report")
                        st.text_area("Report", report, height=200)

                        st.download_button("Download Corrected File", fixed_content, f"fixed_{xliff_file.name}", "application/xml")

# --- 3. MQXLIFF Hata Ayırıcı Aracı (YENİ EKLENDİ) ---
elif tool_selection == "MQXLIFF Error Splitter":
    st.header("MQXLIFF Error Splitter")
    st.write("Splits an .mqxliff file into multiple smaller files based on error codes, then provides them in a single ZIP archive.")

    uploaded_file = st.file_uploader("Upload your .mqxliff file", type=["mqxliff"], key="mqxliff_uploader")

    if uploaded_file:
        if st.button("Split File by Errors", key="mqxliff_split_button"):
            with st.spinner("Processing MQXLIFF and creating ZIP archive..."):
                mqxliff_content_str = uploaded_file.getvalue().decode("utf-8")
                zip_bytes, report = split_mqxliff_by_error(mqxliff_content_str)
                
                if zip_bytes:
                    st.success("File successfully split by error codes!")
                    st.subheader("Processing Report")
                    st.text_area("Report", report, height=200)
                    st.download_button(
                       label="Download Split Files (.zip)",
                       data=zip_bytes,
                       file_name=f"split_errors_{uploaded_file.name.replace('.mqxliff', '.zip')}",
                       mime="application/zip"
                    )
                else:
                    st.error(report)

