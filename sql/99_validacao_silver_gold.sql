-- Validação de Engenharia de Dados e IA (Camadas Silver, Gold e Risco Bancário — Meridian Bank S.A.)
-- Confere se o pipeline declarativo (Lakeflow SDP) e a extração via IA generativa (ai_query)
-- chegaram nos números exatos da especificação determinística (seed=42).
--
-- Execução via CLI:
--   python scripts/run_sql.py sql/99_validacao_silver_gold.sql --profile vertice

WITH v AS (
  -- silver: integração das 3 ferramentas, limpeza e contratos de qualidade
  SELECT 1 AS n, 'projetos com cronograma nas 3 ferramentas' AS item, 60 AS esperado,
         (SELECT COUNT(DISTINCT projeto_id) FROM lakehouse_meridian.silver.tarefas) AS obtido
  UNION ALL SELECT 2, 'tarefas na silver (sem TOTAL e sem tarefa-resumo)', 4917,
         (SELECT COUNT(*) FROM lakehouse_meridian.silver.tarefas)
  UNION ALL SELECT 3, 'tarefas do Excel acima de 100% (cortadas e sinalizadas)', 11,
         (SELECT COUNT_IF(pct_veio_acima_de_100) FROM lakehouse_meridian.silver.tarefas)
  UNION ALL SELECT 4, 'pessoas únicas (523 linhas no RH → 520)', 520,
         (SELECT COUNT(*) FROM lakehouse_meridian.silver.colaboradores)
  UNION ALL SELECT 5, 'grafias da CodeForge que viraram 1 fornecedor', 4,
         (SELECT COUNT(DISTINCT fornecedor_como_veio) FROM lakehouse_meridian.silver.entregas_fornecedor
          WHERE fornecedor = 'CodeForge Consultoria Ltda')
  UNION ALL SELECT 6, 'custos com vírgula decimal recuperados', 671,
         (SELECT COUNT_IF(valor_veio_com_virgula) FROM lakehouse_meridian.silver.custos)
  UNION ALL SELECT 7, 'custo real total (R$ mi) — reconciliado bronze = silver', 193,
         (SELECT CAST(ROUND(SUM(valor) / 1e6) AS INT) FROM lakehouse_meridian.silver.custos)
  -- gold: as perguntas executivas da Diretoria
  UNION ALL SELECT 8, 'projetos críticos (SPI ou CPI < 0,8)', 7,
         (SELECT COUNT(*) FROM lakehouse_meridian.gold.projeto_situacao_atual WHERE situacao = 'crítico')
  UNION ALL SELECT 9, 'projetos em atenção', 10,
         (SELECT COUNT(*) FROM lakehouse_meridian.gold.projeto_situacao_atual WHERE situacao = 'atenção')
  UNION ALL SELECT 10, 'estouro previsto (R$ mil)', 6465,
         (SELECT CAST(ROUND(SUM(estouro_previsto) / 1e3) AS INT) FROM lakehouse_meridian.gold.projeto_situacao_atual
          WHERE status = 'em_andamento')
  UNION ALL SELECT 11, 'melancias (farol verde, SPI < 0,9)', 4,
         (SELECT COUNT_IF(melancia) FROM lakehouse_meridian.gold.projeto_situacao_atual)
  -- fornecedor: SLA e atrasos
  UNION ALL SELECT 12, 'CodeForge: % das entregas feitas no prazo', 0,
         (SELECT CAST(ROUND(100 * AVG(CASE WHEN data_entrega <= data_prometida THEN 1.0 ELSE 0.0 END)) AS INT)
          FROM lakehouse_meridian.silver.entregas_fornecedor
          WHERE fornecedor = 'CodeForge Consultoria Ltda' AND data_entrega IS NOT NULL)
  UNION ALL SELECT 13, 'entregas de fornecedor em atraso hoje', 5,
         (SELECT COUNT_IF(em_atraso) FROM lakehouse_meridian.silver.entregas_fornecedor)
  UNION ALL SELECT 14, 'CodeForge: prazo real ÷ prometido (×100)', 141,
         (SELECT CAST(ROUND(AVG(prazo_real_dias / prazo_prometido_dias) * 100) AS INT)
          FROM lakehouse_meridian.silver.entregas_fornecedor
          WHERE fornecedor = 'CodeForge Consultoria Ltda')
  UNION ALL SELECT 15, 'SREs < 20% de uso nas últimas 12 semanas', 2,
         (SELECT COUNT(*) FROM (SELECT colaborador_id FROM lakehouse_meridian.gold.utilizacao_pessoa_semana
                                WHERE papel = 'sre' AND semana > DATE'2026-07-24'
                                GROUP BY colaborador_id HAVING SUM(horas_apontadas) / SUM(horas_disponiveis) < 0.2))
  -- IA generativa (ai_query)
  UNION ALL SELECT 16, 'status semanais estruturados (todos)', 3911,
         (SELECT COUNT(*) FROM lakehouse_meridian.gold.status_estruturado)
  UNION ALL SELECT 17, 'semanas do PRJ-011 com falta de SRE (90 dias)', 12,
         (SELECT COUNT(*) FROM lakehouse_meridian.gold.status_estruturado
          WHERE projeto_id = 'PRJ-011' AND data_status >= DATE'2026-07-18' AND causa_bloqueio = 'falta_sre')
  UNION ALL SELECT 18, 'status classificados pela IA (últimos 90 dias, com bloqueio)', 163,
         (SELECT COUNT_IF(metodo = 'ia') FROM lakehouse_meridian.gold.status_estruturado)
  -- KPI da carteira e feriados
  UNION ALL SELECT 19, 'margem projetada da carteira (×1000)', 204,
         (SELECT CAST(ROUND((SUM(valor_contrato) - SUM(eac)) / SUM(valor_contrato) * 1000) AS INT)
          FROM lakehouse_meridian.gold.projeto_situacao_atual WHERE status = 'em_andamento')
  UNION ALL SELECT 20, 'bronze.feriados carregada pela ingestão (1 = sim)', 1,
         (SELECT CAST(COUNT(*) > 0 AS INT) FROM lakehouse_meridian.bronze.feriados)
  -- Risco Bancário (Resolução CMN 4.966 / PDD e Fraude Pix / MED BACEN)
  UNION ALL SELECT 21, 'silver.carteira_credito_pdd (720 registros tipados)', 720,
         (SELECT COUNT(*) FROM lakehouse_meridian.silver.carteira_credito_pdd)
  UNION ALL SELECT 22, 'silver.monitoramento_fraude_pix (810 registros tipados)', 810,
         (SELECT COUNT(*) FROM lakehouse_meridian.silver.monitoramento_fraude_pix)
  UNION ALL SELECT 23, 'gold.risco_credito_e_operacional (60 programas bancários)', 60,
         (SELECT COUNT(*) FROM lakehouse_meridian.gold.risco_credito_e_operacional)
)
SELECT n, item, esperado, obtido, CASE WHEN esperado = obtido THEN 'ok' ELSE 'CONFIRA' END AS status
FROM v ORDER BY n;
