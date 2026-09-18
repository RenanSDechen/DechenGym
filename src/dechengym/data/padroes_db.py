"""
Biblioteca de componentes-padrão (01-PADROES) — desenhos reais de fábrica.
==========================================================================

Componentes reutilizáveis extraídos da pasta ``01-PADROES`` dos projetos do
cliente (códigos PDR/BIBLIOTECA, Fischer, 2008). São as peças que se repetem
em todas as máquinas profissionais — proteções, buchas, pinos, polias,
regulagens e estofados — e que o plano de fabricação DechenGym especifica.

O inventário completo (com todas as cotas extraídas) está em
``docs/referencias/01_padroes_biblioteca.json``.
"""

from __future__ import annotations

from typing import Any

BIBLIOTECA_PADROES: dict[str, dict[str, Any]] = {
    # ---- Articulação e deslizamento -------------------------------------
    "bucha_pino_trava": {
        "codigo": "PDR020", "nome": "Bucha guia do pino trava",
        "categoria": "articulacao",
        "especificacao": "Ø10,8 ±0,2 ext x Ø8,2 +0,3 int, flange Ø13, "
                         "comprimento 38/43 mm, chanfro 0,5x45° — prensada no tubo",
        "funcao": "Guia usinada do pino de regulagem (o pino nunca roça no tubo)",
    },
    "pino_bucha_rolamento": {
        "codigo": "PDR050", "nome": "Pino-bucha p/ rolamento 6202ZZ",
        "categoria": "articulacao",
        "especificacao": "Assento Ø15 (rolamento 6202), furo Ø10, flange Ø19",
        "funcao": "Eixo escalonado que monta rolamento blindado em chapa",
    },
    "bucha_nylon_rolete": {
        "codigo": "PDR015", "nome": "Bucha de nylon + rolete de aço",
        "categoria": "articulacao",
        "especificacao": "Bucha nylon Ø60/Ø42/Ø30x200 chanfro 2x45°; rolete "
                         "Ø20x210 com roscas 3/8\" nas pontas",
        "funcao": "Rolo de apoio acolchoado (tornozelo/joelho) com eixo removível",
    },
    "rolete_nylon_garganta": {
        "codigo": "PDR016", "nome": "Rolete de nylon garganta dupla",
        "categoria": "articulacao",
        "especificacao": "Ø200/Ø100, furo Ø25,1 +0,1, comprimento 150, "
                         "gargantas 30/22,5 com faces a 5°",
        "funcao": "Rolete guia de grande diâmetro (apoio de pernas/deslizamento)",
    },
    # ---- Polias e proteções ----------------------------------------------
    "polia_190": {
        "codigo": "PDR018", "nome": "Polia raiada Ø190 canal V",
        "categoria": "polia",
        "especificacao": "Ø190x20, canal 13 mm a 38°, cubo Ø46 estriado "
                         "(sobre rolamento), raios R70",
        "funcao": "Polia principal do cabo de aço 3/16\"",
    },
    "protetor_polia_disco": {
        "codigo": "BIBLIOTECA-03/PDR003", "nome": "Protetor de polia (disco)",
        "categoria": "protecao",
        "especificacao": "Chapa 3,18: disco Ø110 + pé 50 p/ solda, furo Ø10, "
                         "altura 125 — corte laser sem rebarbas",
        "funcao": "Fecha a lateral da polia: dedo nenhum alcança o cabo",
    },
    "protetor_polia_suporte": {
        "codigo": "BIBLIOTECA-01/PDR006", "nome": "Suporte-protetor de polia superior",
        "categoria": "protecao",
        "especificacao": "Chapa 3,175: 120x165, furo eixo Ø10 a 60 mm, "
                         "recorte 40x60 R5/R30, cantos R20",
        "funcao": "Sustenta a polia superior e protege o ponto de convergência",
    },
    "protetor_roldana_dupla": {
        "codigo": "PDR021", "nome": "Protetor de roldana duplo (formato 8)",
        "categoria": "protecao",
        "especificacao": "Chapa 3,0: 260 mm, 2 discos Ø110, pescoço 50x52",
        "funcao": "Par de roldanas alinhadas em um único protetor",
    },
    "protetor_roldana_giratoria": {
        "codigo": "PDR007", "nome": "Protetor de roldana giratória",
        "categoria": "protecao",
        "especificacao": "Disco Ø110 em garfo (vão 27) sobre bucha-pivô "
                         "Ø21,8/Ø15x55 — o conjunto gira e alinha com o cabo",
        "funcao": "Roldana que se orienta sozinha na direção de tração",
    },
    # ---- Regulagens -------------------------------------------------------
    "coluna_regulagem_banco": {
        "codigo": "PDR024", "nome": "Coluna de regulagem do banco",
        "categoria": "regulagem",
        "especificacao": "Tubo INOX 40x40x1,5x350 com 5 furos Ø13 passo 50 + "
                         "chapa base 200x200x3",
        "funcao": "Regulagem de altura do assento em inox (não descasca)",
    },
    "cremalheira_banco": {
        "codigo": "PDR019", "nome": "Cremalheira de regulagem",
        "categoria": "regulagem",
        "especificacao": "Chapa dentada 140x30 (passo 25) ou 390x30 (passo 60)",
        "funcao": "Regulagem rápida de encosto/banco por apoio de pino",
    },
    "setor_regulagem_15": {
        "codigo": "PDR037", "nome": "Setor de regulagem angular 15°",
        "categoria": "regulagem",
        "especificacao": "Chapa 3/16\": 255 mm, furo-pivô Ø20,5, 6 furos Ø11 "
                         "a cada 15° (arco de 60°), raios R230/R200/R170",
        "funcao": "Posição inicial do braço articulado em 6 posições",
    },
    "pino_seletor_placas": {
        "codigo": "00208", "nome": "Pino seletor da coluna de placas",
        "categoria": "regulagem",
        "especificacao": "Barra Ø22, rosca 3/8\", furos Ø10 por nível, ponta "
                         "cônica 30°, comprimento tabelado por nº de placas",
        "funcao": "Seleção de carga da pilha de tijolos",
    },
    # ---- Engates e acessórios --------------------------------------------
    "gancho_chapa": {
        "codigo": "BIBLIOTECA-06/PDR001", "nome": "Gancho de chapa (engate rápido)",
        "categoria": "engate",
        "especificacao": "Chapa 3/16\": 30x55, rasgo U 14 fundo R7, "
                         "entrada 8x10 a 45°",
        "funcao": "Engate rápido de barras/acessórios no cabo",
    },
    "gancho_roscado_10": {
        "codigo": "PDR010", "nome": "Gancho roscado p/ eixo Ø10",
        "categoria": "engate",
        "especificacao": "100 mm, rosca 3/8\" x40, olhal Ø11 +2/−0",
        "funcao": "Terminal de cabo/tirante na coluna de pesos",
    },
    # ---- Estofados e acabamento ------------------------------------------
    "encosto_profissional": {
        "codigo": "00101", "nome": "Encosto anatômico profissional",
        "categoria": "estofado",
        "especificacao": "450x300, espessura anatômica 30→80 mm, topo R80",
        "funcao": "Encosto com perfil lombar (não é prancha reta)",
    },
    "apoio_braco_injetado": {
        "codigo": "PDR047", "nome": "Apoio de braço injetado (scott)",
        "categoria": "estofado",
        "especificacao": "500x270, perfil L 110/310, espessura 40, cantos R40",
        "funcao": "Apoio de braços injetado de alta densidade",
    },
    "calco_borracha_oblongo": {
        "codigo": "PDR014", "nome": "Tampa/calço de borracha p/ tubo oblongo",
        "categoria": "acabamento",
        "especificacao": "Oval 122x39, altura 50, parede 4, nervuras internas "
                         "R2,5 passo 5 (encaixe sob pressão)",
        "funcao": "Pé de borracha: não risca piso, não desliza, fecha o tubo",
    },
    "chapa_fixacao_haste": {
        "codigo": "PDR005", "nome": "Chapa trapezoidal de fixação de haste",
        "categoria": "estrutura",
        "especificacao": "Chapa 3,0: 250 alt, topo 100/base 50, 2 furos Ø10",
        "funcao": "Fixação triangulada das hastes-guia (gusset funcional)",
    },
    "guia_cabo_340": {
        "codigo": "PDR022", "nome": "Guia do cabo de aço Ø340 (disco-came)",
        "categoria": "came",
        "especificacao": "Chapa 1/4\" Ø340, recorte em S com R30 (saída do "
                         "cabo), corte laser sem rebarbas",
        "funcao": "Disco que enrola o cabo com raio variável — a came real",
    },
}


def get_padrao_biblioteca(chave: str) -> dict[str, Any]:
    """Retorna um componente-padrão da biblioteca pelo identificador."""
    if chave not in BIBLIOTECA_PADROES:
        disponiveis = ", ".join(sorted(BIBLIOTECA_PADROES))
        raise ValueError(f"Componente '{chave}' não encontrado na biblioteca. "
                         f"Disponíveis: {disponiveis}")
    return BIBLIOTECA_PADROES[chave]


def listar_biblioteca_padroes(categoria: str | None = None) -> dict[str, Any]:
    """Lista a biblioteca (opcionalmente filtrada por categoria)."""
    itens = {k: v for k, v in BIBLIOTECA_PADROES.items()
             if categoria is None or v["categoria"] == categoria}
    cats = sorted({v["categoria"] for v in BIBLIOTECA_PADROES.values()})
    return {"total": len(itens), "categorias": cats, "componentes": itens}
