import streamlit as st
import pandas as pd

# Araçlarımızı tools klasöründen import ediyoruz
# Bu importların çalışabilmesi için tools/__init__.py dosyasının var olması şarttır.
from tools.tmx_cleaner_tool import clean_tmx_content
from tools.mqxliff_splitter_tool import split_mqxliff_content
from tools.qa_resolver_tool import resolve_qa_issues
from tools.qa_toolkit_tool import run_qa_toolkit

# --- Sayfa Ayarları ve Başlık ---
st.set_page_config(
    page_title="Anova Çeviri Araç Kutusu",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ Anova Çeviri ve Kalite Kontrol Araç Kutusu")
st.markdown("Sık kullanılan çeviri ve QA görevlerini otomatize etmek için merkezi panel.")

# --- KENAR ÇUBUĞU - ARAÇ SEÇİM MENÜSÜ ---
st.sidebar.title("Araçlar")
tool_selection = st.sidebar.selectbox(
    "Lütfen kullanmak istediğiniz aracı seçin:",
    [
        "--- Seçiniz ---",
        "TMX Temizleyici",
        "MQXLIFF Hata Ayırıcı",
        "Otomatik QA Düzeltici",
        "Gelişmiş QA Kiti"
    ]
)

# --- ANA EKRAN ---

if tool_selection == "--- Seçiniz ---":
    st.info("Lütfen soldaki menüden bir araç seçerek başlayın.")

# --- 1. TMX Temizleyici Arayüzü ---
elif tool_selection == "TMX Temizleyici":
    st.header("TMX Temizleyici")
    st.write("Çeviri Belleği (.tmx) dosyalarındaki kopya segmentleri temizler.")
    
    uploaded_file = st.file_uploader("Lütfen .tmx dosyanızı buraya yükleyin", type=["tmx"])

    if uploaded_file is not None:
        if st.button("TMX Dosyasını Temizle"):
            with st.spinner("Dosya işleniyor..."):
                tmx_content_str = uploaded_file.getvalue().decode("utf-8")
                cleaned_content = clean_tmx_content(tmx_content_str)
                st.success("TMX dosyası başarıyla işlendi!")

            st.download_button(
               label="Temizlenmiş TMX Dosyasını İndir",
               data=cleaned_content,
               file_name=f"cleaned_{uploaded_file.name}",
               mime="application/xml"
            )

# --- 2. MQXLIFF Hata Ayırıcı Arayüzü ---
elif tool_selection == "MQXLIFF Hata Ayırıcı":
    st.header("MQXLIFF Hata Ayırıcı")
    st.write("Bir .mqxliff dosyasını segment durumlarına göre (örn: 'Edited', 'Rejected') ayrı dosyalara böler ve bir ZIP arşivi olarak sunar.")

    uploaded_file = st.file_uploader("Lütfen .mqxliff dosyanızı buraya yükleyin", type=["mqxliff"])

    if uploaded_file is not None:
        if st.button("Dosyayı Ayır ve Arşivle"):
            with st.spinner("MQXLIFF işleniyor ve ZIP oluşturuluyor..."):
                mqxliff_content_str = uploaded_file.getvalue().decode("utf-8")
                zip_bytes = split_mqxliff_content(mqxliff_content_str)
                st.success("Dosyalar başarıyla ayrıştırıldı ve ZIP arşivi oluşturuldu!")

            st.download_button(
               label="Bölünmüş Dosyaları ZIP Olarak İndir",
               data=zip_bytes,
               file_name=f"split_{uploaded_file.name.replace('.mqxliff', '.zip')}",
               mime="application/zip"
            )

# --- 3. Otomatik QA Düzeltici Arayüzü ---
elif tool_selection == "Otomatik QA Düzeltici":
    st.header("Otomatik QA Düzeltici")
    st.write("Metin dosyalarındaki yaygın mekanik hataları otomatik olarak düzeltir.")

    uploaded_file = st.file_uploader("Lütfen metin dosyanızı (.txt, .xliff, vb.) buraya yükleyin", type=["txt", "xliff", "xlf", "sdlxliff", "mqxliff"])
    
    st.subheader("Uygulanacak Kurallar")
    fix_spaces = st.checkbox("Ardışık boşlukları tek boşluğa indirge", value=True)
    fix_endings = st.checkbox("Satır başı ve sonundaki boşlukları temizle", value=True)
    
    if uploaded_file is not None:
        if st.button("QA Düzeltmelerini Uygula"):
            options = {
                "fix_double_spaces": fix_spaces,
                "fix_line_endings": fix_endings,
            }
            with st.spinner("QA kuralları uygulanıyor..."):
                file_content_str = uploaded_file.getvalue().decode("utf-8")
                resolved_content, report = resolve_qa_issues(file_content_str, options)
                st.success("Otomatik QA düzeltmeleri tamamlandı!")

                st.subheader("Yapılan Değişiklikler Raporu")
                st.text_area("Rapor", report, height=150)
                
            st.download_button(
               label="Düzeltilmiş Dosyayı İndir",
               data=resolved_content,
               file_name=f"qa_resolved_{uploaded_file.name}",
               mime="text/plain"
            )

# --- 4. Gelişmiş QA Kiti Arayüzü ---
elif tool_selection == "Gelişmiş QA Kiti":
    st.header("Gelişmiş QA Kiti")
    st.write("Bir dosyaya birden çok kalite kontrol adımını art arda uygular.")
    
    main_file = st.file_uploader("Lütfen ana çeviri dosyanızı (.xliff, .txt vb.) yükleyin")
    
    st.subheader("Uygulanacak QA Modülleri")
    run_general = st.checkbox("Genel QA Düzeltmelerini Çalıştır (Boşluk, Noktalama vb.)", value=True)
    run_terminology = st.checkbox("Terminoloji Kontrolünü Çalıştır")

    termbase_file = None
    if run_terminology:
        termbase_file = st.file_uploader("Lütfen terminoloji dosyanızı (.xlsx) yükleyin", type=["xlsx"])

    if main_file is not None:
        if st.button("Gelişmiş QA'i Başlat"):
            termbase_content = None
            if run_terminology and termbase_file:
                # Gerçek uygulamada bu kısım termbase'i işleyecek
                pass 
            
            toolkit_options = {
                "run_general_qa": run_general,
                "run_terminology_qa": run_terminology,
                "termbase_content": termbase_content,
                "general_qa_options": {"fix_double_spaces": True, "fix_line_endings": True}
            }

            with st.spinner("Gelişmiş QA kiti çalıştırılıyor..."):
                main_content_str = main_file.getvalue().decode("utf-8")
                final_content, final_report = run_qa_toolkit(main_content_str, toolkit_options)
                st.success("Tüm QA adımları tamamlandı!")

                st.subheader("Birleştirilmiş Değişiklik Raporu")
                st.text_area("Rapor", final_report, height=250)

            st.download_button(
               label="Nihai Düzeltilmiş Dosyayı İndir",
               data=final_content,
               file_name=f"toolkit_qa_{main_file.name}",
               mime="text/plain"
            )
