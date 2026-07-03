"""
Módulo de Cálculo Estrutural
============================

Ferramentas (Tools) determinísticas que o LLM orquestrador pode invocar
para dimensionar e validar a estrutura de uma máquina articulada:

- :func:`calc_momento_fletor`          — momento fletor / torque na alavanca.
- :func:`get_especificacao_metalon`    — propriedades físicas de um perfil.
- :func:`validar_resistencia_estrutural` — verifica se o perfil suporta a carga.
- :func:`recomendar_espessura_minima`  — sugere a menor espessura aprovada.

Convenções de unidades
-----------------------
- Força é informada em ``kg`` (massa) e convertida internamente para Newton.
- Distâncias/dimensões em ``mm``.
- Momento fletor / torque em ``N·m``.
- Tensões em ``MPa`` (== N/mm²).
"""

from __future__ import annotations

from typing import Any

from dechengym.config import (
    DENSIDADE_ACO_KG_M3,
    ESPESSURAS_COMERCIAIS_MM,
    FATOR_SEGURANCA_PADRAO,
    GRAVIDADE_MS2,
)
from dechengym.data.metalon_db import CATALOGO_METALON, perfis_disponiveis


# ==========================================================================
# Tool 1 — Momento fletor / torque
# ==========================================================================
def calc_momento_fletor(forca_kg: float, distancia_alavanca_mm: float) -> float:
    """Calcula o momento fletor (torque) gerado por uma carga na alavanca.

    O momento fletor em uma alavanca engastada é o produto da força pela
    distância perpendicular ao ponto de apoio (pivô):

    .. math:: M = F \\cdot d = (m \\cdot g) \\cdot d

    Parameters
    ----------
    forca_kg:
        Massa aplicada na extremidade da alavanca, em quilogramas.
    distancia_alavanca_mm:
        Comprimento do braço de alavanca (distância do pivô ao ponto de
        aplicação da carga), em milímetros.

    Returns
    -------
    float
        Momento fletor em N·m.

    Raises
    ------
    ValueError
        Se a força ou a distância forem negativas.

    Examples
    --------
    >>> round(calc_momento_fletor(100, 800), 3)
    784.532
    """
    if forca_kg < 0:
        raise ValueError("A forca (kg) nao pode ser negativa.")
    if distancia_alavanca_mm < 0:
        raise ValueError("A distancia da alavanca (mm) nao pode ser negativa.")

    forca_newton = forca_kg * GRAVIDADE_MS2
    distancia_m = distancia_alavanca_mm / 1000.0
    return forca_newton * distancia_m


# ==========================================================================
# Propriedades geométricas de seção (uso interno + exposto na especificação)
# ==========================================================================
def _propriedades_secao(base_mm: float, altura_mm: float, espessura_mm: float) -> dict[str, float]:
    """Calcula as propriedades de seção de um tubo retangular vazado.

    Convenção: flexão em torno do eixo horizontal (paralelo à ``base``),
    ou seja, a ``altura`` é a dimensão que resiste à flexão. Retorna área,
    momento de inércia (I), módulo de seção (W) e peso por metro.
    """
    if espessura_mm <= 0:
        raise ValueError("A espessura de parede deve ser positiva.")
    if 2 * espessura_mm >= min(base_mm, altura_mm):
        raise ValueError(
            "Espessura de parede grande demais para as dimensoes do perfil "
            f"({espessura_mm} mm em {base_mm}x{altura_mm})."
        )

    base_interna = base_mm - 2 * espessura_mm
    altura_interna = altura_mm - 2 * espessura_mm

    # Área da seção transversal (mm²): retângulo externo menos o vazio interno.
    area_mm2 = base_mm * altura_mm - base_interna * altura_interna

    # Momento de inércia em torno do eixo neutro horizontal (mm⁴).
    inercia_mm4 = (
        base_mm * altura_mm**3 - base_interna * altura_interna**3
    ) / 12.0

    # Módulo de seção (mm³): W = I / c, com c = altura/2.
    modulo_secao_mm3 = inercia_mm4 / (altura_mm / 2.0)

    # Peso por metro (kg/m): área (m²) × 1 m × densidade.
    area_m2 = area_mm2 * 1e-6
    peso_por_metro_kg = area_m2 * DENSIDADE_ACO_KG_M3

    return {
        "area_secao_mm2": area_mm2,
        "momento_inercia_mm4": inercia_mm4,
        "modulo_secao_mm3": modulo_secao_mm3,
        "peso_por_metro_kg": peso_por_metro_kg,
    }


# ==========================================================================
# Tool 2 — Especificação de metalon
# ==========================================================================
def get_especificacao_metalon(perfil: str, espessura_parede_mm: float) -> dict[str, Any]:
    """Retorna as propriedades físicas de um perfil de metalon comercial.

    Consulta o catálogo mockado (:data:`dechengym.data.metalon_db.CATALOGO_METALON`)
    e calcula as propriedades de seção para a espessura de parede informada.

    Parameters
    ----------
    perfil:
        Notação comercial do perfil, ``"BASExALTURA"`` em mm (ex.: ``"50x50"``).
    espessura_parede_mm:
        Espessura de parede desejada, em mm (ex.: ``1.5``, ``3.0``).

    Returns
    -------
    dict
        Dicionário com dimensões, propriedades de seção, peso por metro,
        material e limite de escoamento.

    Raises
    ------
    KeyError
        Se o perfil não existir no catálogo.
    ValueError
        Se a espessura não estiver disponível para o perfil.

    Examples
    --------
    >>> spec = get_especificacao_metalon("50x50", 3.0)
    >>> round(spec["modulo_secao_mm3"], 1)
    8339.7
    """
    if perfil not in CATALOGO_METALON:
        raise KeyError(
            f"Perfil '{perfil}' nao encontrado no catalogo. "
            f"Disponiveis: {perfis_disponiveis()}"
        )

    registro = CATALOGO_METALON[perfil]

    if espessura_parede_mm not in registro["espessuras_mm"]:
        raise ValueError(
            f"Espessura {espessura_parede_mm} mm indisponivel para o perfil "
            f"'{perfil}'. Espessuras: {list(registro['espessuras_mm'])}"
        )

    props = _propriedades_secao(
        registro["base_mm"], registro["altura_mm"], espessura_parede_mm
    )

    return {
        "perfil": perfil,
        "espessura_parede_mm": espessura_parede_mm,
        "dimensoes_mm": {
            "base": registro["base_mm"],
            "altura": registro["altura_mm"],
        },
        "material": registro["material"],
        "limite_escoamento_mpa": registro["limite_escoamento_mpa"],
        **props,
    }


# ==========================================================================
# Tool 3 — Validação de resistência estrutural
# ==========================================================================
def validar_resistencia_estrutural(
    forca_kg: float,
    distancia_alavanca_mm: float,
    perfil: str,
    espessura_parede_mm: float,
    fator_seguranca: float = FATOR_SEGURANCA_PADRAO,
) -> dict[str, Any]:
    """Valida se um perfil de metalon suporta a carga aplicada na alavanca.

    Fluxo:

    1. Calcula o momento fletor (:func:`calc_momento_fletor`).
    2. Obtém as propriedades do perfil (:func:`get_especificacao_metalon`).
    3. Calcula a tensão de flexão ``σ = M / W``.
    4. Compara com a tensão admissível ``σ_adm = escoamento / fator_seguranca``.
    5. Se reprovado, sugere a menor espessura comercial que aprova.

    Returns
    -------
    dict
        Relatório com ``aprovado`` (bool), tensões, coeficiente de utilização
        e, quando aplicável, a ``espessura_recomendada_mm``.
    """
    if fator_seguranca <= 0:
        raise ValueError("O fator de seguranca deve ser positivo.")

    momento_nm = calc_momento_fletor(forca_kg, distancia_alavanca_mm)
    spec = get_especificacao_metalon(perfil, espessura_parede_mm)

    # σ = M / W  →  converte M para N·mm (×1000) para casar com W em mm³.
    momento_nmm = momento_nm * 1000.0
    tensao_flexao_mpa = momento_nmm / spec["modulo_secao_mm3"]

    tensao_admissivel_mpa = spec["limite_escoamento_mpa"] / fator_seguranca
    aprovado = tensao_flexao_mpa <= tensao_admissivel_mpa

    # Coeficiente de utilização: <1 ok, >1 reprovado.
    coef_utilizacao = tensao_flexao_mpa / tensao_admissivel_mpa

    relatorio: dict[str, Any] = {
        "aprovado": aprovado,
        "perfil": perfil,
        "espessura_parede_mm": espessura_parede_mm,
        "momento_fletor_nm": round(momento_nm, 3),
        "tensao_flexao_mpa": round(tensao_flexao_mpa, 3),
        "tensao_admissivel_mpa": round(tensao_admissivel_mpa, 3),
        "fator_seguranca": fator_seguranca,
        "coef_utilizacao": round(coef_utilizacao, 3),
        "espessura_recomendada_mm": espessura_parede_mm if aprovado else None,
        "mensagem": "",
    }

    if aprovado:
        relatorio["mensagem"] = (
            f"Perfil {perfil} com parede {espessura_parede_mm} mm APROVADO "
            f"(utilizacao {coef_utilizacao:.0%})."
        )
    else:
        recomendada = recomendar_espessura_minima(
            forca_kg, distancia_alavanca_mm, perfil, fator_seguranca
        )
        relatorio["espessura_recomendada_mm"] = recomendada
        if recomendada is not None:
            relatorio["mensagem"] = (
                f"Perfil {perfil} com parede {espessura_parede_mm} mm REPROVADO "
                f"(tensao {tensao_flexao_mpa:.1f} MPa > admissivel "
                f"{tensao_admissivel_mpa:.1f} MPa). "
                f"Espessura minima recomendada: {recomendada} mm."
            )
        else:
            relatorio["mensagem"] = (
                f"Perfil {perfil} REPROVADO em todas as espessuras comerciais. "
                f"Considere um perfil de maior secao."
            )

    return relatorio


# ==========================================================================
# Tool 4 — Recomendação de espessura mínima
# ==========================================================================
def recomendar_espessura_minima(
    forca_kg: float,
    distancia_alavanca_mm: float,
    perfil: str,
    fator_seguranca: float = FATOR_SEGURANCA_PADRAO,
) -> float | None:
    """Sugere a menor espessura comercial que aprova o perfil para a carga.

    Itera as espessuras disponíveis para o perfil (interseção com as
    espessuras comerciais conhecidas), em ordem crescente, e retorna a
    primeira que satisfaz ``σ ≤ σ_adm``.

    Returns
    -------
    float | None
        A menor espessura aprovada (mm), ou ``None`` se nenhuma espessura
        comercial do perfil for suficiente.
    """
    if perfil not in CATALOGO_METALON:
        raise KeyError(
            f"Perfil '{perfil}' nao encontrado no catalogo. "
            f"Disponiveis: {perfis_disponiveis()}"
        )

    registro = CATALOGO_METALON[perfil]
    momento_nmm = calc_momento_fletor(forca_kg, distancia_alavanca_mm) * 1000.0
    tensao_admissivel_mpa = registro["limite_escoamento_mpa"] / fator_seguranca

    # Considera apenas espessuras que são, ao mesmo tempo, disponíveis no
    # perfil e reconhecidas como comerciais — em ordem crescente.
    candidatas = sorted(
        e for e in registro["espessuras_mm"] if e in ESPESSURAS_COMERCIAIS_MM
    )

    for espessura in candidatas:
        props = _propriedades_secao(
            registro["base_mm"], registro["altura_mm"], espessura
        )
        tensao = momento_nmm / props["modulo_secao_mm3"]
        if tensao <= tensao_admissivel_mpa:
            return espessura

    return None
