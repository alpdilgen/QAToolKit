import streamlit as st
import xml.etree.ElementTree as ET
from io import StringIO, BytesIO
import pandas as pd
from openai import OpenAI
import zipfile
import re
from sentence_transformers import SentenceTransformer, util

# --- CACHED RESOURCES (To load models only once) ---

@st.cache_resource
def get_openai_client():
    """Caches the OpenAI client. Assumes API key is in Streamlit secrets."""
    if "OPENAI_API_KEY" not in st.secrets:
        return None
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_resource
def load_st_model():
    """Caches the SentenceTransformer model to avoid reloading."""
    return SentenceTransformer("distiluse-base-multilingual-cased-v1")

# --- TOOL 1: TMX CLEANER ---

def clean_tmx_content(tmx_file_buffer, similarity_threshold: float) -> (str, str):
    """Cleans a TMX file using semantic similarity and removes duplicates."""
    model = load_st_model() # THIS LINE WAS MISSING AND IS NOW FIXED
    report_lines = []
    try:
        tree = ET.parse(tmx_file_buffer)
        root = tree.getroot()
        body = root.find('body')
        if body is None:
            return "<!-- Error: <body> tag not found -->", "Error: <body> tag not found in TMX file."

        all_tus = list(body)
        initial_count = len(all_tus)
        unique_sources = {}
        segments_to_process = []
        
        for tu in all_tus:
            source_seg = tu.find("./tuv[1]/seg")
            if source_seg is not None and source_seg.text is not None:
                source_text = source_seg.text.strip()
                if source_text in unique_sources:
                    body.remove(tu)
                    report_lines.append(f"Removed duplicate: '{source_text[:50]}...'")
                else:
                    unique_sources[source_text] = True
                    segments_to_process.append(tu)
            else:
                body.remove(tu)
                report_lines.append("Removed a TU with a missing source segment.")
        
        if segments_to_process:
            source_texts = [tu.find("./tuv[1]/seg").text.strip() for tu in segments_to_process]
            target_texts = [tu.find("./tuv[2]/seg").text.strip() for tu in segments_to_process]
            
            if source_texts and target_texts and len(source_texts) == len(target_texts):
                source_embeddings = model.encode(source_texts, convert_to_tensor=True, show_progress_bar=False)
                target_embeddings = model.encode(target_texts, convert_to_tensor=True, show_progress_bar=False)
                cosine_scores = util.cos_sim(source_embeddings, target_embeddings).diagonal()
                indices_to_remove = {i for i, score in enumerate(cosine_scores) if score.item() < similarity_threshold}
                
                if indices_to_remove:
                    final_segments = [seg for i, seg in enumerate(segments_to_process) if i not in indices_to_remove]
                    report_lines.append(f"Removed {len(indices_to_remove)} segments based on low semantic similarity.")
                    body.clear(); body.extend(final_segments)
        
        final_count = len(body.findall('tu'))
        report_lines.insert(0, f"Processing complete. Original TUs: {initial_count}, Final TUs: {final_count}, Removed: {initial_count - final_count}")
        return ET.tostring(root, encoding='unicode'), "\n".join(report_lines)

    except Exception as e:
        return "<!-- ERROR! -->", f"An error occurred: {str(e)}"

# --- TOOL 2: MQXLIFF SPLITTER ---

def split_mqxliff_content(mqxliff_file_buffer) -> (bytes, str):
    """Splits an MQXLIFF file by error codes into a ZIP archive."""
    report_lines = []
    try:
        content_str = mqxliff_file_buffer.getvalue().decode('utf-8', errors='ignore')
        content_no_ns = re.sub(r' xmlns(:\w+)?="[^"]+"', '', content_str, count=1)
        tree = ET.parse(StringIO(content_no_ns))
        root = tree.getroot()
        error_groups = {}
        for tu in root.findall('.//trans-unit'):
            for warn in tu.findall('.//errorwarning'):
                code = warn.get('code')
                if code:
                    if code not in error_groups: error_groups[code] = []
                    error_groups[code].append(tu)
        
        if not error_groups: return None, "No segments with error codes found."

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            file_node_attrib = root.find('file').attrib if root.find('file') is not None else {}
            for code, units in error_groups.items():
                new_root = ET.Element(root.tag, root.attrib)
                new_file_node = ET.SubElement(new_root, 'file', file_node_attrib)
                body = ET.SubElement(new_file_node, 'body')
                body.extend(units)
                content_to_write = ET.tostring(new_root, encoding='unicode')
                zip_file.writestr(f"error_{code}.xliff", content_to_write)
                report_lines.append(f"Created file for error code {code} with {len(units)} segments.")
        zip_buffer.seek(0)
        return zip_buffer.getvalue(), "\n".join(report_lines)
    except Exception as e:
        return None, f"An error occurred: {str(e)}"

# --- TOOL 3 & 4: QA TOOLS ---

def run_full_qa(xliff_file_buffer, options: dict) -> (str, str):
    """Runs a suite of QA checks, including AI-powered ones."""
    report_lines = []
    try:
        # Pass the buffer directly to the parser
        tree = ET.parse(xliff_file_buffer)
        root = tree.getroot()

        # Simple QA Resolver Logic
        if options.get("fix_double_spaces"):
            count = 0
            for target in root.iter('target'):
                if target.text and '  ' in target.text:
                    target.text = re.sub(r' +', ' ', target.text)
                    count += 1
            if count > 0: report_lines.append(f"Fixed double spaces in {count} segments.")

        # AI-Powered Terminology and Consistency
        if options.get("run_terminology_qa"):
            client = get_openai_client()
            if not client: return "<!-- ERROR! -->", "OpenAI API key not configured."

            termbase_df = options.get("termbase_df")
            if termbase_df is not None:
                term_dict = {str(row['source']).lower(): str(row['target']) for _, row in termbase_df.iterrows()}
                report_lines.append("AI Terminology check would run here (Full logic to be implemented).")
        
        final_content = ET.tostring(root, encoding='unicode')
        report = "\n".join(report_lines) if report_lines else "No applicable QA issues found or fixed."
        return final_content, report
    except Exception as e:
        return "<!-- ERROR! -->", f"An error occurred during QA: {str(e)}"

