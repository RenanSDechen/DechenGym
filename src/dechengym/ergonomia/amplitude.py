"""
Amplitude de movimento (ADM / ROM).
===================================

Ferramentas para consultar a amplitude articular segura e para validar se o
curso projetado do braço articulado permanece dentro da faixa recomendada
de treino — o critério ergonômico central da máquina.
"""

from __future__ import annotations

from typing import Any

from dechengym.data.adm_db import ADM, articulacoes_disponiveis


def get_amplitude_movimento(articulacao: str, movimento: str) -> dict[str, Any]:
    """Retorna a amplitude de movimento (graus) de uma articulação.

    Parameters
    ----------
    articulacao:
        Ex.: ``"cotovelo"``, ``"joelho"``, ``"ombro"``, ``"quadril"``.
    movimento:
        Ex.: ``"flexao"``, ``"extensao"``, ``"abducao"``.

    Returns
    -------
    dict
        ``{"articulacao", "movimento", "adm_anatomica", "adm_treino",
        "amplitude_treino_graus", "descricao"}``.

    Raises
    ------
    KeyError
        Se a articulação ou o movimento não existirem.
    """
    if articulacao not in ADM:
        raise KeyError(
            f"Articulacao '{articulacao}' invalida. Use: {articulacoes_disponiveis()}"
        )
    if movimento not in ADM[articulacao]:
        raise KeyError(
            f"Movimento '{movimento}' invalido para '{articulacao}'. "
            f"Use: {sorted(ADM[articulacao].keys())}"
        )

    dados = ADM[articulacao][movimento]
    treino_min, treino_max = dados["adm_treino"]
    return {
        "articulacao": articulacao,
        "movimento": movimento,
        "adm_anatomica": list(dados["adm_anatomica"]),
        "adm_treino": list(dados["adm_treino"]),
        "amplitude_treino_graus": round(treino_max - treino_min, 1),
        "descricao": dados["descricao"],
    }


def validar_amplitude_projetada(
    articulacao: str,
    movimento: str,
    angulo_inicial_graus: float,
    angulo_final_graus: float,
) -> dict[str, Any]:
    """Valida se o curso projetado da máquina respeita a ADM de treino.

    Compara o arco ``[angulo_inicial, angulo_final]`` que o braço articulado
    percorrerá com a faixa recomendada de treino. Reprova (e avisa) se o
    curso ultrapassa os limites seguros; sugere o ajuste (*clamp*).

    Returns
    -------
    dict
        Relatório com ``aprovado`` (bool), a faixa recomendada, eventuais
        violações e a sugestão de arco corrigido.
    """
    info = get_amplitude_movimento(articulacao, movimento)
    rec_min, rec_max = info["adm_treino"]

    ini = min(angulo_inicial_graus, angulo_final_graus)
    fim = max(angulo_inicial_graus, angulo_final_graus)

    violacoes: list[str] = []
    if ini < rec_min:
        violacoes.append(
            f"inicio {ini} graus abaixo do minimo recomendado ({rec_min} graus)"
        )
    if fim > rec_max:
        violacoes.append(
            f"fim {fim} graus acima do maximo recomendado ({rec_max} graus)"
        )

    aprovado = not violacoes
    # Clampa cada extremo DENTRO de [rec_min, rec_max]. Como o clamp é
    # monotônico e ini <= fim, o arco sugerido nunca fica invertido — mesmo
    # quando todo o arco projetado cai fora da faixa (ex.: 50-60 em 0-45).
    def _clamp(v: float) -> float:
        return min(max(v, rec_min), rec_max)

    sugestao_ini = _clamp(ini)
    sugestao_fim = _clamp(fim)

    return {
        "aprovado": aprovado,
        "articulacao": articulacao,
        "movimento": movimento,
        "arco_projetado_graus": [ini, fim],
        "adm_treino_graus": [rec_min, rec_max],
        "violacoes": violacoes,
        "arco_sugerido_graus": [sugestao_ini, sugestao_fim],
        "mensagem": (
            f"Curso {ini}-{fim} graus APROVADO (dentro da ADM de treino)."
            if aprovado
            else "Curso REPROVADO: "
            + "; ".join(violacoes)
            + f". Sugerido: {sugestao_ini}-{sugestao_fim} graus."
        ),
    }
