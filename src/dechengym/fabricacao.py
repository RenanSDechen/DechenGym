"""
Módulo de Plano de Fabricação Industrial
========================================

Consolida as **especificações de fabricação de nível industrial** — cruzadas
de memoriais descritivos de máquinas comerciais topo de linha — no pacote que
se entrega a um projetista CAD ou serralheiro industrial:

- perfis retangulares de aço (75x35 / 80x40, parede 2,0–3,0 mm);
- berços de articulação em chapa maciça SAE 1020 de 3/8" (9,525 mm),
  cortados a laser;
- eixos usinados em torno CNC com rolamentos blindados (sem buchas);
- bases de estofados em chapa 1020 de 4 mm + reforço de coluna até 10 mm;
- cremalheira dentada em inox 3 mm para regulagem do assento;
- processos: solda MIG, banho antioxidante e pintura eletrostática a pó.

A partir dos **projetos de referência reais** (desenhos 201/202/203/204 —
ver :mod:`dechengym.data.projetos_referencia_db`), o plano incorpora o pacote
de articulação usinada (flange mancal toleranciada, eixo SAE 1045 com canal
de anel elástico), a regulagem por disco de furos 15° + pino trava torneado
com bucha-guia, os gussets de chapa 3,18 e os calços de borracha nervurados —
os itens que separam uma máquina de linha profissional de um tubo soldado.
"""

from __future__ import annotations

from typing import Any

from dechengym.data.padroes_db import BIBLIOTECA_PADROES
from dechengym.data.projetos_referencia_db import PADROES_CONSTRUTIVOS

#: Processos obrigatórios de fabricação e acabamento.
PROCESSOS_FABRICACAO: list[dict[str, str]] = [
    {
        "processo": "Solda MIG",
        "aplicacao": "Todas as junções estruturais do esqueleto",
        "justificativa": "Penetração profunda e segurança nas juntas de alta tensão",
    },
    {
        "processo": "Corte a laser",
        "aplicacao": "Berços de articulação e chapas de tensão",
        "justificativa": "Precisão dimensional nos furos de eixo e fixações",
    },
    {
        "processo": "Usinagem em torno CNC",
        "aplicacao": "Eixos de articulação",
        "justificativa": "Tolerância de montagem com rolamentos blindados",
    },
    {
        "processo": "Banho antioxidante + pintura eletrostática a pó",
        "aplicacao": "Todos os componentes de aço",
        "justificativa": "Acabamento fosco de alto nível e proteção anticorrosiva",
    },
]


def gerar_plano_fabricacao(
    requisicao: dict[str, Any] | None = None,
    iso_lateral: bool = True,
) -> dict[str, Any]:
    """Gera o plano de fabricação industrial da máquina articulada.

    Parameters
    ----------
    requisicao:
        Dicionário da requisição do projeto (usa ``perfil`` e
        ``fator_seguranca`` quando presentes).
    iso_lateral:
        Máquina de dois braços independentes (dobra itens por braço).

    Returns
    -------
    dict
        ``{"estrutura", "componentes", "processos", "dimensoes_gerais"}`` —
        pronto para o memorial, o dossiê PDF e o repasse ao serralheiro.
    """
    req = requisicao or {}
    perfil = req.get("perfil", "40x80")
    n_bracos = 2 if iso_lateral else 1

    estrutura = {
        "perfil_principal": perfil,
        "observacao_perfil": (
            "Perfil retangular de aco (metalon industrial 75x35 ou 80x40); "
            "parede minima 2,00-3,00 mm. Orientar a alma maior na vertical "
            "nos membros sujeitos a flexao (alavancas e colunas)."
        ),
        "footprint_mm": [1200, 1500],
        "altura_maxima_hastes_mm": 1800,
        "base": "Base larga em V para estabilidade lateral, soldada",
    }

    componentes = [
        {
            "item": "Berco de articulacao (chapa de tensao)",
            "material": "Chapa maciça aco carbono SAE 1020",
            "espessura_mm": 9.525,
            "processo": "Corte a laser",
            "quantidade": 2 * n_bracos,
            "nota": '3/8" de polegada; recebe o eixo do braco articulado',
        },
        {
            "item": "Eixo de articulacao",
            "material": "Aco usinado em torno CNC",
            "espessura_mm": None,
            "processo": "Usinagem CNC + rolamentos blindados (sem buchas plasticas)",
            "quantidade": n_bracos,
            "nota": "Movimento liso; 2 rolamentos blindados por eixo",
        },
        {
            "item": "Rolamento blindado",
            "material": "Aco (blindagem 2RS)",
            "espessura_mm": None,
            "processo": "Montado sob pressao no berco",
            "quantidade": 2 * n_bracos,
            "nota": "Vedado contra poeira de academia",
        },
        {
            "item": "Base do encosto toracico",
            "material": "Chapa aco SAE 1020",
            "espessura_mm": 4.0,
            "processo": "Corte + dobra; parafusada ao estofado",
            "quantidade": 1,
            "nota": "Estofado em couro (marrom/preto) parafusado sobre a base",
        },
        {
            "item": "Base do assento",
            "material": "Chapa aco SAE 1020",
            "espessura_mm": 4.0,
            "processo": "Corte + dobra; parafusada ao estofado",
            "quantidade": 1,
            "nota": "Estofado parafusado sobre a base rigida",
        },
        {
            "item": "Reforco da coluna principal",
            "material": "Chapa aco SAE 1020",
            "espessura_mm": 10.0,
            "processo": "Soldado (MIG) na coluna do encosto",
            "quantidade": 1,
            "nota": "Reforco estrutural de ate 10 mm na regiao de maior momento",
        },
        {
            "item": "Cremalheira de regulagem do assento",
            "material": "Aco inox",
            "espessura_mm": 3.0,
            "processo": "Soldada na coluna do assento",
            "quantidade": 1,
            "nota": "Dentada; evita descascar a pintura no uso do pino de regulagem",
        },
        {
            "item": "Chifre de anilhas",
            "material": "Tubo de aco + batente soldado",
            "espessura_mm": None,
            "processo": "Soldado (MIG) ao braco articulado",
            "quantidade": n_bracos,
            "nota": "Inclinado ~45 graus para reter as anilhas",
        },
        # ---- Pacote de articulação usinada (ref. projeto 201-ABDUTOR) ----
        {
            "item": "Flange mancal usinada",
            "material": "Aco SAE 1020 torneado",
            "espessura_mm": None,
            "processo": "Torneada; furo escalonado Ø42 +0,05/-0,02; "
                        "aparafusada com 4x Ø8,5 em CDF Ø80",
            "quantidade": n_bracos,
            "nota": "Ref. 201-07: centraliza eixo e buchas na estrutura "
                    "(Ø100 -0,2, base 8 mm)",
        },
        {
            "item": "Disco de regulagem da posicao inicial",
            "material": 'Chapa aco SAE 1020 de 1/2"',
            "espessura_mm": 12.7,
            "processo": "Corte a laser + furos de regulagem a cada 15 graus em R114",
            "quantidade": n_bracos,
            "nota": "Ref. 201-06: Ø300, ajusta a abertura inicial do braco ao usuario",
        },
        {
            "item": "Pino trava torneado",
            "material": "Aco SAE 1045",
            "espessura_mm": None,
            "processo": "Torneado Ø15x320, ponta conica 15 graus, rosca 3/8\" "
                        "p/ manipulo; corre em bucha-guia usinada (PDR020)",
            "quantidade": n_bracos,
            "nota": "Ref. 201-08: trava o disco de regulagem sem folga",
        },
        {
            "item": "Anel elastico + canal no eixo",
            "material": "Item comercial (anel) + canal 1,6x1 usinado",
            "espessura_mm": None,
            "processo": "Canal usinado no eixo; montagem com anel elastico",
            "quantidade": 2 * n_bracos,
            "nota": "Ref. 201-04: retencao axial do eixo sem solda",
        },
        {
            "item": "Gusset (chapa-reforco trapezoidal)",
            "material": "Chapa aco SAE 1020",
            "espessura_mm": 3.18,
            "processo": "Corte a laser (140x140 a 18 graus) + solda MIG nos "
                        "nos de carga",
            "quantidade": 4,
            "nota": "Ref. 204-03 item 19: triangula pivo-coluna e coluna-base",
        },
        {
            "item": "Calco de borracha nervurado (pe)",
            "material": "Borracha injetada",
            "espessura_mm": None,
            "processo": "Encaixe sob pressao na ponta do tubo (nervuras R2,5)",
            "quantidade": 4,
            "nota": "Ref. PDR014: fecha o tubo, nao risca piso, nao desliza",
        },
        {
            "item": "Manipulo roscado 3/8\"",
            "material": "Item comercial (baquelite/aluminio)",
            "espessura_mm": None,
            "processo": "Roscado no pino trava",
            "quantidade": n_bracos,
            "nota": "Pega ergonomica da regulagem",
        },
    ]

    acabamento = {
        "preparacao": "Banho antioxidante (fosfatizacao) em todos os componentes",
        "pintura": "Eletrostatica a po — estrutura preto fosco, bracos vermelho vibrante",
        "estofados": "Couro sintetico marrom/preto sobre bases de chapa 4 mm",
    }

    padroes_aplicados = [
        {"padrao": k, **{c: v[c] for c in ("descricao", "origem")}}
        for k, v in PADROES_CONSTRUTIVOS.items()
    ]

    return {
        "estrutura": estrutura,
        "componentes": componentes,
        "processos": PROCESSOS_FABRICACAO,
        "acabamento": acabamento,
        "padroes_aplicados": padroes_aplicados,
        "biblioteca_padroes": sorted(BIBLIOTECA_PADROES),
        "observacao_lista_corte": (
            "Lista de corte deve indicar os angulos por item (ex.: 8/8, "
            "45/53, 2 30', 20/20 graus) como nas BOMs de referencia 204-03 "
            "e 201-11 — encaixe sem fresta para a solda MIG."
        ),
    }
