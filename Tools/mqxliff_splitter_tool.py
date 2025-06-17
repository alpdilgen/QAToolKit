# tools/mqxliff_splitter_tool.py

import xml.etree.ElementTree as ET
from io import StringIO, BytesIO
import zipfile

def split_mqxliff_content(mqxliff_content_str: str) -> bytes:
    """
    Bir MQXLIFF içeriğini string olarak alır, hata kategorilerine göre
    ayrı dosyalara böler ve bu dosyaları içeren bir ZIP arşivini
    hafızada oluşturup bytes olarak döndürür.
    """
    try:
        # Bellekte bir ZIP dosyası oluştur
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Örnek bir mantık: Segmentleri durumlarına göre ayır
            # Sizin MQXLIFF_ErrorSplitter.py'nizdeki asıl mantık buraya uyarlanmalı
            tmx_file = StringIO(mqxliff_content_str)
            tree = ET.parse(tmx_file)
            root = tree.getroot()
            
            # Basit bir örnek: "Edited" ve "Rejected" durumlarına göre ayırma
            groups = {"edited": [], "rejected": []}
            
            for tu in root.findall('.//trans-unit'):
                state = tu.get('state', 'unknown').lower()
                if 'edited' in state:
                    groups['edited'].append(tu)
                elif 'rejected' in state:
                    groups['rejected'].append(tu)
            
            # Her grup için ayrı bir XLIFF dosyası oluştur ve ZIP'e ekle
            for group_name, units in groups.items():
                if not units: continue # Eğer grupta segment yoksa atla

                # Yeni bir XLIFF ağacı oluştur
                new_root = ET.Element(root.tag, root.attrib)
                new_body = ET.SubElement(new_root, 'body')
                new_body.extend(units)
                
                # Dosya içeriğini string olarak al
                content_to_write = ET.tostring(new_root, encoding='unicode')
                # ZIP dosyasına ekle
                zip_file.writestr(f"split_{group_name}.mqxliff", content_to_write)

        # ZIP arşivinin byte içeriğini al
        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    except Exception as e:
        # Hata durumunda, hata mesajını bir metin dosyası olarak ZIP'leyip döndür
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("error.txt", f"An error occurred: {str(e)}")
        zip_buffer.seek(0)
        return zip_buffer.getvalue()