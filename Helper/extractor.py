import pdfplumber

def extract_first_24_pages(pdf_path: str, output_txt_path: str, num_pages: int = 24):
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for i in range(min(num_pages, len(pdf.pages))):
                page = pdf.pages[i]
                text += page.extract_text() or ""  # fallback if page has no text

        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"✅ Successfully extracted first {num_pages} pages to '{output_txt_path}'")

    except Exception as e:
        print(f"❌ Failed to extract: {e}")


# --- Usage ---
if __name__ == "__main__":
    extract_first_24_pages("Manual.pdf", "manual_intro.txt")
