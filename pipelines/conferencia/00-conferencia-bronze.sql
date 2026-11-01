-- Conferência da bronze: as 11 tabelas do Meridian Bank S.A. (9 de portfólio + 2 de risco bancário e Pix)
-- Se qualquer contagem divergir, raise_error() interrompe o job antes do pipeline Medalhão.

WITH contagem AS (
  SELECT 'projetos' AS tabela, 60 AS esperado, (SELECT COUNT(*) FROM lakehouse_meridian.bronze.projetos) AS obtido
  UNION ALL SELECT 'status_semanal',           3911,  (SELECT COUNT(*) FROM lakehouse_meridian.bronze.status_semanal)
  UNION ALL SELECT 'excel_tarefas',            1663,  (SELECT COUNT(*) FROM lakehouse_meridian.bronze.excel_tarefas)
  UNION ALL SELECT 'clickup_tarefas',          2119,  (SELECT COUNT(*) FROM lakehouse_meridian.bronze.clickup_tarefas)
  UNION ALL SELECT 'msproject_tarefas',        1260,  (SELECT COUNT(*) FROM lakehouse_meridian.bronze.msproject_tarefas)
  UNION ALL SELECT 'colaboradores',            523,   (SELECT COUNT(*) FROM lakehouse_meridian.bronze.colaboradores)
  UNION ALL SELECT 'apontamentos',             30883, (SELECT COUNT(*) FROM lakehouse_meridian.bronze.apontamentos)
  UNION ALL SELECT 'custos',                   23640, (SELECT COUNT(*) FROM lakehouse_meridian.bronze.custos)
  UNION ALL SELECT 'entregas_fornecedor',      640,   (SELECT COUNT(*) FROM lakehouse_meridian.bronze.entregas_fornecedor)
  UNION ALL SELECT 'carteira_credito_pdd',     720,   (SELECT COUNT(*) FROM lakehouse_meridian.bronze.carteira_credito_pdd)
  UNION ALL SELECT 'monitoramento_fraude_pix', 810,   (SELECT COUNT(*) FROM lakehouse_meridian.bronze.monitoramento_fraude_pix)
)
SELECT tabela, esperado, obtido,
       CASE WHEN esperado = obtido THEN 'ok'
            ELSE raise_error(concat('bronze.', tabela, ': esperado ', esperado, ', veio ', obtido,
                                    '. Veja a saída da tarefa ingestao_data_lake.'))
       END AS status
FROM contagem;
