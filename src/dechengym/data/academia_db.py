"""
Base da Academia Virtual — os equipamentos mais usados do mercado.
=================================================================

Catálogo dos equipamentos presentes em praticamente toda academia comercial,
compilado de rankings do setor (Skelcore "20 most-used gym machines",
WodGuru "gym equipment list", Fitness Expo, Training Station) e fichas
técnicas de fabricantes topo de linha (Life Fitness / Hammer Strength,
Technogym, Matrix).

Cada equipamento traz: categoria e zona da academia, tipo construtivo,
músculos-alvo, **footprint real de mercado** (largura × profundidade, mm),
altura, carga de trabalho e — quando o movimento é coberto pelo pipeline
DechenGym — o ``exercicio_pipeline`` que gera o projeto completo (ergonomia
→ came → estrutura → 3D → dossiê).

.. note::
   Dimensões são valores de referência de catálogos comerciais
   (arredondados); confirme na ficha do fabricante escolhido antes do
   layout final.
"""

from __future__ import annotations

from typing import Any, TypedDict


class Equipamento(TypedDict):
    nome: str
    categoria: str          # zona da academia
    tipo: str               # construtivo
    musculos: list[str]
    footprint_mm: list[int]  # [largura, profundidade]
    altura_mm: int
    carga_max_kg: int
    referencia: str          # linha topo de mercado equivalente
    rank: int                # popularidade (1 = mais usado)
    exercicio_pipeline: str | None  # projeto completo DechenGym


CAT_ARTICULADA = "Musculacao articulada (plate-loaded)"
CAT_SELETORIZADA = "Musculacao seletorizada (polia/placas)"
CAT_PERNAS = "Pernas (guiadas e prensas)"
CAT_LIVRE = "Peso livre e bancos"
CAT_CARDIO = "Cardio"

ACADEMIA_VIRTUAL: dict[str, Equipamento] = {
    # ------------------- Articuladas (plate-loaded) ----------------------
    "remada_iso_lateral": {
        "nome": "Remada Iso-Lateral (plate-loaded)",
        "categoria": CAT_ARTICULADA,
        "tipo": "Articulada, bracos independentes",
        "musculos": ["dorsal", "romboides", "biceps", "deltoide posterior"],
        "footprint_mm": [1200, 1500], "altura_mm": 1800, "carga_max_kg": 200,
        "referencia": "Hammer Strength IL-ROW",
        "rank": 8, "exercicio_pipeline": "remada_maquina",
    },
    "supino_articulado": {
        "nome": "Supino Articulado (chest press plate-loaded)",
        "categoria": CAT_ARTICULADA,
        "tipo": "Articulada, bracos independentes",
        "musculos": ["peitoral", "triceps", "deltoide anterior"],
        "footprint_mm": [1530, 1350], "altura_mm": 1500, "carga_max_kg": 200,
        "referencia": "Hammer Strength Iso-Lateral Bench Press",
        "rank": 6, "exercicio_pipeline": "supino_maquina",
    },
    "desenvolvimento_articulado": {
        "nome": "Desenvolvimento Articulado (shoulder press)",
        "categoria": CAT_ARTICULADA,
        "tipo": "Articulada, bracos independentes",
        "musculos": ["deltoide", "trapezio", "triceps"],
        "footprint_mm": [1370, 1180], "altura_mm": 1520, "carga_max_kg": 160,
        "referencia": "Hammer Strength Iso-Lateral Shoulder Press",
        "rank": 12, "exercicio_pipeline": "desenvolvimento_maquina",
    },
    "rosca_scott_maquina": {
        "nome": "Rosca Scott Articulada (biceps)",
        "categoria": CAT_ARTICULADA,
        "tipo": "Articulada, alavanca unica",
        "musculos": ["biceps", "braquial"],
        "footprint_mm": [900, 1000], "altura_mm": 1100, "carga_max_kg": 80,
        "referencia": "Hammer Strength Preacher Curl",
        "rank": 18, "exercicio_pipeline": "rosca_biceps",
    },
    "triceps_maquina": {
        "nome": "Triceps Articulado (dip/extensao)",
        "categoria": CAT_ARTICULADA,
        "tipo": "Articulada, alavanca unica",
        "musculos": ["triceps", "peitoral inferior"],
        "footprint_mm": [1000, 1200], "altura_mm": 1250, "carga_max_kg": 120,
        "referencia": "Hammer Strength Seated Dip",
        "rank": 19, "exercicio_pipeline": "triceps_maquina",
    },
    # ------------------- Seletorizadas (polia) ---------------------------
    "puxada_alta": {
        "nome": "Puxada Alta (lat pulldown)",
        "categoria": CAT_SELETORIZADA,
        "tipo": "Polia com placas seletorizadas",
        "musculos": ["dorsal", "biceps", "romboides"],
        "footprint_mm": [1220, 1220], "altura_mm": 2380, "carga_max_kg": 120,
        "referencia": "Life Fitness Signature Lat Pulldown",
        "rank": 3, "exercicio_pipeline": None,
    },
    "remada_baixa": {
        "nome": "Remada Baixa Sentada (seated cable row)",
        "categoria": CAT_SELETORIZADA,
        "tipo": "Polia baixa com placas",
        "musculos": ["dorsal", "romboides", "biceps"],
        "footprint_mm": [1080, 1650], "altura_mm": 1500, "carga_max_kg": 120,
        "referencia": "Life Fitness Signature Row",
        "rank": 7, "exercicio_pipeline": None,
    },
    "crucifixo_peck_deck": {
        "nome": "Crucifixo / Peck Deck (voador)",
        "categoria": CAT_SELETORIZADA,
        "tipo": "Seletorizada, bracos convergentes",
        "musculos": ["peitoral", "deltoide anterior"],
        "footprint_mm": [960, 950], "altura_mm": 1980, "carga_max_kg": 110,
        "referencia": "Technogym Selection Pectoral",
        "rank": 9, "exercicio_pipeline": None,
    },
    "crossover_polia": {
        "nome": "Crossover / Estacao de Polias Duplas",
        "categoria": CAT_SELETORIZADA,
        "tipo": "Torre dupla com cabos ajustaveis",
        "musculos": ["peitoral", "dorsal", "deltoide", "core"],
        "footprint_mm": [3600, 700], "altura_mm": 2320, "carga_max_kg": 2 * 95,
        "referencia": "Life Fitness Cable Motion Crossover",
        "rank": 4, "exercicio_pipeline": None,
    },
    "graviton": {
        "nome": "Graviton (barra fixa/paralela assistida)",
        "categoria": CAT_SELETORIZADA,
        "tipo": "Assistencia por contrapeso",
        "musculos": ["dorsal", "biceps", "triceps", "peitoral"],
        "footprint_mm": [1420, 1200], "altura_mm": 2340, "carga_max_kg": 100,
        "referencia": "Technogym Selection Chin/Dip Assist",
        "rank": 15, "exercicio_pipeline": None,
    },
    "abdominal_maquina": {
        "nome": "Abdominal Maquina (crunch)",
        "categoria": CAT_SELETORIZADA,
        "tipo": "Seletorizada com apoio toracico",
        "musculos": ["reto abdominal", "obliquos"],
        "footprint_mm": [1070, 1220], "altura_mm": 1500, "carga_max_kg": 90,
        "referencia": "Technogym Selection Abdominal Crunch",
        "rank": 16, "exercicio_pipeline": None,
    },
    # ------------------- Pernas ------------------------------------------
    "leg_press_45": {
        "nome": "Leg Press 45 graus",
        "categoria": CAT_PERNAS,
        "tipo": "Carro guiado em trilhos, plate-loaded",
        "musculos": ["quadriceps", "gluteo", "isquiotibiais"],
        "footprint_mm": [1600, 2180], "altura_mm": 1450, "carga_max_kg": 400,
        "referencia": "Hammer Strength Linear Leg Press",
        "rank": 2, "exercicio_pipeline": None,
    },
    "cadeira_extensora": {
        "nome": "Cadeira Extensora (leg extension)",
        "categoria": CAT_PERNAS,
        "tipo": "Articulada com came, seletorizada",
        "musculos": ["quadriceps"],
        "footprint_mm": [1080, 1140], "altura_mm": 1520, "carga_max_kg": 110,
        "referencia": "Life Fitness Signature Leg Extension",
        "rank": 5, "exercicio_pipeline": "cadeira_extensora",
    },
    "mesa_flexora": {
        "nome": "Cadeira/Mesa Flexora (leg curl)",
        "categoria": CAT_PERNAS,
        "tipo": "Articulada com came, seletorizada",
        "musculos": ["isquiotibiais"],
        "footprint_mm": [1170, 1220], "altura_mm": 1520, "carga_max_kg": 110,
        "referencia": "Life Fitness Signature Seated Leg Curl",
        "rank": 10, "exercicio_pipeline": "mesa_flexora",
    },
    "hack_squat": {
        "nome": "Hack Squat / Agachamento Guiado",
        "categoria": CAT_PERNAS,
        "tipo": "Carro guiado 45 graus, plate-loaded",
        "musculos": ["quadriceps", "gluteo"],
        "footprint_mm": [1480, 2230], "altura_mm": 1520, "carga_max_kg": 350,
        "referencia": "Hammer Strength V-Squat",
        "rank": 13, "exercicio_pipeline": None,
    },
    "cadeira_abdutora": {
        "nome": "Cadeira Abdutora",
        "categoria": CAT_PERNAS,
        "tipo": "Articulada seletorizada",
        "musculos": ["gluteo medio", "abdutores"],
        "footprint_mm": [900, 1500], "altura_mm": 1520, "carga_max_kg": 100,
        "referencia": "Technogym Selection Abductor",
        "rank": 11, "exercicio_pipeline": "cadeira_abdutora",
    },
    "cadeira_adutora": {
        "nome": "Cadeira Adutora",
        "categoria": CAT_PERNAS,
        "tipo": "Articulada seletorizada",
        "musculos": ["adutores"],
        "footprint_mm": [900, 1500], "altura_mm": 1520, "carga_max_kg": 100,
        "referencia": "Technogym Selection Adductor",
        "rank": 14, "exercicio_pipeline": None,
    },
    "panturrilha_em_pe": {
        "nome": "Panturrilha em Pe (standing calf)",
        "categoria": CAT_PERNAS,
        "tipo": "Guiada com ombreiras, plate-loaded",
        "musculos": ["panturrilha"],
        "footprint_mm": [960, 880], "altura_mm": 1900, "carga_max_kg": 250,
        "referencia": "Hammer Strength Standing Calf",
        "rank": 17, "exercicio_pipeline": None,
    },
    "elevacao_pelvica": {
        "nome": "Elevacao Pelvica (hip thrust)",
        "categoria": CAT_PERNAS,
        "tipo": "Articulada plate-loaded com cinto",
        "musculos": ["gluteo", "isquiotibiais"],
        "footprint_mm": [1500, 1100], "altura_mm": 900, "carga_max_kg": 250,
        "referencia": "Panatta Hip Thrust",
        "rank": 20, "exercicio_pipeline": None,
    },
    # ------------------- Peso livre / bancos -----------------------------
    "smith": {
        "nome": "Maquina Smith (barra guiada)",
        "categoria": CAT_LIVRE,
        "tipo": "Barra guiada em trilhos com travas",
        "musculos": ["corpo inteiro (agachamento, supino, remada)"],
        "footprint_mm": [2220, 1650], "altura_mm": 2230, "carga_max_kg": 300,
        "referencia": "Matrix Magnum Smith",
        "rank": 1, "exercicio_pipeline": None,
    },
    "power_rack": {
        "nome": "Power Rack / Gaiola",
        "categoria": CAT_LIVRE,
        "tipo": "Estrutura fixa com seguranca",
        "musculos": ["corpo inteiro (basicos livres)"],
        "footprint_mm": [1400, 1500], "altura_mm": 2320, "carga_max_kg": 450,
        "referencia": "Hammer Strength HD Elite Rack",
        "rank": 21, "exercicio_pipeline": None,
    },
    "banco_regulavel": {
        "nome": "Banco Regulavel + Halteres",
        "categoria": CAT_LIVRE,
        "tipo": "Banco 0-85 graus",
        "musculos": ["corpo inteiro (livres)"],
        "footprint_mm": [640, 1700], "altura_mm": 450, "carga_max_kg": 380,
        "referencia": "Life Fitness Signature Multi-Adjustable Bench",
        "rank": 22, "exercicio_pipeline": None,
    },
    "banco_romano": {
        "nome": "Banco Romano 45 (lombar)",
        "categoria": CAT_LIVRE,
        "tipo": "Banco fixo inclinado",
        "musculos": ["lombar", "gluteo", "isquiotibiais"],
        "footprint_mm": [720, 1130], "altura_mm": 880, "carga_max_kg": 180,
        "referencia": "Hammer Strength Back Extension",
        "rank": 23, "exercicio_pipeline": None,
    },
    # ------------------- Cardio ------------------------------------------
    "esteira": {
        "nome": "Esteira",
        "categoria": CAT_CARDIO,
        "tipo": "Motorizada",
        "musculos": ["cardio / membros inferiores"],
        "footprint_mm": [950, 2110], "altura_mm": 1600, "carga_max_kg": 180,
        "referencia": "Life Fitness Integrity+",
        "rank": 1, "exercicio_pipeline": None,
    },
    "eliptico": {
        "nome": "Eliptico",
        "categoria": CAT_CARDIO,
        "tipo": "Transmissao por inercia",
        "musculos": ["cardio / corpo inteiro"],
        "footprint_mm": [760, 2110], "altura_mm": 1730, "carga_max_kg": 180,
        "referencia": "Technogym Synchro",
        "rank": 2, "exercicio_pipeline": None,
    },
    "bike_vertical": {
        "nome": "Bike Vertical",
        "categoria": CAT_CARDIO,
        "tipo": "Resistencia eletromagnetica",
        "musculos": ["cardio / membros inferiores"],
        "footprint_mm": [630, 1220], "altura_mm": 1500, "carga_max_kg": 160,
        "referencia": "Life Fitness Integrity Bike",
        "rank": 3, "exercicio_pipeline": None,
    },
    "remo_ergometro": {
        "nome": "Remo Ergometro",
        "categoria": CAT_CARDIO,
        "tipo": "Resistencia a ar/magnetica",
        "musculos": ["cardio / corpo inteiro"],
        "footprint_mm": [610, 2440], "altura_mm": 910, "carga_max_kg": 150,
        "referencia": "Concept2 RowErg",
        "rank": 4, "exercicio_pipeline": None,
    },
}


def categorias() -> list[str]:
    """Categorias na ordem de exibição da academia."""
    return [CAT_ARTICULADA, CAT_SELETORIZADA, CAT_PERNAS, CAT_LIVRE, CAT_CARDIO]


def equipamentos_da_categoria(cat: str) -> list[tuple[str, Equipamento]]:
    itens = [(k, v) for k, v in ACADEMIA_VIRTUAL.items() if v["categoria"] == cat]
    return sorted(itens, key=lambda kv: kv[1]["rank"])


def resumo_academia() -> dict[str, Any]:
    """Totais da academia virtual (área, equipamentos por categoria)."""
    area_equip = sum(e["footprint_mm"][0] * e["footprint_mm"][1] for e in ACADEMIA_VIRTUAL.values()) / 1e6
    return {
        "total_equipamentos": len(ACADEMIA_VIRTUAL),
        "com_projeto_completo": sum(1 for e in ACADEMIA_VIRTUAL.values() if e["exercicio_pipeline"]),
        "area_ocupada_m2": round(area_equip, 1),
        "por_categoria": {c: len(equipamentos_da_categoria(c)) for c in categorias()},
    }
