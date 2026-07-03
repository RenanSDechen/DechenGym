"""
Constantes físicas e parâmetros de engenharia usados por todo o projeto.

Centralizar aqui evita "números mágicos" espalhados pelo código e facilita
a auditoria dos critérios de projeto pelo engenheiro responsável.
"""

# --------------------------------------------------------------------------
# Constantes físicas
# --------------------------------------------------------------------------

#: Aceleração da gravidade padrão (m/s²) — ISO 80000-3.
GRAVIDADE_MS2: float = 9.80665

#: Densidade do aço carbono (kg/m³) — usada no cálculo de peso por metro.
DENSIDADE_ACO_KG_M3: float = 7850.0


# --------------------------------------------------------------------------
# Critérios de projeto (dimensionamento estrutural)
# --------------------------------------------------------------------------

#: Fator de segurança padrão aplicado sobre o limite de escoamento.
#:
#: Equipamentos de musculação recebem cargas dinâmicas e uso intenso; um
#: fator de 2.0 sobre o escoamento é um ponto de partida conservador e
#: comum para estruturas soldadas sujeitas a fadiga moderada.
FATOR_SEGURANCA_PADRAO: float = 2.0

#: Espessuras de parede comerciais de metalon (mm), em ordem crescente.
#: Usadas pela rotina de recomendação de espessura mínima.
ESPESSURAS_COMERCIAIS_MM: tuple[float, ...] = (0.9, 1.2, 1.5, 2.0, 3.0, 4.75)
