# Arquivo: run.py
import streamlit.cli as stcli
import sys
import os

if __name__ == "__main__":
    # Configurar o caminho para o arquivo principal da aplicação
    sys.argv = ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.headless=true"]
    sys.exit(stcli.main())