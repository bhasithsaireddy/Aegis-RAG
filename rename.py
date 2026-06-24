import os
import re

dir_path = r'd:\projects\mrag\aegis-rag'
exclude_dirs = {'node_modules', 'venv', '.venv', '.git', 'models', 'data', 'out'}
extensions = {'.md', '.js', '.jsx', '.py', '.json', '.html', '.css', '.txt', '.toml'}

replacements = [
    (r'Aegis RAG', 'Aegis RAG'),
    (r'Aegis RAG', 'Aegis RAG'),
    (r'aegis-rag', 'aegis-rag'),
    (r'Aegis RAG', 'Aegis RAG'),
    (r'Aegis RAG', 'Aegis RAG'),
    (r'aegis-rag', 'aegis-rag')
]

for root, dirs, files in os.walk(dir_path):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file == 'package-lock.json':
            continue
        ext = os.path.splitext(file)[1]
        if ext in extensions:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                continue
            
            new_content = content
            for old, new in replacements:
                new_content = re.sub(old, new, new_content)
                
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {file_path}")
