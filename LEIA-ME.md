# Correção da ordenação da visualização de apresentação

Esta atualização altera somente a ordenação inicial da visualização compartilhável (
`?visao=sem-checkin`): o custo líquido passa a ser exibido do maior para o menor.

- Lojas com custo localizado aparecem em ordem decrescente de custo líquido.
- Lojas sem custo localizado permanecem no final.
- O indicador de ordenação mostra a seta de ordem decrescente.
- A ordenação manual pelos cabeçalhos continua funcionando normalmente.
- KPIs, filtros, conciliação, consultas ao BigQuery e layout não foram alterados.

## Como aplicar

1. Faça uma cópia de segurança dos arquivos atuais `app.py` e `matriz.py`.
2. Substitua esses dois arquivos pelos arquivos deste pacote, mantendo-os na raiz do projeto.
3. Execute localmente: `streamlit run app.py`.
4. Abra a visualização de apresentação e confira a coluna **Custo líquido**.

Não é necessário executar SQL, reenviar dados ou alterar `requirements.txt`.
