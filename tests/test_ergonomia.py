"""
Testes do módulo de Ergonomia — estrutura BDD (Given/When/Then).
===============================================================

Cobrem antropometria/faixas de ajuste, amplitude de movimento, padrão de
pegada (orientação/largura/diâmetro), curva de resistência e o integrador
de projeto ergonômico.
"""

import pytest

from dechengym.ergonomia import (
    avaliar_curva_resistencia,
    calcular_alinhamento_pivo,
    calcular_faixa_ajuste,
    calcular_largura_pegada,
    dimensionar_pega,
    gerar_perfil_resistencia_alvo,
    get_amplitude_movimento,
    get_antropometria,
    get_curva_forca,
    get_padrao_pegada,
    projetar_ergonomia,
    validar_amplitude_projetada,
)


# ==========================================================================
# Antropometria
# ==========================================================================
class TestAntropometria:
    def test_retorna_medida_por_percentil_e_sexo(self):
        # Given uma medida, percentil e sexo
        # When consultamos a antropometria
        valor = get_antropometria("altura_poplitea", 50, "masculino")
        # Then deve retornar o valor tabelado (mm)
        assert valor == pytest.approx(440.0)

    def test_interpola_percentil_intermediario(self):
        # Given um percentil intermediário (25) entre P5 e P50
        # When consultamos
        p25 = get_antropometria("estatura", 25, "masculino")
        # Then deve ficar entre P5 (1650) e P50 (1755)
        assert 1650 < p25 < 1755

    def test_medida_inexistente_levanta_erro(self):
        # Given uma medida inexistente
        # When consultada
        # Then levanta KeyError
        with pytest.raises(KeyError):
            get_antropometria("tamanho_orelha", 50, "masculino")


class TestFaixaAjuste:
    def test_curso_cobre_mulher_p5_a_homem_p95(self):
        # Given o assento (altura poplitea) e o envelope "ambos"
        # When calculamos a faixa de ajuste
        faixa = calcular_faixa_ajuste("altura_poplitea", sexo="ambos")
        # Then o mínimo vem da mulher P5 e o máximo do homem P95
        assert faixa["minimo_mm"] == pytest.approx(355.0)  # feminino P5
        assert faixa["maximo_mm"] == pytest.approx(490.0)  # masculino P95
        # And o curso é positivo
        assert faixa["curso_mm"] == pytest.approx(135.0)


# ==========================================================================
# Amplitude de movimento (ADM)
# ==========================================================================
class TestAmplitudeMovimento:
    def test_retorna_adm_anatomica_e_de_treino(self):
        # Given cotovelo/flexão
        # When consultamos a ADM
        adm = get_amplitude_movimento("cotovelo", "flexao")
        # Then traz as duas faixas e a amplitude de treino
        assert adm["adm_anatomica"] == [0, 145]
        assert adm["adm_treino"] == [10, 135]
        assert adm["amplitude_treino_graus"] == pytest.approx(125.0)

    def test_arco_dentro_da_adm_e_aprovado(self):
        # Given um arco de 20 a 130 graus para flexão de cotovelo
        # When validamos
        rel = validar_amplitude_projetada("cotovelo", "flexao", 20, 130)
        # Then é aprovado (dentro de 10-135)
        assert rel["aprovado"] is True

    def test_arco_excede_adm_e_reprovado_com_sugestao(self):
        # Given um arco de 0 a 150 graus (excede o máximo de treino 135)
        # When validamos
        rel = validar_amplitude_projetada("cotovelo", "flexao", 0, 150)
        # Then é reprovado
        assert rel["aprovado"] is False
        # And sugere o arco corrigido (clamp em 10-135)
        assert rel["arco_sugerido_graus"] == [10, 135]
        assert rel["violacoes"]


# ==========================================================================
# Padrão de pegada
# ==========================================================================
class TestPadraoPegada:
    def test_orientacao_supinada_enfatiza_biceps(self):
        # Given a orientação supinada
        # When consultamos o padrão
        pegada = get_padrao_pegada("supinada")
        # Then descreve o ângulo do antebraço e a ênfase
        assert pegada["angulo_antebraco_graus"] == -90
        assert "iceps" in pegada["enfase"]

    def test_diametro_pega_conforto_na_faixa_esperada(self):
        # Given objetivo de conforto para homem P50
        # When dimensionamos a pega
        spec = dimensionar_pega("conforto", 50, "masculino")
        # Then o diâmetro fica na faixa de conforto (28-45 mm)
        assert 28.0 <= spec["diametro_recomendado_mm"] <= 45.0
        # And ~20% do comprimento da mão (189 mm -> ~37.8 mm)
        assert spec["diametro_ideal_mm"] == pytest.approx(37.8, abs=0.2)

    def test_diametro_pega_forca_preensao_e_mais_grosso(self):
        # Given objetivos diferentes
        conforto = dimensionar_pega("conforto", 50, "masculino")
        fat = dimensionar_pega("forca_preensao", 50, "masculino")
        # Then a pega de força de preensão é mais grossa
        assert fat["diametro_recomendado_mm"] > conforto["diametro_recomendado_mm"]

    def test_diametro_por_comprimento_mao_direto(self):
        # Given um comprimento de mão informado diretamente
        # When dimensionamos
        spec = dimensionar_pega("conforto", comprimento_mao_mm=200)
        # Then usa o valor informado (200 * 0.20 = 40)
        assert spec["diametro_ideal_mm"] == pytest.approx(40.0)

    def test_largura_pegada_aberta_maior_que_media(self):
        # Given pegadas média e aberta para o mesmo usuário
        media = calcular_largura_pegada("media", 50, "masculino")
        aberta = calcular_largura_pegada("aberta", 50, "masculino")
        # Then a aberta é mais larga que a média
        assert aberta["distancia_entre_pegas_mm"] > media["distancia_entre_pegas_mm"]
        # And a média equivale à largura biacromial
        assert media["distancia_entre_pegas_mm"] == pytest.approx(400.0)


# ==========================================================================
# Curva de resistência x curva de força
# ==========================================================================
class TestCurvaResistencia:
    def test_biceps_tem_curva_em_sino(self):
        # Given o bíceps
        # When consultamos a curva de força
        curva = get_curva_forca("biceps")
        # Then é do tipo sino com pico no meio
        assert curva["tipo"] == "sino"
        assert curva["perfil"][2] == max(curva["perfil"])

    def test_perfil_alvo_proporcional_a_carga_de_pico(self):
        # Given carga de pico de 50 kg para o bíceps
        # When geramos o perfil-alvo
        alvo = gerar_perfil_resistencia_alvo("biceps", 50)
        # Then o pico do perfil corresponde à carga de pico
        assert max(alvo["resistencia_alvo_kg"]) == pytest.approx(50.0)

    def test_maquina_que_segue_a_curva_pontua_alto(self):
        # Given uma máquina cujo perfil é idêntico à curva de força do bíceps
        curva = get_curva_forca("biceps")
        # When avaliamos o casamento
        aval = avaliar_curva_resistencia(list(curva["perfil"]), "biceps")
        # Then a pontuação é máxima
        assert aval["pontuacao"] == pytest.approx(100.0)

    def test_resistencia_constante_descasa_de_curva_em_sino(self):
        # Given uma máquina de resistência constante (came circular)
        # When avaliamos contra o bíceps (curva em sino)
        aval = avaliar_curva_resistencia([1, 1, 1, 1, 1], "biceps")
        # Then a pontuação cai (descasamento) e há recomendação
        assert aval["pontuacao"] < 100.0
        assert aval["recomendacao"]

    def test_tamanho_de_perfil_incompativel_levanta_erro(self):
        # Given um perfil com número errado de amostras
        # When avaliamos
        # Then levanta ValueError
        with pytest.raises(ValueError):
            avaliar_curva_resistencia([1, 2, 3], "biceps")


# ==========================================================================
# Alinhamento de pivô e integrador
# ==========================================================================
class TestProjetoErgonomico:
    def test_alinhamento_pivo_usa_medida_de_referencia(self):
        # Given a altura do cotovelo sentado como referência
        # When calculamos o alinhamento do pivô
        al = calcular_alinhamento_pivo("altura_cotovelo_sentado", 50, "masculino")
        # Then a altura do pivô corresponde à medida e traz faixa de ajuste
        assert al["altura_pivo_mm"] == pytest.approx(245.0)
        assert al["faixa_ajuste_p5_p95"]["curso_mm"] > 0

    def test_envelope_completo_da_rosca_biceps(self):
        # Given o exercício rosca de bíceps
        # When projetamos a ergonomia
        env = projetar_ergonomia("rosca_biceps", percentil=50, sexo="masculino")
        # Then o envelope reúne todos os blocos ergonômicos
        assert env["articulacao"] == "cotovelo"
        assert env["movimento"] == "flexao"
        assert env["grupo_muscular"] == "biceps"
        # And o padrão de pegada da rosca é supinada
        assert env["pegada"]["orientacao"]["orientacao"] == "supinada"
        # And traz alinhamento de pivô, ADM e curva-alvo
        assert env["alinhamento_pivo"]["altura_pivo_mm"] > 0
        assert env["amplitude_movimento"]["adm_treino"] == [10, 135]
        assert env["curva_resistencia_alvo"]["resistencia_alvo_kg"]

    def test_exercicio_inexistente_levanta_erro(self):
        # Given um exercício fora do catálogo
        # When projetamos
        # Then levanta KeyError
        with pytest.raises(KeyError):
            projetar_ergonomia("voar")


# ==========================================================================
# Regressões (defeitos corrigidos na auditoria)
# ==========================================================================
class TestRegressoes:
    def test_faixa_ambos_usa_maior_entre_sexos(self):
        # Regressão do Defeito #1: na largura do quadril a mulher P95 (420) é
        # mais larga que o homem P95 (400); "ambos" não pode assumir homem=máx.
        # Given a largura do quadril e o envelope "ambos"
        faixa = calcular_faixa_ajuste("largura_quadril_sentado", sexo="ambos")
        # Then o máximo acomoda a mulher P95 (420 mm), não os 400 do homem
        assert faixa["maximo_mm"] == pytest.approx(420.0)

    def test_extensao_cotovelo_tem_amplitude_de_trabalho(self):
        # Regressão do Defeito #2: extensão de cotovelo (tríceps) é trabalhada
        # pelo arco de flexão — não pode ter amplitude zero.
        adm = get_amplitude_movimento("cotovelo", "extensao")
        assert adm["amplitude_treino_graus"] > 0
        assert adm["adm_treino"] == [10, 135]

    def test_extensao_joelho_tem_amplitude_de_trabalho(self):
        # Regressão do Defeito #2: cadeira extensora percorre o arco de flexão.
        adm = get_amplitude_movimento("joelho", "extensao")
        assert adm["amplitude_treino_graus"] > 0
        assert adm["adm_treino"] == [0, 120]

    def test_cadeira_abdutora_nao_alinha_pelo_ombro(self):
        # Regressão do Defeito #3: máquina de quadril não pode alinhar o pivô
        # pela altura do ombro.
        env = projetar_ergonomia("cadeira_abdutora")
        assert env["alinhamento_pivo"]["medida_referencia"] != "altura_ombro_sentado"
        assert env["articulacao"] == "quadril"

    def test_valores_diretos_negativos_na_pega_levantam_erro(self):
        # Regressão do Defeito #4: guardas de entrada para valores diretos.
        with pytest.raises(ValueError):
            dimensionar_pega("conforto", comprimento_mao_mm=-10)
        with pytest.raises(ValueError):
            calcular_largura_pegada("media", largura_biacromial_mm=-10)
