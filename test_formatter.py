import requests
import os

url = "http://127.0.0.1:5000/process"
file_path = r"c:\Users\gokul\OneDrive\Desktop\rishi 2\research_paper.md"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

# Test PDF generation
payload = {'format': 'pdf'}
files = [('file', ('research_paper.md', open(file_path, 'rb'), 'text/markdown'))]
response = requests.post(url, data=payload, files=files)

print("PDF Response:", response.json())

# Test DOCX generation
files = [('file', ('research_paper.md', open(file_path, 'rb'), 'text/markdown'))]
payload = {'format': 'docx'}
response = requests.post(url, data=payload, files=files)

print("DOCX Response:", response.json())
