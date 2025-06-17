# tools/qa_resolver_tool.py

import re

def resolve_qa_issues(content_str: str, options: dict) -> (str, str):
    """
    Bir metin içeriğini string olarak alır, seçilen QA kurallarına göre
    düzeltir. Düzeltilmiş metni ve yapılan değişikliklerin raporunu döndürür.
    """
    report_lines = []
    original_content = content_str
    
    # Seçenek 1: Çift boşlukları düzelt
    if options.get("fix_double_spaces", False):
        resolved_content = re.sub(r' +', ' ', original_content)
        if resolved_content != original_content:
            report_lines.append("Fixed multiple consecutive spaces.")
            original_content = resolved_content

    # Seçenek 2: Satır başı/sonu boşluklarını temizle
    if options.get("fix_line_endings", False):
        lines = original_content.splitlines()
        stripped_lines = [line.strip() for line in lines]
        resolved_content = "\n".join(stripped_lines)
        if resolved_content != original_content:
            report_lines.append("Stripped leading/trailing whitespace from lines.")
            original_content = resolved_content

    # Buraya qa_resolver.py'nizdeki diğer tüm kurallar eklenebilir
    # (noktalama, sayılar, etiketler vb.)

    final_report = "\n".join(report_lines) if report_lines else "No issues found or no checks selected."
    
    return original_content, final_report