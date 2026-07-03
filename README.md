# DechenGym

IA para **projeto de equipamentos de musculação** (máquinas articuladas) com
foco em **ergonomia**, **cálculo estrutural** e **geração de código
paramétrico** (OpenSCAD) + memorial descritivo.

A arquitetura é orientada a **orquestração de agentes** e **Tool Calling**:
cada capacidade de engenharia é uma função Python pura e determinística que
um LLM orquestrador (Langflow, SDK, etc.) invoca como *tool*.

## Visão da arquitetura

```
                 ┌────────────────────────┐
                 │   LLM Orquestrador      │
                 │  (Langflow / SDK)       │
                 └───────────┬────────────┘
                             │ Tool Calling (TOOL_SCHEMAS)
             ┌───────────────┼────────────────────┐
             ▼               ▼                     ▼
   Cálculo Estrutural   Especificação        Geração de saída
   (momento fletor,     de Metalon           (OpenSCAD + JSON
    validação)          (catálogo mock)        memorial descritivo)
```

## Estrutura do projeto

```
DechenGym/
├── requirements.txt
├── pyproject.toml
├── README.md
├── src/dechengym/
│   ├── config.py                 # constantes físicas e critérios de projeto
│   ├── calculo_estrutural.py     # Tools de cálculo e validação estrutural
│   ├── geracao_openscad.py       # Tools de geração OpenSCAD + memorial
│   ├── data/metalon_db.py        # catálogo mockado de perfis de aço
│   ├── tools/registry.py         # schemas + dispatcher das Tools (Tool Calling)
│   └── langflow/components.py    # esqueleto de custom components Langflow
├── tests/                        # testes BDD (Given/When/Then)
│   ├── test_calculo_estrutural.py
│   └── test_geracao_openscad.py
├── examples/exemplo_braco_articulado.py
└── output/                       # artefatos gerados (.scad / .json)
```

## Instalação

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Uso rápido

```python
from dechengym import (
    calc_momento_fletor,
    validar_resistencia_estrutural,
    gerar_script_openscad,
    gerar_memorial_descritivo,
)

# Torque de uma alavanca de 800 mm com 100 kg na ponta
calc_momento_fletor(100, 800)            # -> 784.532 N.m

# Valida perfil 50x50 parede 1.5 mm (reprova e recomenda 3 mm)
validar_resistencia_estrutural(100, 800, "50x50", 1.5)

# Gera geometria e memorial
scad = gerar_script_openscad({"comprimento_alavanca_mm": 800})
memorial = gerar_memorial_descritivo({"comprimento_alavanca_mm": 800})
```

Exemplo completo (grava artefatos em `output/`):

```bash
python examples/exemplo_braco_articulado.py
```

## Ferramentas (Tools)

| Tool                              | Descrição                                              |
|-----------------------------------|--------------------------------------------------------|
| `calc_momento_fletor`             | Momento fletor / torque (N·m) de uma alavanca.         |
| `get_especificacao_metalon`       | Propriedades físicas de um perfil de metalon.          |
| `validar_resistencia_estrutural`  | Verifica se o perfil suporta a carga; recomenda parede.|
| `recomendar_espessura_minima`     | Menor espessura comercial que aprova o perfil.         |
| `gerar_script_openscad`           | Código OpenSCAD paramétrico da máquina.                |
| `gerar_memorial_descritivo`       | Lista de cortes e especificações (JSON).               |

Os schemas prontos para tool-calling estão em
`dechengym.tools.TOOL_SCHEMAS`; a execução por nome em
`dechengym.tools.executar_tool`.

## Modelo de cálculo estrutural

- **Momento fletor:** `M = m · g · d` (kg → N via g = 9,80665 m/s²).
- **Tensão de flexão:** `σ = M / W`, sendo `W` o módulo de seção do tubo.
- **Critério de aprovação:** `σ ≤ σ_adm`, com
  `σ_adm = limite_escoamento / fator_segurança` (padrão 2,0).

## Testes (BDD)

Os testes seguem o contrato **Given / When / Then**:

```bash
pytest
```

Contrato de aceite de referência já coberto:

> **Given** alavanca de 800 mm • **When** carga de 100 kg • **Then** torque
> exato em N·m • **And** rejeitar Metalon de 1,5 mm e sugerir ≥ 3 mm.

## Roadmap

- [ ] Geração da **imagem do produto** (render do `.scad` → PNG).
- [ ] Módulo de **ergonomia** (ADM articular, curvas de resistência).
- [ ] Custom components completos para **Langflow**.
- [ ] Catálogo de metalon a partir de fonte real (substituir o mock).
