import re
import pdfplumber
import pandas as pd

# Path to your PDF
pdf_path = "Manual.pdf"

# Updated regex patterns
alarm_number_re = re.compile(r"(?:A\s*LARM|ALARM)\s+NUMBER:\s+([0-9a-fA-F]{4})", re.IGNORECASE)
alarm_message_re = re.compile(r"Alarm Message[:\s]+(.+?)(?:\n|Recovery:|Cause:)", re.IGNORECASE | re.DOTALL)
recovery_re = re.compile(r"Recovery[:\s]*(.*?)(?=\n[A-Z][a-z]+[:]|$)", re.IGNORECASE | re.DOTALL)
cause_re = re.compile(r"Cause[:\s]*(.*?)(?=\n[A-Z][a-z]+[:]|$)", re.IGNORECASE | re.DOTALL)

# Collect all alarm blocks
alarms = []
alarm_text = ""

# Step 1: Extract all text after TOC
with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        if i < 23:  # Skip intro/TOC pages
            continue
        text = page.extract_text()
        if text:
            alarm_text += "\n" + text

# Step 2: Split based on the correct "Alarm Number" heading
alarm_blocks = re.findall(
    r"((?:A\s*LARM|ALARM)\s+NUMBER:\s+[0-9a-fA-F]{4}.*?)(?=(?:A\s*LARM|ALARM)\s+NUMBER:|\Z)",
    alarm_text,
    re.IGNORECASE | re.DOTALL
)

# Step 3: Parse each block
for block in alarm_blocks:
    number = alarm_number_re.search(block)
    message = alarm_message_re.search(block)
    recovery = recovery_re.search(block)
    cause = cause_re.search(block)

    alarms.append({
        "Alarm Number": number.group(1).strip() if number else "",
        "Alarm Message": message.group(1).strip().replace('\n', ' ') if message else "",
        "Recovery": recovery.group(1).strip().replace('\n', ' ') if recovery else "",
        "Cause": cause.group(1).strip().replace('\n', ' ') if cause else ""
    })

# Step 4: Save to Excel
df = pd.DataFrame(alarms)
df.to_excel("Alarm_Manual_Extracted.xlsx", index=False)
print("✅ Extracted successfully using updated regex and saved to Excel!")
