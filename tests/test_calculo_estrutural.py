"""
Testes do módulo de Cálculo Estrutural — estrutura BDD (Given/When/Then).
========================================================================

Cada teste segue estritamente o padrão:

    # Given  -> contexto / entradas
    # When   -> ação (chamada da tool)
    # Then   -> asserção sobre o resultado
    # And    -> asserção adicional

Contrato de aceite de referência (do briefing):

    Given  um braço articulado com alavanca de 800 mm
    When   a carga aplicada for de 100 kg em uma das extremidades
    Then   a ferramenta de cálculo deve retornar o torque exato em N.m
    And    a ferramenta de especificação deve rejeitar um Metalon de 1.5 mm
           e sugerir no mínimo 3 mm de espessura.
"""

import math

import pytest

from dechengym.calculo_estrutural import (
    calc_momento_fletor,
    get_especificacao_metalon,
    recomendar_espessura_minima,
    validar_resistencia_estrutural,
)
from dechengym.config import GRAVIDADE_MS2


# ==========================================================================
# calc_momento_fletor
# ==========================================================================
class TestCalcMomentoFletor:
    """Contrato da ferramenta de cálculo de torque/momento fletor."""

    def test_torque_exato_para_alavanca_800mm_carga_100kg(self):
        # Given que o usuário solicita um braço articulado com alavanca de 800 mm
        distancia_alavanca_mm = 800
        # And uma carga de 100 kg aplicada em uma das extremidades
        forca_kg = 100

        # When a ferramenta de cálculo é invocada
        torque_nm = calc_momento_fletor(forca_kg, distancia_alavanca_mm)

        # Then deve retornar o torque exato em N.m (M = m * g * d)
        torque_esperado = 100 * GRAVIDADE_MS2 * 0.8  # 784.532 N.m
        assert torque_nm == pytest.approx(torque_esperado)
        assert torque_nm == pytest.approx(784.532, abs=1e-3)

    def test_momento_e_proporcional_a_distancia(self):
        # Given uma mesma carga
        forca_kg = 50
        # When aplicada a duas distâncias, sendo a segunda o dobro da primeira
        m1 = calc_momento_fletor(forca_kg, 400)
        m2 = calc_momento_fletor(forca_kg, 800)

        # Then o momento deve dobrar
        assert m2 == pytest.approx(2 * m1)

    def test_momento_nulo_quando_carga_zero(self):
        # Given carga nula
        # When calculado o momento
        # Then o resultado deve ser zero
        assert calc_momento_fletor(0, 800) == 0.0

    def test_rejeita_entradas_negativas(self):
        # Given entradas negativas
        # When a ferramenta é chamada
        # Then deve levantar ValueError
        with pytest.raises(ValueError):
            calc_momento_fletor(-1, 800)
        with pytest.raises(ValueError):
            calc_momento_fletor(100, -800)


# ==========================================================================
# get_especificacao_metalon
# ==========================================================================
class TestGetEspecificacaoMetalon:
    """Contrato da ferramenta de especificação de metalon."""

    def test_retorna_propriedades_fisicas_do_perfil(self):
        # Given um perfil 50x50 com parede de 3 mm
        # When consultamos a especificação
        spec = get_especificacao_metalon("50x50", 3.0)

        # Then deve conter as propriedades físicas essenciais
        assert spec["perfil"] == "50x50"
        assert spec["limite_escoamento_mpa"] == 250.0
        # And o módulo de seção e o peso por metro devem ser positivos
        assert spec["modulo_secao_mm3"] > 0
        assert spec["peso_por_metro_kg"] > 0
        # And o módulo de seção calculado deve bater com o esperado (mm³)
        assert spec["modulo_secao_mm3"] == pytest.approx(8339.7, abs=0.5)

    def test_perfil_inexistente_levanta_keyerror(self):
        # Given um perfil fora do catálogo
        # When consultado
        # Then deve levantar KeyError
        with pytest.raises(KeyError):
            get_especificacao_metalon("999x999", 3.0)

    def test_espessura_indisponivel_levanta_valueerror(self):
        # Given uma espessura inexistente para o perfil
        # When consultada
        # Then deve levantar ValueError
        with pytest.raises(ValueError):
            get_especificacao_metalon("50x50", 12.7)


# ==========================================================================
# Contrato de aceite completo (integração das ferramentas)
# ==========================================================================
class TestContratoAceiteBracoArticulado:
    """Cenário BDD completo descrito no briefing."""

    def test_rejeita_1_5mm_e_sugere_no_minimo_3mm(self):
        # Given um braço articulado com alavanca de 800 mm, perfil 50x50
        distancia_alavanca_mm = 800
        perfil = "50x50"
        # When a carga aplicada for de 100 kg em uma das extremidades
        forca_kg = 100

        # And validamos a estrutura com um Metalon de parede 1.5 mm
        relatorio = validar_resistencia_estrutural(
            forca_kg, distancia_alavanca_mm, perfil, espessura_parede_mm=1.5
        )

        # Then a ferramenta de especificação deve REJEITAR o Metalon de 1.5 mm
        assert relatorio["aprovado"] is False

        # And deve sugerir no mínimo 3 mm de espessura
        assert relatorio["espessura_recomendada_mm"] == 3.0

    def test_recomendacao_direta_de_espessura_minima(self):
        # Given a mesma carga/alavanca
        # When pedimos diretamente a espessura mínima recomendada
        espessura = recomendar_espessura_minima(100, 800, "50x50")

        # Then deve ser exatamente 3.0 mm (menor comercial que aprova)
        assert espessura == 3.0

    def test_3mm_e_aprovado_para_a_carga(self):
        # Given o perfil 50x50 com parede de 3 mm
        # When validamos a estrutura para 100 kg a 800 mm
        relatorio = validar_resistencia_estrutural(100, 800, "50x50", 3.0)

        # Then deve ser aprovado
        assert relatorio["aprovado"] is True
        # And o coeficiente de utilização deve ser <= 1
        assert relatorio["coef_utilizacao"] <= 1.0

    def test_torque_reportado_no_relatorio_confere(self):
        # Given a validação estrutural
        relatorio = validar_resistencia_estrutural(100, 800, "50x50", 3.0)
        # When comparamos o momento reportado
        # Then deve ser o torque exato
        assert relatorio["momento_fletor_nm"] == pytest.approx(784.532, abs=1e-3)

    def test_perfil_pequeno_reprovado_em_todas_espessuras(self):
        # Given um perfil subdimensionado (20x20) para carga pesada
        # When validamos com carga elevada
        relatorio = validar_resistencia_estrutural(100, 800, "20x20", 1.5)
        # Then deve reprovar
        assert relatorio["aprovado"] is False
        # And pode não haver espessura comercial suficiente (recomenda None)
        assert relatorio["espessura_recomendada_mm"] is None
