# Análise dos arquivos enviados — 11/11/2026

## Estrutura

| Métrica | ENTRADA AUTO NF LOJAS | CHECKIN |
|:--|--:|--:|
| Linhas de dados | 16.106 | 184.977 |
| Unidades distintas pela descrição | 77 | 82 |
| Identificador da nota | `NUMERONF` | `Nota` |
| Unidade | `EMPRESA` | `Loja` |
| Valor financeiro | — | `Valor` |
| Número/estado do check-in | — | `Check-In` / `Status Check-In` |

**Exemplos de tratamento:** `75137-1` → `75137`; `1776754-001` → `1776754`.
O sufixo é removido apenas da coluna `Nota` do CHECKIN. Identificadores numéricos
recebem normalização coerente dos zeros à esquerda.

## Resultado da conciliação

Chave **código da unidade + NF normalizada**, mantendo todas as linhas da Auto NF.

| Situação da ENTRADA AUTO NF | Registros |
|:--|--:|
| Localizado (correspondência única) | 2.108 |
| Múltiplos check-ins para a mesma unidade + NF | 59 |
| Sem correspondência no CHECKIN enviado | 13.939 |
| Identificadores inválidos | 0 |
| **Total de registros** | **16.106** |

Total com alguma correspondência: **2.167** registros (13,5%).
Sem correspondência: **13.939** registros (86,5%).

Há **49 combinações únicas de unidade + NF com múltiplos check-ins**, afetando
59 linhas da Auto NF, para **101 registros candidatos** do CHECKIN.
Essas ocorrências são apresentadas separadamente, sem inventar um valor financeiro.

**Valor total de notas localizadas sem ambiguidade:** R$ 24.520.649,14,
contabilizando apenas uma vez cada combinação unidade + NF na Auto NF.

## Qualidade e cautelas

- A Auto NF possui 903 repetições adicionais da combinação unidade + NF;
  **nenhuma linha foi removida** da tabela operacional.
- Buscar apenas pelo número da NF, sem restringir à loja, geraria **2.602
  combinações únicas que só aparecem em outra unidade** no CHECKIN. Não
  devem ser tratadas como acertos na unidade de origem.
- No arquivo Auto, a coluna `NFECHAVEACESSO` contém valores em notação científica;
  isso impede utilizá-la com segurança como identificador completo de 44 dígitos.
- A ausência de correspondência se refere aos arquivos analisados, e não a todo
  o histórico dos sistemas de origem.
- Há notas sem o sufixo `-série` no CHECKIN: o sistema mantém essas notas
  como estão, sem descartá-las.

A análise foi testada com os dois arquivos originais enviados e as quatro
rotinas de teste do projeto foram executadas com sucesso.
