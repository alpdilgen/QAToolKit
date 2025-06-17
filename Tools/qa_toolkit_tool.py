# tools/qa_toolkit_tool.py

# Diğer araçlardan fonksiyonları import ettiğimizi varsayalım
from .qa_resolver_tool import resolve_qa_issues
# from .terminology_fixer_tool import fix_terminology # Örnek
# from .consistency_fixer_tool import fix_consistency # Örnek

def run_qa_toolkit(content_str: str, toolkit_options: dict) -> (str, str):
    """
    Ana QA fonksiyonu. Seçilen araçları sırayla çalıştırır
    ve birleştirilmiş bir rapor sunar.
    """
    final_report = []
    current_content = content_str
    
    # Genel QA Çözücü
    if toolkit_options.get("run_general_qa", False):
        qa_options = toolkit_options.get("general_qa_options", {})
        current_content, report = resolve_qa_issues(current_content, qa_options)
        final_report.append("--- General QA Resolver Report ---\n" + report)

    # Terminoloji QA
    # if toolkit_options.get("run_terminology_qa", False):
    #     termbase_content = toolkit_options.get("termbase_content")
    #     current_content, report = fix_terminology(current_content, termbase_content)
    #     final_report.append("--- Terminology QA Report ---\n" + report)

    # Tutarlılık QA
    # if toolkit_options.get("run_consistency_qa", False):
    #     current_content, report = fix_consistency(current_content)
    #     final_report.append("--- Consistency QA Report ---\n" + report)

    return current_content, "\n\n".join(final_report)