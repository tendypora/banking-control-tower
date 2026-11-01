-- Dataset Analítico 3 (Setor Bancário): "Risco de Crédito (PDD CMN 4.966) & Fraude Pix"
-- Cole em Dashboards → seu dashboard → aba Data → + Create from SQL.

WITH kpi_ti AS (
  SELECT projeto_id,
         ROUND(SUM(horas * pct_concluido / 100) /
               SUM(horas * GREATEST(0, LEAST(1, datediff(DATE'2026-10-16', inicio_baseline)
                        / datediff(fim_baseline, inicio_baseline)))), 2) AS spi
  FROM lakehouse_meridian.bronze.rascunho_tarefas
  GROUP BY projeto_id
),
credito_atual AS (
  SELECT projeto_id,
         modalidade_credito,
         superintendencia,
         CAST(saldo_carteira_milhoes AS DECIMAL(18,2))    AS saldo_carteira_milhoes,
         CAST(inadimplencia_over90_pct AS DECIMAL(10,2))  AS inadimplencia_over90_pct,
         estagio_cmn_4966,
         CAST(provisao_pdd_milhoes AS DECIMAL(18,2))      AS provisao_pdd_milhoes,
         CAST(indice_cobertura_pdd_pct AS DECIMAL(10,1))  AS indice_cobertura_pdd_pct
  FROM lakehouse_meridian.bronze.carteira_credito_pdd
  WHERE competencia = '2026-10'
),
fraude_recente AS (
  SELECT projeto_id,
         MAX(canal_bancario)                                             AS canal_bancario,
         ROUND(SUM(CAST(volume_transacoes_mil AS DOUBLE)), 1)            AS transacoes_mil_8s,
         ROUND(SUM(CAST(fraude_bloqueada_mil AS DOUBLE)) / 1000, 2)      AS fraude_evitada_milhoes,
         ROUND(SUM(CAST(perda_liquida_fraude_mil AS DOUBLE)) / 1000, 2)  AS perda_liquida_fraude_milhoes,
         SUM(CAST(acionamentos_med_bacen AS INT))                        AS acionamentos_med_bacen,
         ROUND(AVG(CAST(latencia_p99_ms AS DOUBLE)), 1)                  AS latencia_p99_ms,
         ROUND(MIN(CAST(disponibilidade_sla_pct AS DOUBLE)), 2)          AS pior_sla_pct
  FROM lakehouse_meridian.bronze.monitoramento_fraude_pix
  WHERE CAST(semana AS DATE) >= DATE'2026-08-21'
  GROUP BY projeto_id
)
SELECT c.projeto_id,
       p.nome_projeto,
       c.superintendencia,
       c.modalidade_credito,
       k.spi,
       c.saldo_carteira_milhoes,
       c.inadimplencia_over90_pct,
       c.estagio_cmn_4966,
       c.provisao_pdd_milhoes,
       c.indice_cobertura_pdd_pct,
       coalesce(f.canal_bancario, 'Core & Crédito')       AS canal_bancario,
       coalesce(f.fraude_evitada_milhoes, 0)              AS fraude_evitada_milhoes,
       coalesce(f.perda_liquida_fraude_milhoes, 0)        AS perda_liquida_fraude_milhoes,
       coalesce(f.acionamentos_med_bacen, 0)              AS acionamentos_med_bacen,
       coalesce(f.latencia_p99_ms, 0)                     AS latencia_p99_ms,
       coalesce(f.pior_sla_pct, 99.9)                     AS pior_sla_pct
FROM credito_atual c
JOIN lakehouse_meridian.bronze.projetos p USING (projeto_id)
LEFT JOIN kpi_ti k USING (projeto_id)
LEFT JOIN fraude_recente f USING (projeto_id)
WHERE p.status = 'em_andamento'
ORDER BY c.provisao_pdd_milhoes DESC;
