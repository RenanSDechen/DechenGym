"""
Pacote Orquestrador
===================

Transforma um *briefing em linguagem natural* em um **projeto de máquina
articulada validado**, encadeando as ferramentas de ergonomia, síntese de
came, cálculo estrutural, geração de geometria e imagem — com um loop de
**autocorreção estrutural**.

Arquitetura (provedor-agnóstica)
--------------------------------
- :mod:`~dechengym.orquestrador.pipeline` : núcleo **determinístico** do
  projeto (:func:`projetar_maquina`) + :class:`RequisicaoProjeto`.
- :mod:`~dechengym.orquestrador.adapters` : camada de LLM plugável para
  interpretar o briefing — :class:`AdaptadorRegras` (fallback offline) e
  :class:`AdaptadorAnthropic` (Claude real, quando há credencial).
- :mod:`~dechengym.orquestrador.agente` : :func:`orquestrar`, que une a
  interpretação do briefing ao pipeline determinístico.

O núcleo roda e é testável **sem** qualquer LLM; a chamada real ao Claude
entra por cima quando houver ``ANTHROPIC_API_KEY``.
"""

from dechengym.orquestrador.adapters import (
    AdaptadorAnthropic,
    AdaptadorLLM,
    AdaptadorRegras,
    adaptador_padrao,
)
from dechengym.orquestrador.agente import orquestrar
from dechengym.orquestrador.pipeline import RequisicaoProjeto, projetar_maquina

__all__ = [
    "RequisicaoProjeto",
    "projetar_maquina",
    "AdaptadorLLM",
    "AdaptadorRegras",
    "AdaptadorAnthropic",
    "adaptador_padrao",
    "orquestrar",
]
