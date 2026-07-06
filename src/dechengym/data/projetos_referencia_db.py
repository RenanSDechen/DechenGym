"""
Projetos de referência — desenhos reais de fabricação (nível projetista).
========================================================================

Base extraída dos desenhos técnicos fornecidos pelo cliente (pasta
``projetosprontos``: 201-ABDUTOR, 202-ESTAÇÃO, 203-AGACHAMENTO ANILHADO 60°,
204-PECK DECK — pranchas A2/A4 datadas de 2008, material padrão SAE 1020).
Os JSONs completos peça a peça estão em ``docs/referencias/``.

Estes projetos definem o **padrão construtivo profissional** que o gerador
DechenGym reproduz:

- articulações **usinadas com tolerância** (buchas Ø42 +0,05/−0,02, flanges
  mancal, eixos SAE 1045 com canal para anel elástico);
- **regulagens posicionais** por disco de furos (passo 15°) com pino trava
  torneado, ou por fileira de furos Ø13 com passo 30–50 mm em tubo inox;
- estrutura em **tubo oblongo 40x115** (montantes), tubo redondo Ø60 (bases),
  quadrados 50x50/40x40, retangular 70x50, com **cortes em ângulo** listados;
- chapas-reforço (gussets) 3,18 mm, barras chatas 4,76x38, cantoneiras;
- acabamentos e segurança: protetores de polia, calços de borracha,
  amortecimento da pilha de placas, itens comerciais especificados
  (mosquetão, porca 3/4", rolamentos).
"""

from __future__ import annotations

from typing import Any

PROJETOS_REFERENCIA: dict[str, dict[str, Any]] = {
    "abdutor_201": {
        "nome": "Cadeira Abdutora (projeto 201)",
        "tipo": "seletorizada de braços articulados",
        "fonte": "201-ABDUTOR (12 pranchas, SAE 1020)",
        "arquitetura": {
            "coluna": "tubo oblongo 40x115x2, altura 1150 mm",
            "base": "tubo redondo Ø60x1,5, comprimento 1600 mm, travessa 700 mm",
            "bracos": "tubo quadrado 50x50x1,5 a 40° do montante, 480 mm",
            "apoio_pernas": "3 tubos Ø25,4x1,5 espaçados 140 mm (3 posições de almofada)",
        },
        "articulacao": {
            "eixo": "SAE 1045 Ø20x418, canal 1,6x1 p/ anel elástico, rosca 3/8\"",
            "bucha_guia": "Ø48 ext, furo Ø42 +0,05, comprimentos 300/360",
            "flange_mancal": "Ø100 −0,2, furo escalonado Ø42 +0,05/−0,02, 4x Ø8,5 em CDF Ø80",
            "disco_regulagem": "Ø300 x 1/2\", furos de regulagem a cada 15° em R114",
            "disco_do_braco": "Ø187x14 usinado, canais R3/R1,5 na borda",
            "pino_trava": "SAE 1045 Ø15x320, ponta cônica 15°, rosca 3/8\" p/ manípulo",
        },
        "regulagens": ["abertura inicial dos braços: disco de furos 15° + pino trava",
                       "posição da almofada de perna: 3 tubos Ø25,4 (eixo Ø20/Ø15 encaixável)"],
        "footprint_mm": [1600, 700],
        "altura_mm": 1150,
    },
    "estacao_202": {
        "nome": "Estação de Musculação (projeto 202)",
        "tipo": "multi-estação com coluna de placas e polias",
        "fonte": "202-ESTAÇÃO (12 pranchas, SAE 1020)",
        "arquitetura": {
            "viga_principal": "1850 mm; coluna 940-960 mm; base 750 mm",
            "bracos": "tubo Ø25,4x1,5 x1810 com luva Ø38x193, curva R175",
            "coluna_placas": "9 tijolinhos ferro fundido 250x120x25 + placa-guia superior",
        },
        "articulacao": {
            "buchas": "Ø42 ext, furo Ø35 +0,05/−0 (x51 e x68); escalonada Ø35/Ø33",
            "suporte": "chapa dobrada 3,18 + hastes 50x20, chanfro 5x45°",
        },
        "carga": {
            "placas": "ferro fundido 250x120x25, furos-guia Ø45 escareados p/ Ø35, "
                      "furo central Ø32 com rasgo 10x10",
            "seletor": "barra chata 1/8\"x1\" x350, 9 furos Ø11 passo 27, ponta 20°",
            "amortecimento": "fita de borracha 1 mm sob a placa-guia superior",
            "engates": "gancho rosca 3/8\" abertura Ø11 +2/−0; mosquetão comercial 60x12",
            "acessorios": "barra longa 900+180 dobradas; barra curta 350; "
                          "tornozeleira fita Kevlar 50x650 + argola 1/2 lua 2\"",
        },
        "footprint_mm": [1850, 750],
        "altura_mm": 2100,
    },
    "agachamento_203": {
        "nome": "Agachamento Anilhado 60° / Hack (projeto 203)",
        "tipo": "anilhada guiada a 60°",
        "fonte": "203-AGACHAMENTO ANILHADO (2 pranchas A2 com BOM, SAE 1020)",
        "arquitetura": {
            "trilhos": "1950 mm a 30° da vertical (rampa 60°)",
            "base": "1300 mm; plataforma 500x500 com chapa xadrez/corrugada 3,18",
            "bracos": "700 mm com pinos porta-anilha Ø50, ombreiras 900 mm",
            "tubos": "oblongo 40x115; quadrados; redondo Ø38x1,5; cantoneira 1 1/2\"",
        },
        "articulacao": {
            "buchas": "nylon cônicas Ø43 +0,05 / Ø66, 4 peças (deslizamento nos trilhos)",
            "eixos": "SAE 1010/1045 Ø22x380 e Ø20x390 3/8\"",
            "barras_chata": "4,75x38 (detalhes de fixação), porca 3/4\"",
        },
        "regulagens": ["ganchos de segurança em fileira de furos Ø13 passo 30 mm "
                       "em chapa inox (detalhe 5: 200 mm, 4 furos)"],
        "footprint_mm": [1300, 900],
        "altura_mm": 1690,
    },
    "peck_deck_204": {
        "nome": "Peck Deck / Voador (projeto 204)",
        "tipo": "articulada com came e coluna de placas",
        "fonte": "204-PECK DECK (4 pranchas com BOM de 32 itens, SAE 1020/1045/inox)",
        "arquitetura": {
            "base": "tubo redondo Ø60 x3700 (dobrado em quadro) + retangular 70x50x1,5 x680",
            "coluna": "tubo oblongo 40x115x1,5 (1295 mm) + 50x50x1,5 x1730 cortes 8°/8°",
            "encosto": "inclinação 9°; assento em chapa 3,18x200x200",
            "bracos": "tubo Ø38 com dobra R172, segmentos 360+350, exc. 430, comp. 805",
        },
        "came": {
            "disco": "Ø340 SAE 1020, 2 peças (uma por braço) — perfil espiral com recorte",
            "eixos": "SAE 1045 Ø20x235/335 escalonados Ø20/Ø18/Ø16, rosca 4,37",
            "buchas": "1 1/2\" sch80 x133; Ø38 sch40 x55; Ø42/Ø48x130; "
                      "Ø38/Ø25,5 rosca 3/8\"; Ø20/Ø13 rosca 5/16\"",
        },
        "regulagens": ["batentes/posição inicial: tubos inox 40x40x2 com furos Ø13 "
                       "passo 30 (x250) e passo 50 (x350)"],
        "reforcos": "chapas trapezoidais 3,18x140x140 cortadas a 18° (gussets)",
        "footprint_mm": [1700, 700],
        "altura_mm": 1280,
    },
    "leg_press_45_208": {
        "nome": "Leg Press 45° (projeto 208)",
        "tipo": "anilhada guiada, carrinho deslizante",
        "fonte": "208 (3 pranchas, BOM de 36 itens, SAE 1020/1045/inox)",
        "arquitetura": {
            "trilhos": "viga U 3\" x2000 a 45°, cortes 45°",
            "torre": "largura 700, vão interno 535, altura ~1800",
            "carrinho": "quadro 800x515; placa dos pés 500x480 com pivô "
                        "Ø20 0/−0,05; eixos SAE 1045 Ø20x680-690",
            "porta_anilhas": "tubo oblongo 40x115x1,5 x1810 (2x)",
        },
        "deslizamento": {
            "buchas": "nylon Ø66x30, rebaixo Ø42, conicidade 8° (4x) — correm "
                      "DENTRO da viga U; sem rodízios",
            "eixos": "SAE 1045 Ø20/Ø28 escalonados",
        },
        "seguranca": {
            "trava": "alavanca de destrave em chapa (chanfro 15x45°) + "
                     "manípulo Ø25,4 curvado R80",
            "regulagem": "chapa INOX 40x200 com 3 furos Ø13 passo 30",
            "guia": "porca 3/4\" soldada em guia (fuso de batente)",
        },
        "footprint_mm": [1200, 2200],
        "altura_mm": 1800,
    },
    "hack_45_209": {
        "nome": "Agachamento/Hack 45° (projeto 209)",
        "tipo": "anilhada guiada, carrinho de ombros",
        "fonte": "209 (3 pranchas, BOM de 33 linhas, SAE 1020/ABNT-1010/inox)",
        "arquitetura": {
            "trilhos": "viga U 3\" x1950 a 45°, buchas afastadas 700",
            "carrinho": "1300 mm, quadro 750 (travessas 3x250), ombreiras a "
                        "10°, 3 almofadas de encosto + apoio lombar",
            "apoio_pes": "plataforma 500x500 em chapa corrugada 3 mm",
            "porta_anilhas": "tubo oblongo 40x115 x1595 (2x)",
        },
        "deslizamento": {
            "buchas": "nylon Ø66/Ø42 +0,05 x30, cônicas ~6° (4x)",
            "eixos": "Ø22x380 pontas Ø20 (2x) + Ø20x390 rosca 3/8\" (1x)",
        },
        "seguranca": {
            "trava": "braços de destrave dir+esq em tubo Ø25,4 (corpo 700, "
                     "dobra 90°, pega 100) com ganchos 5x31 que apoiam nos "
                     "batentes das colunas",
            "regulagem": "chapa INOX 40x200 com furos Ø13 passo 30",
        },
        "footprint_mm": [1585, 900],
        "altura_mm": 1690,
    },
    "suporte_dumbbells_205": {
        "nome": "Suporte de Dumbbells (projeto 205)",
        "tipo": "rack de piso, 2 níveis",
        "fonte": "205 (1 prancha com BOM, SAE 1020)",
        "arquitetura": {
            "trilhos": "cantoneira 50x50x3 x1200 (4x), bandejas inclinadas "
                       "(cortes das colunas a 15°)",
            "estrutura": "tubo 40x40x1,5 (pés 450, travessa 1000) + "
                         "30x50x1,5 (colunas 650/350, apoios 230)",
        },
        "footprint_mm": [1200, 450],
        "altura_mm": 650,
    },
    "suporte_barras_206": {
        "nome": "Cavalete p/ Barras (projeto 206)",
        "tipo": "rack de piso horizontal",
        "fonte": "206 (1 prancha, SAE 1020)",
        "arquitetura": {
            "bracos": "40x40x1,5 x550 com gancho em barra chata 5x38x195 "
                      "dobrada a 66° (abas 53/50)",
            "acabamento": "ponteiras de borracha 40x40 nas extremidades",
        },
        "footprint_mm": [550, 350],
        "altura_mm": 600,
    },
    "suporte_barras_vertical_207": {
        "nome": "Suporte Vertical p/ 6 Barras (projeto 207)",
        "tipo": "rack de piso vertical",
        "fonte": "207 (1 prancha com BOM, SAE 1020 + pinos SAE 1045)",
        "arquitetura": {
            "colunas": "40x40x1,5 x820, altura total 860",
            "porta_barras": "travessa furada 6x Ø32 passo 82 (embaixo) + "
                            "12 pinos Ø1/4\"x65 separadores (em cima)",
        },
        "footprint_mm": [550, 400],
        "altura_mm": 860,
    },
    "arco_210": {
        "nome": "Arco / apoio abdominal (projeto 210)",
        "tipo": "banco em arco",
        "fonte": "210 (2 pranchas com BOM, SAE 1020/ABNT-1010)",
        "arquitetura": {
            "chassi": "2 quadros em J: tubo Ø38x1,5 x1500 curvado R175, "
                      "altura 600, bases 475/669",
            "uniao": "transversais Ø25,4 x620/x610, parafusos passantes Ø10",
            "cabeceira": "chapa 100x100x3 + flange Ø100/Ø80 esp. 10",
        },
        "footprint_mm": [1500, 700],
        "altura_mm": 600,
    },
}


# Padrões construtivos transversais (o "DNA" comum aos 4 projetos) ---------

PADROES_CONSTRUTIVOS: dict[str, dict[str, Any]] = {
    "articulacao_usinada": {
        "descricao": "Articulação em bucha usinada + eixo SAE 1045 (nunca furo no tubo)",
        "especificacao": "Bucha Ø42/Ø48 com furo toleranciado +0,05/−0,02; eixo "
                         "escalonado com canal 1,6x1 p/ anel elástico e rosca 3/8\"; "
                         "flange mancal aparafusada (4x Ø8,5 em CDF Ø80)",
        "origem": "201-04/05/06/07, 202-08, 204-01",
    },
    "regulagem_disco_pino": {
        "descricao": "Regulagem angular por disco de furos + pino trava torneado",
        "especificacao": "Disco Ø300x1/2\" com furos a cada 15° em R114; pino SAE 1045 "
                         "Ø15x320 com ponta cônica 15° e manípulo roscado 3/8\"",
        "origem": "201-06/08",
    },
    "regulagem_furos_inox": {
        "descricao": "Regulagem linear por fileira de furos em tubo/chapa inox",
        "especificacao": "Tubo inox 40x40x2 ou chapa inox com furos Ø13, passo 30-50 mm",
        "origem": "203-02 det.5, 204-02",
    },
    "gusset_trapezoidal": {
        "descricao": "Chapa-reforço trapezoidal em todo nó soldado de carga",
        "especificacao": "Chapa 3,18 mm, 140x140 (corte a 18°) ou 225x225x50",
        "origem": "204-03 item 19, 201-01",
    },
    "amortecimento_borracha": {
        "descricao": "Borracha em todo fim de curso e apoio",
        "especificacao": "Calço de borracha nos pés; fita de borracha 1 mm sob a "
                         "placa-guia da pilha; roletes/buchas de nylon",
        "origem": "01-PADROES (CALÇO BORRACHA), 202-10, 203 (bucha nylon)",
    },
    "protecao_movel": {
        "descricao": "Protetor em toda polia/roldana e pilha de placas",
        "especificacao": "Protetores de polia dedicados (biblioteca 01-PADROES, "
                         "5 variantes) e carenagem da coluna de tijolos",
        "origem": "01-PADROES (PROTEÇÃO POLIA 3/4/5, PROTETOR ROLDANA)",
    },
    "deslizamento_viga_u": {
        "descricao": "Deslizamento linear por buchas cônicas de nylon em viga U",
        "especificacao": "Buchas nylon Ø66x30 (rebaixo Ø42 +0,05, conicidade "
                         "6-8°) sobre eixos SAE 1045, correndo dentro de viga "
                         "U 3\" — sem rodízios nem trilho comercial",
        "origem": "208-02 item 8, 209-01 det. bucha",
    },
    "trava_seguranca": {
        "descricao": "Destrave de segurança por braço rotativo com ganchos",
        "especificacao": "Braços dir+esq em tubo Ø25,4 (dobra 90°, pega 100) "
                         "com ganchos de barra 5x31 apoiando em batentes; "
                         "alavanca com chanfro 15x45° no leg press",
        "origem": "209-01 braço destrave, 208-01 trava",
    },
    "itens_comerciais": {
        "descricao": "Itens de mercado especificados, não fabricados",
        "especificacao": "Mosquetão 60x12; porca 3/4\"; anéis elásticos; manípulos; "
                         "rolamentos blindados 2RS",
        "origem": "202-08, 201-11, especificação industrial do cliente",
    },
    "cortes_em_angulo": {
        "descricao": "Lista de corte com ângulos explícitos por item",
        "especificacao": "Cortes 8°/8°, 45°/53°, 2°30', 20°/20° indicados na BOM — "
                         "encaixe sem fresta para solda MIG",
        "origem": "204-03, 201-11",
    },
}


def get_projeto_referencia(nome: str) -> dict[str, Any]:
    """Retorna um projeto de referência pelo identificador."""
    if nome not in PROJETOS_REFERENCIA:
        disponiveis = ", ".join(sorted(PROJETOS_REFERENCIA))
        raise ValueError(f"Projeto de referência '{nome}' não encontrado. "
                         f"Disponíveis: {disponiveis}")
    return PROJETOS_REFERENCIA[nome]


def listar_padroes_construtivos() -> dict[str, Any]:
    """Padrões construtivos transversais extraídos dos projetos reais."""
    return {"padroes": PADROES_CONSTRUTIVOS,
            "projetos": {k: v["nome"] for k, v in PROJETOS_REFERENCIA.items()}}
