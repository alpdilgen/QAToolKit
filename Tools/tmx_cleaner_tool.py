import streamlit as st
import xml.etree.ElementTree as ET
from io import StringIO
from sentence_transformers import SentenceTransformer, util

# Modelin tekrar tekrar yüklenmesini önlemek için cache'lenir
@st.cache_resource
def load_st_model():
    """Caches the sentence transformer model to avoid reloading on each run."""
    return SentenceTransformer("distiluse-base-multilingual-cased-v1")

def clean_tmx_content(tmx_content_as_string: str, similarity_threshold: float = 0.6) -> (str, str):
    """
    Cleans a TMX file by removing duplicate and semantically dissimilar translation units.
    """
    model = load_st_model()
    report_lines = []
    
    try:
        tmx_file = StringIO(tmx_content_as_string)
        tree = ET.parse(tmx_file)
        root = tree.getroot()
        body = root.find('body')

        if body is None:
            return tmx_content_as_string, "Error: <body> tag not found in TMX file."

        unique_sources = {}
        segments_to_process = []
        
        all_tus = list(body)
        initial_count = len(all_tus)
        
        for tu in all_tus:
            # Find source and target segments more robustly
            source_lang_code = tu.find("./tuv[1]").get('{http://www.w3.org/XML/1998/namespace}lang', 'src')
            target_lang_code = tu.find("./tuv[2]").get('{http://www.w3.org/XML/1998/namespace}lang', 'trg')

            source_seg = tu.find(f"./tuv[@{{http://www.w3.org/XML/1998/namespace}}lang='{source_lang_code}']/seg")
            target_seg = tu.find(f"./tuv[@{{http://www.w3.org/XML/1998/namespace}}lang='{target_lang_code}']/seg")

            if source_seg is not None and target_seg is not None and source_seg.text is not None:
                source_text = source_seg.text.strip()
                if source_text in unique_sources:
                    body.remove(tu)
                    report_lines.append(f"Removed duplicate source: '{source_text[:50]}...'")
                else:
                    unique_sources[source_text] = True
                    segments_to_process.append(tu)
            else:
                body.remove(tu)
                report_lines.append("Removed a TU with missing source or target seg.")

        # Semantic similarity check on the remaining unique segments
        if segments_to_process:
            source_texts = [tu.find("./tuv[1]/seg").text.strip() for tu in segments_to_process]
            target_texts = [tu.find("./tuv[2]/seg").text.strip() for tu in segments_to_process]
            
            source_embeddings = model.encode(source_texts, convert_to_tensor=True, show_progress_bar=True)
            target_embeddings = model.encode(target_texts, convert_to_tensor=True, show_progress_bar=True)
            
            cosine_scores = util.cos_sim(source_embeddings, target_embeddings).diagonal()
            
            indices_to_remove = set()
            for i, score in enumerate(cosine_scores):
                if score.item() < similarity_threshold:
                    indices_to_remove.add(i)
                    report_lines.append(f"Removed low similarity pair (Score: {score.item():.2f}): '{source_texts[i][:50]}...'")
            
            if indices_to_remove:
                # Rebuild the list of TUs to keep
                final_segments = [seg for i, seg in enumerate(segments_to_process) if i not in indices_to_remove]
                # Clear body and append only the ones to keep
                body.clear()
                body.extend(final_segments)
        
        final_count = len(body.findall('tu'))
        report_lines.insert(0, f"Processing complete. Original TUs: {initial_count}, Final TUs: {final_count}, Removed: {initial_count - final_count}")
        
        cleaned_xml_string = ET.tostring(root, encoding='unicode')
        report = "\n".join(report_lines)
        return cleaned_xml_string, report

    except Exception as e:
        return tmx_content_as_string, f"An error occurred during processing: {str(e)}"

