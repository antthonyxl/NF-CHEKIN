import unittest

from consultas_bigquery import _AUTO_SQL, _CHECKIN_SQL, consulta_custos_relevantes, consulta_tabela


class ConsultaBigQueryTeste(unittest.TestCase):
    def test_campos_equivalentes_aos_xlsx_originais(self):
        a = consulta_tabela("empresa-bi-123", "controle_recebimento", "entrada_auto_nf", _AUTO_SQL)
        c = consulta_tabela("empresa-bi-123", "controle_recebimento", "checkin", _CHECKIN_SQL)
        self.assertIn("`empresa-bi-123.controle_recebimento.entrada_auto_nf`", a)
        self.assertIn("AS `EMPRESA`", a)
        self.assertIn("AS `NUMERONF`", a)
        self.assertIn("AS `Nota`", c)
        self.assertIn("AS `Check-In`", c)
        self.assertEqual(len(_AUTO_SQL), 8)
        self.assertEqual(len(_CHECKIN_SQL), 10)


    def test_custos_filtrados_por_chaves_da_auto_nf(self):
        sql = consulta_custos_relevantes("empresa-bi-123", "controle_recebimento")
        self.assertIn("`empresa-bi-123.controle_recebimento.custo_nf_entrada`", sql)
        self.assertIn("`empresa-bi-123.controle_recebimento.entrada_auto_nf`", sql)
        self.assertIn("WHERE EXISTS", sql)
        self.assertIn("REGEXP_EXTRACT", sql)
        self.assertIn("SAFE_CAST", sql)

    def test_consulta_custos_recusa_identificador_inseguro(self):
        with self.assertRaises(ValueError):
            consulta_custos_relevantes("p` DROP TABLE t; --", "controle_recebimento")

    def test_identificadores_inseguros_recusados(self):
        with self.assertRaises(ValueError):
            consulta_tabela("p` DROP TABLE t; --", "controle_recebimento", "checkin", _CHECKIN_SQL)


if __name__ == "__main__":
    unittest.main()
