-- Validação de Machine Learning, Governança Semântica e Databricks App (Meridian Bank S.A.)
-- Confere a tabela de features, métricas do modelo preditivo de estouro em 30 dias,
-- ranking de risco futuro, Metric View governada (mv_projetos) e indicadores operacionais do App.
--
-- Execução via CLI:
--   python scripts/run_sql.py sql/99_validacao_ml_governanca_app.sql --profile vertice

WITH m AS (SELECT * FROM lakehouse_meridian.ml.modelo_metricas),
s AS (SELECT * FROM lakehouse_meridian.gold.score_estouro_30d),
f AS (SELECT * FROM lakehouse_meridian.ml.features_projeto_semana),
p AS (SELECT * FROM lakehouse_meridian.gold.projeto_situacao_atual),
checagens AS (
  -- 1 · Engenharia de Features e Modelo Preditivo (30 dias)
  SELECT 'features: linhas' AS item, '4235' AS esperado, CAST(COUNT(*) AS STRING) AS obtido FROM f UNION ALL
  SELECT 'features: linhas de treino (elegível com rótulo)', '1643', CAST(COUNT_IF(elegivel = 1 AND estoura_30d IS NOT NULL) AS STRING) FROM f UNION ALL
  SELECT 'features: taxa base', '0.167', CAST(ROUND(AVG(CASE WHEN elegivel = 1 THEN estoura_30d END), 3) AS STRING) FROM f UNION ALL
  SELECT 'features: nenhum alvo preenchido hoje', '0', CAST(COUNT_IF(semana = DATE'2026-10-16' AND alvo_pior_indice_30d IS NOT NULL) AS STRING) FROM f UNION ALL
  SELECT 'modelo: AUC (2 casas)', '0.92', CAST(ROUND(auc, 2) AS STRING) FROM m UNION ALL
  SELECT 'modelo: AUC da regra da folga (2 casas)', '0.87', CAST(ROUND(auc_baseline_folga, 2) AS STRING) FROM m UNION ALL
  SELECT 'modelo: ganha da regra da folga', 'true', CAST(auc >= auc_baseline_folga AS STRING) FROM m UNION ALL
  SELECT 'modelo: AUC abaixo de 0,98 (sem vazamento)', 'true', CAST(auc < 0.98 AS STRING) FROM m UNION ALL
  SELECT 'modelo: estouros avisados no top 5', '9 de 10', estouros_avisados || ' de ' || estouros_teste FROM m UNION ALL
  SELECT 'modelo: antecedência média (dias, arredondado)', '41', CAST(CAST(ROUND(antecedencia_media_dias) AS INT) AS STRING) FROM m UNION ALL
  SELECT 'score: uma linha por projeto em andamento', '41', CAST(COUNT(*) AS STRING) FROM s UNION ALL
  SELECT 'score: data de referência', '2026-10-16', CAST(MAX(data_referencia) AS STRING) FROM s UNION ALL
  SELECT 'score: faixa alto · medio · baixo', '18 · 4 · 19',
         COUNT_IF(faixa_risco = 'alto') || ' · ' || COUNT_IF(faixa_risco = 'medio') || ' · ' || COUNT_IF(faixa_risco = 'baixo') FROM s UNION ALL
  SELECT 'score: todo projeto crítico ou em atenção com prob 1,0', '17',
         CAST((SELECT COUNT(*) FROM s s2 JOIN p USING (projeto_id)
               WHERE p.situacao IN ('crítico', 'atenção') AND s2.prob_estouro_30d = 1.0) AS STRING) UNION ALL
  SELECT 'score: projetos ok para a regra com risco alto ou médio', '5',
         CAST((SELECT COUNT(*) FROM s s3 JOIN p USING (projeto_id)
               WHERE p.situacao = 'ok' AND s3.faixa_risco IN ('alto', 'medio')) AS STRING) UNION ALL
  SELECT 'score: probabilidade do PRJ-024 na faixa média (0,45 a 0,50)', 'true',
         CAST((SELECT prob_estouro_30d BETWEEN 0.45 AND 0.50 FROM s WHERE projeto_id = 'PRJ-024') AS STRING) UNION ALL
  SELECT 'score: nenhum motivo vazio', '0', CAST(COUNT_IF(principais_fatores IS NULL OR principais_fatores = '') AS STRING) FROM s UNION ALL
  -- 2 · Governança Semântica (Unity Catalog Metric View)
  SELECT 'mv_projetos: SPI · CPI da carteira', '0.92 · 0.96',
         (SELECT CAST(ROUND(MEASURE(spi), 2) AS STRING) || ' · ' || CAST(ROUND(MEASURE(cpi), 2) AS STRING) FROM lakehouse_meridian.gold.mv_projetos) UNION ALL
  SELECT 'mv_projetos: estouro previsto (R$ mi)', '6.47',
         (SELECT CAST(ROUND(MEASURE(estouro_previsto) / 1e6, 2) AS STRING) FROM lakehouse_meridian.gold.mv_projetos) UNION ALL
  SELECT 'mv_projetos: em risco · críticos · melancias', '17 · 7 · 4',
         (SELECT MEASURE(projetos_em_risco) || ' · ' || MEASURE(projetos_criticos) || ' · ' || MEASURE(projetos_melancia)
          FROM lakehouse_meridian.gold.mv_projetos) UNION ALL
  -- 3 · Indicadores Operacionais do Databricks App
  SELECT 'app: alto risco em 30 dias (faixa alta)', '18', CAST(COUNT_IF(faixa_risco = 'alto') AS STRING) FROM s UNION ALL
  SELECT 'app: SREs com uso < 20% nas últimas 12 semanas', 'COL0017, COL0018',
         (SELECT array_join(sort_array(collect_list(colaborador_id)), ', ') FROM (
            SELECT colaborador_id FROM lakehouse_meridian.gold.utilizacao_pessoa_semana
            WHERE papel = 'sre' AND semana > DATE'2026-07-24'
            GROUP BY colaborador_id HAVING SUM(horas_apontadas) / SUM(horas_disponiveis) < 0.2)) UNION ALL
  SELECT 'app: dias de impacto por falta de SRE no PRJ-011 (90 dias)', '57.0',
         CAST((SELECT SUM(dias_impacto) FROM lakehouse_meridian.gold.status_estruturado
               WHERE projeto_id = 'PRJ-011' AND data_status >= DATE'2026-07-18' AND causa_bloqueio = 'falta_sre') AS STRING)
)
SELECT item, esperado, obtido, CASE WHEN esperado = obtido THEN 'ok' ELSE 'CONFIRA' END AS status FROM checagens;
