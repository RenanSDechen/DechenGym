"""
Núcleo determinístico do projeto de máquina.
============================================

:func:`projetar_maquina` recebe uma :class:`RequisicaoProjeto` estruturada e
percorre o pipeline completo, produzindo um projeto validado:

1. **Ergonomia** — envelope do exercício (pivô, ADM, pegada, ajustes).
2. **Came** — síntese do perfil de resistência variável + prova do casamento.
3. **Estrutura** — validação com **autocorreção** da espessura de parede.
4. **Geometria** — script OpenSCAD + memorial descritivo.
5. **Imagem** — preview SVG e prompt para modelo de imagem.

É puro e determinístico — sem qualquer dependência de LLM — e portanto
inteiramente testável.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from dechengym.calculo_estrutural import validar_resistencia_estrutural
from dechengym.config import ESPESSURAS_COMERCIAIS_MM, FATOR_SEGURANCA_PADRAO
from dechengym.data.metalon_db import CATALOGO_METALON
from dechengym.ergonomia import avaliar_curva_resistencia, projetar_ergonomia
from dechengym.geracao_imagem import gerar_preview_svg, montar_prompt_imagem_produto
from dechengym.geracao_openscad import (
    gerar_memorial_descritivo,
    gerar_script_openscad,
    parametros_geometria_de_ergonomia,
)
from dechengym.sintese_came import (
    calcular_resistencia_came,
    gerar_came_openscad,
    gerar_came_svg,
    sintetizar_came_de_ergonomia,
)


@dataclass
class RequisicaoProjeto:
    """Parâmetros estruturados de um projeto de máquina articulada."""

    exercicio: str
    carga_kg: float = 100.0
    percentil: float = 50.0
    sexo: str = "masculino"
    objetivo_pega: str = "conforto"
    comprimento_alavanca_mm: float = 400.0
    perfil: str = "50x50"
    fator_seguranca: float = FATOR_SEGURANCA_PADRAO
    raio_max_came_mm: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _autocorrigir_estrutura(req: RequisicaoProjeto) -> dict[str, Any]:
    """Escolhe a menor espessura de parede que aprova a alavanca.

    Itera as espessuras comerciais do perfil (autocorreção) até a estrutura
    passar, registrando cada tentativa — o comportamento "de agente" do
    pipeline: propor → validar → ajustar → convergir.
    """
    if req.perfil not in CATALOGO_METALON:
        raise KeyError(f"Perfil '{req.perfil}' fora do catalogo.")

    registro = CATALOGO_METALON[req.perfil]
    espessuras = sorted(
        e for e in registro["espessuras_mm"] if e in ESPESSURAS_COMERCIAIS_MM
    )

    historico: list[dict[str, Any]] = []
    escolhida: float | None = None
    relatorio_final: dict[str, Any] | None = None

    for espessura in espessuras:
        rel = validar_resistencia_estrutural(
            req.carga_kg,
            req.comprimento_alavanca_mm,
            req.perfil,
            espessura,
            req.fator_seguranca,
        )
        historico.append(
            {
                "espessura_parede_mm": espessura,
                "aprovado": rel["aprovado"],
                "coef_utilizacao": rel["coef_utilizacao"],
            }
        )
        if rel["aprovado"]:
            escolhida = espessura
            relatorio_final = rel
            break

    if relatorio_final is None:  # nenhuma espessura aprovou
        relatorio_final = validar_resistencia_estrutural(
            req.carga_kg,
            req.comprimento_alavanca_mm,
            req.perfil,
            espessuras[-1],
            req.fator_seguranca,
        )

    return {
        "aprovado": escolhida is not None,
        "espessura_escolhida_mm": escolhida,
        "iteracoes": historico,
        "relatorio": relatorio_final,
    }


def projetar_maquina(requisicao: RequisicaoProjeto) -> dict[str, Any]:
    """Executa o pipeline completo e retorna o projeto validado.

    Returns
    -------
    dict
        ``{"requisicao", "ergonomia", "came", "estrutura", "geometria",
        "imagem", "aprovado", "resumo"}``.
    """
    req = requisicao

    # 1) Ergonomia --------------------------------------------------------
    ergonomia = projetar_ergonomia(
        req.exercicio,
        percentil=req.percentil,
        sexo=req.sexo,
        carga_pico_kg=req.carga_kg,
        objetivo_pega=req.objetivo_pega,
    )

    # 2) Came (síntese + prova do casamento) ------------------------------
    perfil_came = sintetizar_came_de_ergonomia(
        ergonomia, raio_max_mm=req.raio_max_came_mm
    )
    resistencia_came = calcular_resistencia_came(perfil_came, req.carga_kg)
    avaliacao_came = avaliar_curva_resistencia(
        resistencia_came["torque_nm"], ergonomia["grupo_muscular"]
    )

    # 3) Estrutura (autocorreção) -----------------------------------------
    estrutura = _autocorrigir_estrutura(req)
    espessura = estrutura["espessura_escolhida_mm"] or CATALOGO_METALON[req.perfil][
        "espessuras_mm"
    ][-1]

    # 4) Geometria (nasce alinhada à ergonomia + estrutura validada) ------
    lado = int(req.perfil.split("x")[0])
    parametros = parametros_geometria_de_ergonomia(
        ergonomia,
        extras={
            "comprimento_alavanca_mm": req.comprimento_alavanca_mm,
            "espessura_parede_mm": espessura,
            "perfil_base_mm": lado,
            "perfil_coluna_mm": lado,
            "perfil_alavanca_mm": lado,
        },
    )
    scad = gerar_script_openscad(parametros)
    memorial = gerar_memorial_descritivo(parametros)

    # 5) Imagem -----------------------------------------------------------
    adm = ergonomia["amplitude_movimento"]["adm_treino"]
    preview_svg = gerar_preview_svg(
        parametros, angulo_inicial_graus=adm[0], angulo_final_graus=min(adm[1], 90)
    )
    came_svg = gerar_came_svg(perfil_came)
    came_scad = gerar_came_openscad(perfil_came, espessura_mm=12.0)
    prompt_imagem = montar_prompt_imagem_produto(parametros, envelope_ergonomico=ergonomia)

    aprovado = estrutura["aprovado"] and avaliacao_came["pontuacao"] >= 90.0

    resumo = (
        f"{ergonomia['nome']}: pivo {ergonomia['alinhamento_pivo']['altura_pivo_mm']} mm, "
        f"pega {ergonomia['pegada']['orientacao']['orientacao']} "
        f"Ø{ergonomia['pegada']['diametro']['diametro_recomendado_mm']} mm, "
        f"came {perfil_came['tipo_curva']} (casamento {avaliacao_came['pontuacao']}/100), "
        f"perfil {req.perfil} parede "
        f"{estrutura['espessura_escolhida_mm'] or '—'} mm "
        f"({'APROVADO' if aprovado else 'REVISAR'})."
    )

    return _montar_projeto(
        req, ergonomia, perfil_came, resistencia_came, avaliacao_came,
        came_scad, came_svg, estrutura, parametros, scad, memorial,
        preview_svg, prompt_imagem, aprovado, resumo,
    )


def projetar_maquina_params(exercicio: str, **campos: Any) -> dict[str, Any]:
    """Atalho por argumentos nomeados (para o registro de Tools).

    Constrói uma :class:`RequisicaoProjeto` a partir dos campos e delega a
    :func:`projetar_maquina`.
    """
    return projetar_maquina(RequisicaoProjeto(exercicio=exercicio, **campos))


def _montar_projeto(
    req, ergonomia, perfil_came, resistencia_came, avaliacao_came, came_scad,
    came_svg, estrutura, parametros, scad, memorial, preview_svg, prompt_imagem,
    aprovado, resumo,
) -> dict[str, Any]:
    return {
        "requisicao": req.to_dict(),
        "ergonomia": ergonomia,
        "came": {
            "perfil": perfil_came,
            "resistencia": resistencia_came,
            "avaliacao": avaliacao_came,
            "openscad": came_scad,
            "svg": came_svg,
        },
        "estrutura": estrutura,
        "geometria": {
            "parametros": parametros,
            "openscad": scad,
            "memorial": memorial,
        },
        "imagem": {
            "preview_svg": preview_svg,
            "prompt_produto": prompt_imagem,
        },
        "aprovado": aprovado,
        "resumo": resumo,
    }
