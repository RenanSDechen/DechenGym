"""
Camada de interpretação do briefing (provedor-agnóstica).
========================================================

Converte um *briefing em linguagem natural* em uma
:class:`~dechengym.orquestrador.pipeline.RequisicaoProjeto`.

- :class:`AdaptadorRegras` — heurístico, **sem dependências e offline**.
  É o fallback determinístico usado nos testes e quando não há LLM.
- :class:`AdaptadorAnthropic` — usa o Claude (via SDK ``anthropic``) para
  interpretar briefings livres. Requer ``ANTHROPIC_API_KEY`` (ou perfil
  ``ant``) e o pacote ``anthropic`` instalado.

:func:`adaptador_padrao` escolhe automaticamente o Anthropic quando há
credencial/SDK, caindo para o de regras caso contrário.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Protocol

from dechengym.data.exercicios_db import CATALOGO_EXERCICIOS
from dechengym.orquestrador.pipeline import RequisicaoProjeto

#: Modelo Claude padrão (mais capaz). Ajuste se desejar Sonnet/Haiku.
MODELO_PADRAO = "claude-opus-4-8"


class AdaptadorLLM(Protocol):
    """Contrato de um interpretador de briefing."""

    nome: str

    def interpretar(self, briefing: str) -> RequisicaoProjeto:  # pragma: no cover
        ...


# ==========================================================================
# Utilitários de normalização (compartilhados)
# ==========================================================================
def _sem_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


# Palavras-chave -> exercício do catálogo (ordem importa: mais específico antes).
_PALAVRAS_EXERCICIO: list[tuple[tuple[str, ...], str]] = [
    (("rosca", "biceps"), "rosca_biceps"),
    (("triceps",), "triceps_maquina"),
    (("supino", "peito", "peitoral"), "supino_maquina"),
    (("remada", "dorsal", "costas"), "remada_maquina"),
    (("desenvolvimento", "ombro", "deltoide"), "desenvolvimento_maquina"),
    (("extensora", "quadriceps", "quadricipe"), "cadeira_extensora"),
    (("flexora", "isquio", "posterior de coxa", "posteriores"), "mesa_flexora"),
    (("abdutora", "abducao", "gluteo medio"), "cadeira_abdutora"),
]


class AdaptadorRegras:
    """Interpretador heurístico offline (fallback determinístico)."""

    nome = "regras"

    def interpretar(self, briefing: str) -> RequisicaoProjeto:
        txt = _sem_acentos(briefing)

        exercicio = self._detectar_exercicio(txt)
        return RequisicaoProjeto(
            exercicio=exercicio,
            carga_kg=self._detectar_carga(txt),
            percentil=self._detectar_percentil(txt),
            sexo=self._detectar_sexo(txt),
            objetivo_pega=self._detectar_objetivo_pega(txt),
        )

    @staticmethod
    def _detectar_exercicio(txt: str) -> str:
        for palavras, exercicio in _PALAVRAS_EXERCICIO:
            if any(p in txt for p in palavras):
                return exercicio
        # Sem correspondência: usa o primeiro do catálogo como padrão seguro.
        from dechengym.data.exercicios_db import exercicios_disponiveis

        return exercicios_disponiveis()[0]

    @staticmethod
    def _detectar_carga(txt: str) -> float:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*kg", txt)
        if m:
            return float(m.group(1).replace(",", "."))
        return 100.0

    @staticmethod
    def _detectar_percentil(txt: str) -> float:
        m = re.search(r"p(?:ercentil)?\s*[:=]?\s*(\d{1,3})", txt)
        if m:
            return max(5.0, min(95.0, float(m.group(1))))
        return 50.0

    @staticmethod
    def _detectar_sexo(txt: str) -> str:
        if "feminin" in txt or "mulher" in txt:
            return "feminino"
        if "masculin" in txt or "homem" in txt:
            return "masculino"
        return "masculino"

    @staticmethod
    def _detectar_objetivo_pega(txt: str) -> str:
        if "preensao" in txt or "grossa" in txt or "fat grip" in txt:
            return "forca_preensao"
        if "precisao" in txt:
            return "precisao"
        return "conforto"


class AdaptadorAnthropic:
    """Interpretador via Claude (SDK ``anthropic``), com fallback de regras.

    Usa saída estruturada (``messages.parse``) para extrair os parâmetros do
    briefing. Se a interpretação falhar ou retornar um exercício fora do
    catálogo, cai para :class:`AdaptadorRegras`.
    """

    nome = "anthropic"

    def __init__(self, modelo: str = MODELO_PADRAO, api_key: str | None = None):
        self.modelo = modelo
        self._api_key = api_key
        self._fallback = AdaptadorRegras()

    def interpretar(self, briefing: str) -> RequisicaoProjeto:  # pragma: no cover
        try:
            import anthropic
            from pydantic import BaseModel, Field
        except Exception:
            return self._fallback.interpretar(briefing)

        exercicios = sorted(CATALOGO_EXERCICIOS.keys())

        class _Brief(BaseModel):
            exercicio: str = Field(description=f"Um de: {exercicios}")
            carga_kg: float = Field(default=100, description="Carga alvo em kg")
            percentil: float = Field(default=50, description="Percentil (5-95)")
            sexo: str = Field(default="masculino", description="masculino ou feminino")
            objetivo_pega: str = Field(
                default="conforto",
                description="conforto, forca_preensao ou precisao",
            )

        cliente = (
            anthropic.Anthropic(api_key=self._api_key)
            if self._api_key
            else anthropic.Anthropic()
        )
        sistema = (
            "Voce extrai parametros de projeto de uma maquina de musculacao "
            "articulada a partir de um briefing em linguagem natural. Escolha "
            f"o exercicio mais proximo do catalogo: {exercicios}."
        )
        try:
            resp = cliente.messages.parse(
                model=self.modelo,
                max_tokens=1024,
                system=sistema,
                messages=[{"role": "user", "content": briefing}],
                output_format=_Brief,
            )
            dados = resp.parsed_output
        except Exception:
            return self._fallback.interpretar(briefing)

        if dados is None or dados.exercicio not in CATALOGO_EXERCICIOS:
            # Interpretacao invalida: usa o exercicio das regras, demais campos do LLM.
            base = self._fallback.interpretar(briefing)
            return RequisicaoProjeto(
                exercicio=base.exercicio,
                carga_kg=dados.carga_kg if dados else base.carga_kg,
                percentil=dados.percentil if dados else base.percentil,
                sexo=dados.sexo if dados else base.sexo,
                objetivo_pega=dados.objetivo_pega if dados else base.objetivo_pega,
            )

        return RequisicaoProjeto(
            exercicio=dados.exercicio,
            carga_kg=dados.carga_kg,
            percentil=max(5.0, min(95.0, dados.percentil)),
            sexo=dados.sexo if dados.sexo in ("masculino", "feminino") else "masculino",
            objetivo_pega=(
                dados.objetivo_pega
                if dados.objetivo_pega in ("conforto", "forca_preensao", "precisao")
                else "conforto"
            ),
        )


def adaptador_padrao() -> AdaptadorLLM:
    """Escolhe o adaptador: Anthropic se houver credencial+SDK, senão regras."""
    tem_sdk = False
    try:  # pragma: no cover - depende de dependência opcional
        import anthropic  # noqa: F401

        tem_sdk = True
    except Exception:
        tem_sdk = False

    if tem_sdk and os.getenv("ANTHROPIC_API_KEY"):
        return AdaptadorAnthropic()
    return AdaptadorRegras()
