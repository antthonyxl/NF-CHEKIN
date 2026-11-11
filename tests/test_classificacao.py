import unittest
from pathlib import Path

import pandas as pd

from classificacao import (
    NAO_CLASSIFICADO, chave_unidade, classificar_unidades,
    filtrar_hierarquia, ler_classificacao,
)


class FiltrosHierarquiaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cadastro = ler_classificacao(Path(__file__).resolve().parents[1] / "classificacao_unidades.csv")

    def test_equivalencia_de_nomes_sem_ativar_falsos_positivos(self):
        self.assertEqual(chave_unidade("002-VIT.SA"), chave_unidade("Vit.Sa"))
        self.assertEqual(chave_unidade("008-2 IRMAOS"), chave_unidade("2 Irmaos"))
        self.assertEqual(chave_unidade("031-RIBEIRAO"), chave_unidade("Ribeirão"))
        self.assertNotEqual(chave_unidade("022-BARREIRO"), chave_unidade("Barro"))

    def test_classifica_e_preserva_unidades_sem_mapeamento(self):
        dados = pd.DataFrame({
            "EMPRESA": ["001-CARPINA", "002-VIT.SA", "005-BONGI", "025-TAMBAU", "998-CD FLV P"],
            "NUMERONF": ["1", "2", "3", "4", "5"],
        })
        classificados = classificar_unidades(dados, self.cadastro)
        self.assertEqual(len(classificados), len(dados))
        self.assertEqual(classificados["NUMERONF"].tolist(), dados["NUMERONF"].tolist())
        self.assertEqual(classificados["REGIONAL"].tolist(), [
            "FERNANDO CAZZETTA", "FERNANDO CAZZETTA", "ANTÔNIO PINHO", NAO_CLASSIFICADO, NAO_CLASSIFICADO
        ])
        self.assertEqual(classificados["DISTRITAL"].tolist(), [
            "DIVANE LOPES", "DIVANE LOPES", "ROMULO EMANUEL", NAO_CLASSIFICADO, NAO_CLASSIFICADO
        ])

    def test_filtro_regional_distrital_e_combinações(self):
        dados = pd.DataFrame({"EMPRESA": ["001-CARPINA", "002-VIT.SA", "005-BONGI", "998-CD FLV P"]})
        classificados = classificar_unidades(dados, self.cadastro)
        self.assertEqual(len(filtrar_hierarquia(classificados)), 4)
        self.assertEqual(len(filtrar_hierarquia(classificados, ["FERNANDO CAZZETTA"])), 2)
        self.assertEqual(len(filtrar_hierarquia(classificados, distritais=["ROMULO EMANUEL"])), 1)
        self.assertEqual(len(filtrar_hierarquia(classificados, ["FERNANDO CAZZETTA"], ["ROMULO EMANUEL"])), 0)
        self.assertEqual(len(filtrar_hierarquia(classificados, [NAO_CLASSIFICADO])), 1)


if __name__ == '__main__':
    unittest.main()
