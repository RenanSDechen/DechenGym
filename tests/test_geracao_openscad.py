"""
Testes do módulo de Geração OpenSCAD — estrutura BDD (Given/When/Then).
"""

import json

import pytest

from dechengym.ergonomia import projetar_ergonomia
from dechengym.geracao_openscad import (
    gerar_memorial_descritivo,
    gerar_script_openscad,
    parametros_geometria_de_ergonomia,
)


class TestGerarScriptOpenscad:
    """Contrato da ferramenta de geração de geometria paramétrica."""

    def test_gera_scad_com_parametros_injetados(self):
        # Given parâmetros de geometria de um braço articulado
        parametros = {
            "nome": "leg_extension",
            "altura_coluna_mm": 1000,
            "comprimento_alavanca_mm": 800,
            "espessura_parede_mm": 3.0,
        }
        # When geramos o script OpenSCAD
        scad = gerar_script_openscad(parametros)

        # Then o resultado é um texto .scad não vazio
        assert isinstance(scad, str)
        assert len(scad) > 0
        # And os parâmetros informados aparecem parametrizados no código
        assert "altura_coluna       = 1000;" in scad
        assert "comprimento_alavanca= 800;" in scad
        assert "leg_extension" in scad
        # And os módulos estruturais essenciais foram declarados
        for modulo in ("module base()", "module coluna()", "module alavanca()"):
            assert modulo in scad

    def test_usa_padroes_quando_sem_parametros(self):
        # Given nenhuma entrada
        # When geramos o script
        scad = gerar_script_openscad()
        # Then usa os parâmetros padrão de referência
        assert "braco_articulado" in scad
        assert "maquina_articulada();" in scad


class TestGerarMemorialDescritivo:
    """Contrato do memorial descritivo (lista de cortes / materiais)."""

    def test_memorial_contem_lista_de_cortes(self):
        # Given parâmetros de geometria válidos
        parametros = {"perfil_base_mm": 50, "perfil_coluna_mm": 50}
        # When geramos o memorial
        memorial = gerar_memorial_descritivo(parametros)

        # Then deve conter a lista de cortes e o peso total
        assert "lista_cortes" in memorial
        assert len(memorial["lista_cortes"]) >= 4
        assert memorial["peso_total_estrutura_kg"] > 0
        # And cada peça deve ter comprimento de corte e quantidade
        for peca in memorial["lista_cortes"]:
            assert peca["comprimento_corte_mm"] > 0
            assert peca["quantidade"] >= 1

    def test_memorial_serializavel_em_json(self):
        # Given a opção como_json
        # When geramos o memorial serializado
        memorial_json = gerar_memorial_descritivo({}, como_json=True)
        # Then deve ser uma string JSON válida e parseável
        assert isinstance(memorial_json, str)
        dados = json.loads(memorial_json)
        assert dados["tipo"] == "maquina_articulada"


class TestRegressoesGeometria:
    """Regressões de defeitos encontrados na auditoria."""

    def test_pega_fica_na_ponta_da_alavanca_e_nao_acima_do_pivo(self):
        # Regressão (auditoria): a pega estava deslocada em +Z (acima do pivô);
        # a alavanca se estende em +X, então a pega deve somar comprimento em X.
        scad = gerar_script_openscad({"comprimento_alavanca_mm": 800})
        assert "- perfil_alavanca/2 + comprimento_alavanca" in scad
        # E não deve mais somar o comprimento da alavanca no eixo Z.
        assert "altura_coluna + comprimento_alavanca" not in scad

    def test_pivo_da_ergonomia_desconta_a_altura_da_base(self):
        # Regressão (auditoria): pivô ficava perfil_base acima da altura
        # anatômica (o .scad coloca o pivô em perfil_base + altura_coluna).
        env = projetar_ergonomia("rosca_biceps", percentil=50, sexo="masculino")
        altura_pivo = env["alinhamento_pivo"]["altura_pivo_mm"]
        par = parametros_geometria_de_ergonomia(env, extras={"perfil_base_mm": 50})
        assert par["altura_coluna_mm"] == pytest.approx(altura_pivo - 50)

    def test_memorial_sinaliza_peso_nao_estimado(self):
        # Regressão (auditoria): peso não pode ser silenciosamente 0 para perfil
        # fora do catálogo — deve sinalizar via avisos e flags.
        memorial = gerar_memorial_descritivo({"perfil_base_mm": 45})  # 45x45 inexistente
        assert memorial["peso_total_completo"] is False
        assert memorial["avisos"]
        base = [p for p in memorial["lista_cortes"] if "base" in p["descricao"].lower()]
        assert base and all(p["peso_estimado"] is False for p in base)
        assert all(p["peso_total_kg"] is None for p in base)

    def test_memorial_valido_permanece_completo(self):
        # Um perfil dentro do catálogo mantém peso estimado e sem avisos.
        memorial = gerar_memorial_descritivo({})  # padrões (todos no catálogo)
        assert memorial["peso_total_completo"] is True
        assert memorial["avisos"] == []
