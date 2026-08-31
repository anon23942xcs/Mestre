"""
Configurações centrais do projeto "Mestre".

Antes, cada arquivo (main.py e ia_service.py) carregava o .env e configurava
o Gemini separadamente, de forma duplicada. Agora existe um único lugar de
verdade para isso.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# O modelo antigo (gemini-1.5-flash) foi desativado pela Google e qualquer
# chamada a ele retorna erro 404. gemini-2.5-flash é a opção atual com bom
# custo-benefício para um caso de uso de narração em texto. Fica configurável
# por variável de ambiente para não precisar mexer no código quando a Google
# aposentar esse modelo também.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# A cada N turnos, o Compilador roda para destilar memorias_recentes em
# memorias_importantes.
TURNOS_POR_COMPILACAO = int(os.getenv("TURNOS_POR_COMPILACAO", "10"))

# Quantas memórias recentes (brutas) ficam guardadas antes de começar a
# descartar as mais antigas.
LIMITE_MEMORIAS_RECENTES = int(os.getenv("LIMITE_MEMORIAS_RECENTES", "8"))

# Máximo de memórias importantes (destiladas) mantidas pelo Compilador.
LIMITE_MEMORIAS_IMPORTANTES = int(os.getenv("LIMITE_MEMORIAS_IMPORTANTES", "5"))

if not GEMINI_API_KEY:
    print("AVISO: GEMINI_API_KEY não encontrada no .env. A IA vai recusar chamadas até isso ser configurado.")
