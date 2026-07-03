"""
Configuração de testes.

Garante que ``src/`` esteja no ``sys.path`` mesmo quando o pacote não foi
instalado com ``pip install -e .`` (redundante com ``pythonpath`` do
pyproject, porém torna os testes executáveis via ``python -m pytest`` sem
configuração adicional).
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
