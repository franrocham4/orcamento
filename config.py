import os
from pathlib import Path

# Caminho da pasta a monitorar
WATCH_FOLDER = r"C:\Users\danielcoelho\Desktop\Nova pasta"

# Padrão do arquivo Excel a procurar
EXCEL_PATTERN = "*.xlsm"

# Porta do servidor
PORT = 5000

# Host do servidor
HOST = "127.0.0.1"

# Intervalo de verificação de arquivo (em segundos)
CHECK_INTERVAL = 2

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent

# Diretório de templates
TEMPLATES_DIR = BASE_DIR / "templates"

# Diretório de arquivos estáticos
STATIC_DIR = BASE_DIR / "static"
