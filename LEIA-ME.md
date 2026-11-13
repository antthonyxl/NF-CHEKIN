# NF / CHECK-IN — atualizações programadas

## O que mudou

- O dashboard deixa de expirar o cache principal a cada 10 minutos.
- As atualizações automáticas são programadas para **08:00, 12:00 e 17:00**, no fuso `America/Sao_Paulo` (horário de Brasília).
- A sessão ativa agenda somente o próximo horário, usando `st.fragment`; não existe verificação a cada minuto.
- Na virada de cada horário, o Streamlit executa um rerun completo, invalida o cache de leitura do BigQuery uma única vez por processo e carrega novamente as três bases.
- Os reruns causados por filtros, abas ou outras interações reutilizam os dados em cache, sem consultar o BigQuery novamente.
- O botão **Atualizar dados agora** foi mantido como atualização manual extraordinária.
- `matriz.py` foi incluído sem alterações; a matriz não participa do agendamento.

## Como aplicar

1. Faça uma cópia de segurança do `app.py` atual.
2. Substitua o `app.py` pelo arquivo deste pacote.
3. **Não é necessário substituir `matriz.py`**; ele está incluído apenas para preservar a versão que você enviou.
4. Não altere `fonte_bigquery.py`, `requirements.txt`, `.streamlit/secrets.toml` ou as tabelas do BigQuery para esta atualização.
5. Inicie localmente:

```powershell
streamlit run app.py
```

## Comportamento e limite importante

O agendamento do `st.fragment` funciona enquanto houver uma sessão do dashboard ativa e conectada. Se ninguém estiver com o dashboard aberto, não há uma sessão de navegador para disparar o rerun naquele horário; quando alguém abrir o app depois, ele identifica a janela vigente e carrega os dados atuais do BigQuery.

O botão manual continua permitindo uma atualização fora dos três horários. Se a regra precisar ser estritamente limitada a três atualizações, inclusive sem permitir atualização manual, remova o botão `Atualizar dados agora`.

## Validação realizada

- Sintaxe Python (`py_compile`) aprovada para `app.py` e `matriz.py`.
- Cálculo da janela anterior e do próximo horário testado para antes e depois de 08h, 12h e 17h.
- Não foi possível validar a conexão real com o BigQuery neste ambiente.
