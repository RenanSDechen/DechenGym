"""
Testes do módulo de Geração OpenSCAD — estrutura BDD (Given/When/Then).
"""

import json

from dechengym.geracao_openscad import (
    gerar_memorial_descritivo,
    gerar_script_openscad,
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
