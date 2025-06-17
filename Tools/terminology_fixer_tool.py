import streamlit as st
import xml.etree.ElementTree as ET
from io import StringIO
import pandas as pd
from openai import OpenAI

@st.cache_resource
def get_openai_client():
    """Caches the OpenAI client."""
    # This assumes you have set your OPENAI_API_KEY in Streamlit's secrets
    if "OPENAI_API_KEY" not in st.secrets:
        return None
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def fix_terminology(xliff_content_str: str, termbase_df: pd.DataFrame) -> (str, str):
    """
    Finds and suggests fixes for terminology issues in an XLIFF file using an AI model.
    """
    client = get_openai_client()
    if not client:
        return xliff_content_str, "OpenAI API key is not configured in Streamlit secrets."
        
    report_lines = []
    
    try:
        tree = ET.parse(StringIO(xliff_content_str))
        root = tree.getroot()
        
        term_dict = {str(row['source']).lower(): str(row['target']) for index, row in termbase_df.iterrows()}

        for trans_unit in root.findall('.//trans-unit'):
            source_node = trans_unit.find('source')
            target_node = trans_unit.find('target')
            
            if source_node is not None and target_node is not None and source_node.text is not None:
                source_text = source_node.text
                target_text = target_node.text if target_node.text else ""

                relevant_terms = {s: t for s, t in term_dict.items() if s in source_text.lower()}
                
                if relevant_terms:
                    prompt = f"""
                    You are a professional translator and QA specialist.
                    Analyze the following translation pair based on the provided terminology.
                    Source: "{source_text}"
                    Current Target: "{target_text}"
                    Required Terminology (Source -> Target): {relevant_terms}

                    If the target text does not correctly use the required terminology, provide a corrected version, making only the necessary changes.
                    If it's already correct, just return the original target text.
                    Respond ONLY with the corrected (or original) target text, without any introductory phrases.
                    """
                    
                    completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a translation QA specialist that only outputs corrected text."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1
                    )
                    
                    ai_corrected_text = completion.choices[0].message.content.strip().strip('"')

                    if ai_corrected_text != target_text:
                        report_lines.append(f"FIXED Unit ID '{trans_unit.get('id')}': From '{target_text[:40]}...' to '{ai_corrected_text[:40]}...'")
                        target_node.text = ai_corrected_text

        cleaned_xliff_string = ET.tostring(root, encoding='unicode')
        report = "\n".join(report_lines) if report_lines else "No terminology issues found or fixed by AI."
        return cleaned_xliff_string, report

    except Exception as e:
        return xliff_content_str, f"An error occurred: {str(e)}"
