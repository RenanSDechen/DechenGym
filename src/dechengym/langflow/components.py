"""
Esqueleto de custom components para Langflow.
============================================

Este módulo mostra *como* as Tools do DechenGym podem ser expostas como
componentes de um fluxo Langflow, sem tornar o Langflow uma dependência
obrigatória do core.

O import do Langflow é adiado/protegido: se a biblioteca não estiver
instalada, o módulo continua importável (útil para testes do core), mas os
componentes só podem ser instanciados quando o Langflow existir.

Para usar de fato:

    pip install langflow
    # e então descomente/importe estes componentes no seu projeto Langflow.

Referência: cada componente Langflow herda de ``Component``, declara
``inputs``/``outputs`` e implementa o método de build que chama a função
pura correspondente do core.
"""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover - depende de dependência opcional
    from langflow.custom import Component
    from langflow.io import FloatInput, MessageTextInput, Output

    LANGFLOW_DISPONIVEL = True
except Exception:  # Langflow não instalado: fornecemos stubs mínimos.
    LANGFLOW_DISPONIVEL = False

    class Component:  # type: ignore[no-redef]
        """Stub de ``langflow.custom.Component`` (Langflow ausente)."""

    def _stub(*_args: Any, **_kwargs: Any):  # type: ignore[no-redef]
        raise RuntimeError(
            "Langflow nao esta instalado. Rode 'pip install langflow' para "
            "usar os custom components."
        )

    FloatInput = MessageTextInput = Output = _stub  # type: ignore[assignment]


from dechengym.calculo_estrutural import (
    calc_momento_fletor,
    validar_resistencia_estrutural,
)
from dechengym.geracao_openscad import gerar_script_openscad


class MomentoFletorComponent(Component):
    """Componente Langflow: cálculo de momento fletor."""

    display_name = "DechenGym - Momento Fletor"
    description = "Calcula o momento fletor (N.m) de uma alavanca."
    icon = "calculator"

    inputs = [
        FloatInput(name="forca_kg", display_name="Forca (kg)"),
        FloatInput(name="distancia_alavanca_mm", display_name="Alavanca (mm)"),
    ]
    outputs = [Output(name="momento_nm", display_name="Momento (N.m)", method="build")]

    def build(self) -> float:  # pragma: no cover - requer runtime do Langflow
        return calc_momento_fletor(self.forca_kg, self.distancia_alavanca_mm)


class ValidacaoEstruturalComponent(Component):
    """Componente Langflow: validação de resistência estrutural."""

    display_name = "DechenGym - Validacao Estrutural"
    description = "Valida se um perfil de metalon suporta a carga da alavanca."
    icon = "shield-check"

    inputs = [
        FloatInput(name="forca_kg", display_name="Forca (kg)"),
        FloatInput(name="distancia_alavanca_mm", display_name="Alavanca (mm)"),
        MessageTextInput(name="perfil", display_name="Perfil (ex.: 50x50)"),
        FloatInput(name="espessura_parede_mm", display_name="Parede (mm)"),
    ]
    outputs = [Output(name="relatorio", display_name="Relatorio", method="build")]

    def build(self) -> dict:  # pragma: no cover - requer runtime do Langflow
        return validar_resistencia_estrutural(
            self.forca_kg,
            self.distancia_alavanca_mm,
            self.perfil,
            self.espessura_parede_mm,
        )


class OpenScadComponent(Component):
    """Componente Langflow: geração do script OpenSCAD."""

    display_name = "DechenGym - Gerar OpenSCAD"
    description = "Gera o codigo OpenSCAD parametrico da maquina articulada."
    icon = "file-code"

    inputs = [
        MessageTextInput(
            name="parametros_json",
            display_name="Parametros (JSON)",
            info="Dicionario de geometria serializado em JSON.",
        ),
    ]
    outputs = [Output(name="scad", display_name="Script .scad", method="build")]

    def build(self) -> str:  # pragma: no cover - requer runtime do Langflow
        import json

        parametros = json.loads(self.parametros_json) if self.parametros_json else {}
        return gerar_script_openscad(parametros)
