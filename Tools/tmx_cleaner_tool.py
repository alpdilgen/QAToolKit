# tools/tmx_cleaner_tool.py

import xml.etree.ElementTree as ET
from io import StringIO

def clean_tmx_content(tmx_content_as_string: str) -> str:
    """
    Bir TMX içeriğini string olarak alır, kopyaları temizler ve
    temizlenmiş TMX içeriğini string olarak döndürür.
    Bu, orijinal TMX_Cleaner.py script'inizin fonksiyonlaştırılmış halidir.
    """
    try:
        # String içeriği bir dosya gibi okumak için StringIO kullanıyoruz
        # Bu, diske yazma ihtiyacını ortadan kaldırır
        tmx_file = StringIO(tmx_content_as_string)
        
        tree = ET.parse(tmx_file)
        root = tree.getroot()
        body = root.find('body')

        unique_segments = {}
        duplicates_found = 0

        # Orijinal TMX'teki tüm <tu> (translation unit) elemanlarını bul
        translation_units = list(body) # Kopya üzerinde çalışmak için listeye çevir

        for tu in translation_units:
            source_text = ""
            tuv_source = tu.find("./tuv[@xml:lang='en-US']/seg") # Kaynak dil kodunuza göre özelleştirilebilir
            if tuv_source is not None and tuv_source.text is not None:
                source_text = tuv_source.text.strip()
            
            if source_text in unique_segments:
                body.remove(tu) # Eğer bu kaynak metin daha önce görüldüyse, bu <tu>'yu sil
                duplicates_found += 1
            else:
                unique_segments[source_text] = True

        # Temizlenmiş XML'i tekrar string'e çevir
        # Not: Bu basit bir kopya temizleme örneğidir. Sizin TMX_Cleaner.py'nizdeki
        # daha karmaşık mantığı bu fonksiyonun içine taşıyabilirsiniz.
        
        cleaned_xml_string = ET.tostring(root, encoding='unicode')
        
        # Raporlama için bir başlık ekleyebiliriz
        report = f"\n"
        return report + cleaned_xml_string

    except Exception as e:
        # Hata durumunda, hatayı ve orijinal içeriği geri döndür
        error_message = f"\n"
        return error_message + tmx_content_as_string