"""
Testes do módulo de Síntese de Came — estrutura BDD (Given/When/Then).
=====================================================================

O contrato central é o **round-trip**: a came sintetizada a partir de uma
curva de força, quando tem sua resistência recalculada e reavaliada, deve
casar quase perfeitamente com a curva de força de origem.
"""

import xml.etree.ElementTree as ET

import pytest

from dechengym.ergonomia import avaliar_curva_resistencia, projetar_ergonomia
from dechengym.sintese_came import (
    calcular_resistencia_came,
    gerar_came_openscad,
    gerar_came_svg,
    sintetizar_came_de_ergonomia,
    sintetizar_perfil_came,
)


class TestSintetizarPerfilCame:
    def test_raio_proporcional_a_curva_de_forca(self):
        # Given o bíceps (pico de força no meio) e raio máximo de 100 mm
        # When sintetizamos o perfil
        perfil = sintetizar_perfil_came("biceps", raio_max_mm=100, amplitude_movimento_graus=120)
        # Then o raio de pico coincide com o raio máximo
        raio_pico = max(a["raio_mm"] for a in perfil["amostras_trabalho"])
        assert raio_pico == pytest.approx(100.0)
        # And o raio mínimo é raio_max × menor fator da curva (bíceps: 0.55)
        assert perfil["raio_min_mm"] == pytest.approx(55.0)

    def test_pico_de_raio_ocorre_no_meio_para_curva_em_sino(self):
        # Given a curva em sino do bíceps (pico a 50%)
        perfil = sintetizar_perfil_came("biceps", 100, 120)
        # When localizamos o ponto de maior raio
        pico = max(perfil["amostras_trabalho"], key=lambda a: a["raio_mm"])
        # Then ele está no centro do movimento (~50%)
        assert pico["movement_pct"] == pytest.approx(50.0, abs=1.0)

    def test_poligono_fechado_cobre_360_graus(self):
        # Given uma ADM de 120 graus
        perfil = sintetizar_perfil_came("biceps", 100, 120)
        # When inspecionamos o polígono
        # Then ele tem pontos suficientes para formar uma chapa fechada
        assert len(perfil["poligono_xy"]) > len(perfil["amostras_trabalho"])

    def test_parametros_invalidos_levantam_erro(self):
        # Given parâmetros inválidos
        # When sintetizamos
        # Then levanta ValueError
        with pytest.raises(ValueError):
            sintetizar_perfil_came("biceps", raio_max_mm=0)
        with pytest.raises(ValueError):
            sintetizar_perfil_came("biceps", amplitude_movimento_graus=0)


class TestRoundTripCasamento:
    """Contrato de aceite: came sintetizada casa com a curva de força."""

    @pytest.mark.parametrize("grupo", ["biceps", "triceps", "dorsal", "quadriceps"])
    def test_came_sintetizada_pontua_100(self, grupo):
        # Given uma came sintetizada da curva de força do grupo
        perfil = sintetizar_perfil_came(grupo, raio_max_mm=100, amplitude_movimento_graus=120)
        # When calculamos a resistência e reavaliamos o casamento
        resistencia = calcular_resistencia_came(perfil, carga_kg=50)
        aval = avaliar_curva_resistencia(resistencia["torque_nm"], grupo)
        # Then o casamento é (praticamente) perfeito
        assert aval["pontuacao"] >= 99.5

    def test_torque_pico_proporcional_a_carga(self):
        # Given a mesma came sob duas cargas
        perfil = sintetizar_perfil_came("biceps", 100, 120)
        r50 = calcular_resistencia_came(perfil, 50)
        r100 = calcular_resistencia_came(perfil, 100)
        # When comparamos o torque de pico
        # Then dobrar a carga dobra o torque (tolerância p/ arredondamento a 4 casas)
        assert r100["torque_pico_nm"] == pytest.approx(2 * r50["torque_pico_nm"], abs=0.01)


class TestSaidasCame:
    def test_openscad_contem_poligono_e_furos(self):
        # Given um perfil de came
        perfil = sintetizar_perfil_came("quadriceps", 90, 120)
        # When geramos o OpenSCAD
        scad = gerar_came_openscad(perfil, espessura_mm=12, diametro_eixo_mm=25)
        # Then contém o polígono extrudado e os furos
        assert "polygon(points" in scad
        assert "linear_extrude" in scad
        assert "diametro_eixo    = 25" in scad
        assert "circle(d = diametro_cabo" in scad

    def test_svg_valido(self):
        # Given um perfil de came
        perfil = sintetizar_perfil_came("dorsal", 100, 120)
        # When geramos o SVG
        svg = gerar_came_svg(perfil)
        # Then é XML bem-formado com o contorno da came
        raiz = ET.fromstring(svg)
        assert raiz.tag.endswith("svg")
        assert "<path" in svg


class TestSinteseDeErgonomia:
    @pytest.mark.parametrize(
        "exercicio",
        [
            "rosca_biceps",
            "triceps_maquina",
            "supino_maquina",
            "remada_maquina",
            "desenvolvimento_maquina",
            "cadeira_extensora",
            "mesa_flexora",
            "cadeira_abdutora",
        ],
    )
    def test_came_de_ergonomia_funciona_para_todo_exercicio(self, exercicio):
        # Regressão: exercícios de extensão (tríceps, cadeira extensora) tinham
        # amplitude zero e quebravam a síntese da came. Todos devem funcionar.
        # Given o envelope ergonômico do exercício
        env = projetar_ergonomia(exercicio, carga_pico_kg=50)
        # When sintetizamos a came e reavaliamos o casamento
        perfil = sintetizar_came_de_ergonomia(env, raio_max_mm=100)
        resistencia = calcular_resistencia_came(perfil, carga_kg=50)
        aval = avaliar_curva_resistencia(resistencia["torque_nm"], env["grupo_muscular"])
        # Then a amplitude é positiva e o casamento é (praticamente) perfeito
        assert perfil["amplitude_graus"] > 0
        assert aval["pontuacao"] >= 99.5

    def test_usa_grupo_e_adm_do_envelope(self):
        # Given o envelope ergonômico da rosca de bíceps
        env = projetar_ergonomia("rosca_biceps")
        # When sintetizamos a came a partir do envelope
        perfil = sintetizar_came_de_ergonomia(env, raio_max_mm=100)
        # Then usa o grupo muscular do exercício
        assert perfil["grupo_muscular"] == "biceps"
        # And a amplitude vem da ADM de treino (10-135 -> 125 graus)
        assert perfil["amplitude_graus"] == pytest.approx(125.0)
