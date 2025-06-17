import xml.etree.ElementTree as ET
from io import StringIO, BytesIO
import zipfile
import re

def split_mqxliff_content(mqxliff_content_str: str) -> (bytes, str):
    """
    Bir MQXLIFF içeriğini string olarak alır, hata kategorilerine göre
    ayrı dosyalara böler ve bu dosyaları içeren bir ZIP arşivini
    hafızada oluşturup bytes olarak döndürür.
    """
    report_lines = []
    try:
        # Bellekte bir ZIP dosyası oluştur
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # XML içeriğini ayrıştır
            # Namespace'leri görmezden gelmek için regex ile temizlik
            mqxliff_content_str = re.sub(r' xmlns(:\w+)?="[^"]+"', '', mqxliff_content_str, count=1)
            tree = ET.parse(StringIO(mqxliff_content_str))
            root = tree.getroot()
            
            error_groups = {}  # {error_code: [trans-unit_element]}
            
            # Tüm trans-unit'leri bul
            for tu in root.findall('.//trans-unit'):
                warnings = tu.findall('.//errorwarning')
                for warn in warnings:
                    code = warn.get('code')
                    if code:
                        if code not in error_groups:
                            error_groups[code] = []
                        error_groups[code].append(tu)
            
            if not error_groups:
                return None, "No segments with error codes were found in the file."

            # Her hata kodu grubu için ayrı bir XLIFF dosyası oluştur
            for code, units in error_groups.items():
                # Yeni bir XLIFF ağacı oluştur (orijinalin başlık bilgileriyle)
                new_root = ET.Element(root.tag, root.attrib)
                file_node = root.find('file')
                if file_node is not None:
                     new_file_node = ET.SubElement(new_root, 'file', file_node.attrib)
                     body = ET.SubElement(new_file_node, 'body')
                     body.extend(units) # Sadece bu hata koduna ait segmentleri ekle
                     
                     # Dosya içeriğini string olarak al
                     content_to_write = ET.tostring(new_root, encoding='unicode')
                     # ZIP dosyasına yaz
                     zip_file.writestr(f"error_{code}.xliff", content_to_write)
                     report_lines.append(f"Created file for error code {code} with {len(units)} segments.")

        zip_buffer.seek(0)
        report = "\n".join(report_lines) if report_lines else "No specific error groups found to split."
        return zip_buffer.getvalue(), report
        
    except Exception as e:
        return None, f"An error occurred during splitting: {str(e)}"
