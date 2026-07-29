import os
import re
import requests
from bs4 import BeautifulSoup
import pdfplumber
from deep_translator import GoogleTranslator

os.makedirs("docs", exist_ok=True)

BASE_URL = "https://mileswmathis.com/"
UPDATES_URL = "https://mileswmathis.com/updates.html"

def get_paper_links():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(UPDATES_URL, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, "html.parser")
        
        pdf_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().endswith(".pdf"):
                full_url = href if href.startswith("http") else BASE_URL + href.lstrip("/")
                title = a.get_text(strip=True) or href.split("/")[-1]
                pdf_links.append((full_url, title))
        return pdf_links[:15]
    except Exception as e:
        print(f"Siteye erişilemedi: {e}")
        return []

def process_pdf(pdf_url, pdf_title):
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', pdf_url.split("/")[-1].replace(".pdf", ""))
    html_path = f"docs/{clean_name}.html"

    if os.path.exists(html_path):
        return clean_name, pdf_title

    print(f"İşleniyor ve Çevriliyor: {pdf_title}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(pdf_url, headers=headers)
        with open("temp.pdf", "wb") as f:
            f.write(res.content)

        text = ""
        with pdfplumber.open("temp.pdf") as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        if not text.strip():
            return None, None

        translator = GoogleTranslator(source='auto', target='tr')
        chunks = [text[i:i+3000] for i in range(0, len(text), 3000)]
        translated_text = ""
        for chunk in chunks:
            try:
                translated_text += translator.translate(chunk) + "\n"
            except:
                translated_text += chunk + "\n"

        # f-string hatasına sebep olan \n karakteri burada f-string dışına alındı:
        html_body_text = translated_text.replace('\n', '<br>')

        html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{pdf_title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.8; max-width: 800px; margin: 0 auto; padding: 20px; background: #fafafa; color: #222; }}
        .card {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        a {{ color: #0066cc; text-decoration: none; font-weight: bold; }}
        h1 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; font-size: 24px; }}
    </style>
</head>
<body>
    <div class="card">
        <p><a href="index.html">← Tüm Makalelere Dön</a></p>
        <h1>{pdf_title}</h1>
        <div>{html_body_text}</div>
    </div>
</body>
</html>"""

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        if os.path.exists("temp.pdf"):
            os.remove("temp.pdf")

        return clean_name, pdf_title
    except Exception as e:
        print(f"Hata oluştu ({pdf_url}): {e}")
        return None, None

if __name__ == "__main__":
    papers = get_paper_links()
    
    for url, title in papers:
        process_pdf(url, title)

    index_html = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Miles Mathis Türkçe Çevirileri</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; background: #fafafa; }
        .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        ul { list-style: none; padding: 0; }
        li { margin: 12px 0; padding: 12px; background: #f4f4f4; border-radius: 6px; }
        a { color: #222; text-decoration: none; font-weight: 600; display: block; }
        a:hover { color: #0066cc; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Miles Mathis - Türkçe Makale Kütüphanesi</h2>
        <ul>
"""
    if os.path.exists("docs"):
        for file in os.listdir("docs"):
            if file.endswith(".html") and file != "index.html":
                display_name = file.replace(".html", "").replace("_", " ").title()
                index_html += f'<li><a href="{file}">📄 {display_name}</a></li>\n'

    index_html += """
        </ul>
    </div>
</body>
</html>"""

    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
