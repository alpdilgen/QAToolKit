import streamlit as st
import xml.etree.ElementTree as ET
from io import StringIO
from sentence_transformers import SentenceTransformer, util

@st.cache_resource
def load_st_model():
    """Cache the sentence transformer model to avoid reloading on each run."""
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

        unique_sources = {}
        segments_to_process = []
        
        all_tus = list(body) # Create a copy to iterate over while modifying
        for tu in all_tus:
            source_seg = tu.find("./tuv[@xml:lang='en-US']/seg") # Adjust lang code if needed
            target_seg = tu.find("./tuv[@xml:lang='de-DE']/seg") # Adjust lang code if needed

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

        # Semantic similarity check
        source_texts = [tu.find("./tuv/seg").text.strip() for tu in segments_to_process]
        target_texts = [tu.findall("./tuv/seg")[1].text.strip() for tu in segments_to_process]

        if source_texts and target_texts:
            source_embeddings = model.encode(source_texts, convert_to_tensor=True)
            target_embeddings = model.encode(target_texts, convert_to_tensor=True)
            
            cosine_scores = util.cos_sim(source_embeddings, target_embeddings).diagonal()
            
            indices_to_remove = []
            for i, score in enumerate(cosine_scores):
                if score.item() < similarity_threshold:
                    indices_to_remove.append(i)
                    report_lines.append(f"Removed low similarity pair (Score: {score.item():.2f}): '{source_texts[i][:50]}...'")
            
            # Remove from the end to avoid index shifting
            for i in sorted(indices_to_remove, reverse=True):
                body.remove(segments_to_process[i])

        cleaned_xml_string = ET.tostring(root, encoding='unicode')
        report = "\n".join(report_lines)
        return cleaned_xml_string, report

    except Exception as e:
        return f"<!-- ERROR: {str(e)} -->", f"An error occurred: {str(e)}"
