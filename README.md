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
│   ├── ergonomia/                # Tools de ergonomia e biomecânica
│   │   ├── antropometria.py      #   dimensões corporais + faixas de ajuste
│   │   ├── amplitude.py          #   ADM articular + validação do curso
│   │   ├── pegada.py             #   padrão de pegada (orientação/largura/diâmetro)
│   │   ├── curva_resistencia.py  #   curva de força x resistência da máquina
│   │   └── projeto.py            #   integrador do envelope ergonômico
│   ├── data/                     # bancos mockados (metalon, antropometria,
│   │   │                         #   ADM, pegada, curvas de força, exercícios)
│   │   └── ...
│   ├── tools/registry.py         # schemas + dispatcher das Tools (Tool Calling)
│   └── langflow/components.py    # esqueleto de custom components Langflow
├── tests/                        # testes BDD (Given/When/Then)
│   ├── test_calculo_estrutural.py
│   ├── test_geracao_openscad.py
│   └── test_ergonomia.py
│   ├── geracao_imagem.py         # Tools de imagem (SVG / PNG / prompt IA)
│   ├── sintese_came.py           # Tools de came de resistência variável
├── examples/
│   ├── exemplo_braco_articulado.py
│   ├── exemplo_ergonomia.py
│   ├── exemplo_imagem.py
│   └── exemplo_came.py
└── output/                       # artefatos gerados (.scad / .svg / .json)
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

### Geração de imagem

| Tool                              | Descrição                                              |
|-----------------------------------|--------------------------------------------------------|
| `gerar_preview_svg`               | Desenho técnico 2D (blueprint) em SVG — sem dependências. |
| `renderizar_openscad_png`         | Render 3D em PNG via OpenSCAD CLI (se instalado).       |
| `montar_prompt_imagem_produto`    | Prompt para modelo texto→imagem (render de produto).   |

### Síntese de came (resistência variável)

| Tool                              | Descrição                                              |
|-----------------------------------|--------------------------------------------------------|
| `sintetizar_perfil_came`          | Gera o perfil da came a partir da curva de força.      |
| `calcular_resistencia_came`       | Torque resultante τ(θ) = W·r(θ) da came.               |
| `gerar_came_openscad`             | Código OpenSCAD da came (chapa extrudada + furos).     |
| `gerar_came_svg`                  | Preview 2D do perfil da came (SVG).                    |
| `sintetizar_came_de_ergonomia`    | Atalho: came a partir do envelope ergonômico.          |

### Ergonomia

| Tool                              | Descrição                                              |
|-----------------------------------|--------------------------------------------------------|
| `get_antropometria`               | Dimensão corporal por medida, percentil e sexo.        |
| `calcular_faixa_ajuste`           | Curso de regulagem para o envelope P5–P95.             |
| `get_amplitude_movimento`         | ADM anatômica e recomendada para treino (graus).       |
| `validar_amplitude_projetada`     | Verifica se o curso do braço respeita a ADM segura.    |
| `get_padrao_pegada`               | Orientação do punho (pronada/supinada/neutra/mista).   |
| `dimensionar_pega`                | Diâmetro da pega a partir do comprimento da mão.       |
| `calcular_largura_pegada`         | Distância entre pegas a partir da largura biacromial.  |
| `get_curva_forca`                 | Curva de força humana do grupo muscular.               |
| `gerar_perfil_resistencia_alvo`   | Perfil de resistência que acompanha a curva de força.  |
| `avaliar_curva_resistencia`       | Pontua o casamento resistência × curva de força.       |
| `calcular_alinhamento_pivo`       | Altura do eixo de pivô alinhada ao eixo articular.     |
| `projetar_ergonomia`              | Integrador: envelope ergonômico completo do exercício. |

Os schemas prontos para tool-calling estão em
`dechengym.tools.TOOL_SCHEMAS`; a execução por nome em
`dechengym.tools.executar_tool`.

## Modelo de ergonomia

O módulo de ergonomia trata uma máquina articulada como a interface entre a
**anatomia do usuário** e a **mecânica do equipamento**, cobrindo:

- **Antropometria (envelope P5–P95):** tabelas por sexo/percentil (mm) que
  dimensionam os **cursos de regulagem** (assento, encosto) para acomodar da
  mulher P5 ao homem P95.
- **Alinhamento articular:** o eixo de pivô da máquina deve coincidir com o
  eixo anatômico de rotação da articulação (ex.: cotovelo na rosca) — o erro
  de alinhamento é a principal fonte de desconforto/lesão em máquinas.
- **Amplitude de movimento (ADM):** cada movimento tem faixa anatômica e
  faixa **recomendada de treino** (mais conservadora); o curso do braço é
  validado para não exceder o seguro.
- **Padrão de pegada** (interface mão–máquina), em três eixos:
  - *orientação do punho:* pronada, supinada, neutra ou mista;
  - *largura:* fechada / média / aberta (múltiplo da largura biacromial);
  - *diâmetro da pega:* ≈ 20% do comprimento da mão para conforto/força de
    trabalho (~30–45 mm); mais grossa (~50–60 mm) para força de preensão.
- **Curva de resistência × curva de força:** a resistência da máquina
  (definida pela geometria do braço/came) deve acompanhar a curva de força
  do músculo (ascendente, descendente ou em sino) para manter a solicitação
  adequada em toda a amplitude. `avaliar_curva_resistencia` pontua esse
  casamento de 0 a 100 e indica onde ajustar a geometria.

O integrador `projetar_ergonomia("rosca_biceps", ...)` consolida tudo isso
em um "envelope ergonômico", e `parametros_geometria_de_ergonomia(...)`
converte esse envelope em parâmetros para a geração OpenSCAD — de modo que a
geometria **nasce alinhada** às recomendações ergonômicas.

```bash
python examples/exemplo_ergonomia.py
```

## Geração de imagem

A imagem do produto é atacada em três trilhas complementares, para funcionar
em qualquer ambiente e degradar graciosamente:

1. **Preview técnico SVG** (`gerar_preview_svg`): vista lateral / blueprint
   em **Python puro, sem dependências** — sempre disponível e determinístico.
   Ilustra base, coluna, eixo de pivô, braço nas posições inicial/final e o
   **arco de movimento (ADM)**, ligando a ergonomia à representação visual.
2. **Render 3D PNG** (`renderizar_openscad_png`): chama o executável do
   OpenSCAD para renderizar o `.scad`. Requer o OpenSCAD instalado; caso
   contrário, levanta um erro com orientação (o SVG segue disponível).
3. **Render de produto por IA** (`montar_prompt_imagem_produto`): monta o
   *prompt* (positivo e negativo) descrevendo a máquina, para o agente
   orquestrador repassar à sua Tool de texto→imagem — **provedor-agnóstico**.

```bash
python examples/exemplo_imagem.py
```

O pipeline completo é: `projetar_ergonomia` →
`parametros_geometria_de_ergonomia` → `gerar_script_openscad` +
`gerar_memorial_descritivo` + `gerar_preview_svg` /
`montar_prompt_imagem_produto`.

## Síntese de came (o diferencial ergonômico)

O que separa uma máquina genérica de uma com biomecânica projetada é a
**came de resistência variável**: a resistência sentida deve acompanhar a
força do músculo em cada ponto do movimento. O módulo `sintese_came`
converte a curva de força em geometria fabricável.

Fundamento: com tração de cabo aproximadamente constante `W = m·g`, o torque
resistente é `τ(θ) = W · r(θ)`, onde `r(θ)` é o raio efetivo da came. Para
manter a intensidade relativa constante, queremos `τ(θ) ∝ S(θ)` (curva de
força), logo:

```
r(θ) = r_max · S_norm(θ)
```

ou seja, **o raio da came é proporcional à curva de força normalizada** — o
pico de resistência coincide com o ponto de maior força. Para o bíceps
(curva em sino), isso produz a came em formato de lágrima, com raio máximo
no meio da amplitude.

O casamento é **provado por round-trip**: a resistência recalculada da came
sintetizada, reavaliada por `avaliar_curva_resistencia`, pontua **100/100**.

```bash
python examples/exemplo_came.py
```

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

- [x] Módulo de **ergonomia** (antropometria, ADM, pegada, curva de força).
- [x] Geração da **imagem do produto** (SVG técnico / PNG OpenSCAD / prompt IA).
- [x] **Síntese de came** de resistência variável (curva de força → geometria).
- [ ] **Agente orquestrador** (briefing em linguagem natural → design validado).
- [ ] Fechar loop estrutura↔geometria (validação realimenta o `.scad`).
- [ ] Custom components completos para **Langflow**.
- [ ] Bancos de dados a partir de fontes reais (metalon e antropometria).
