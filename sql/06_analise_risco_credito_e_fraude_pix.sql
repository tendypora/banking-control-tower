-- ==============================================================================
-- ANÁLISE INTEGRADA: RISCO DE CRÉDITO (PDD / CMN 4.966), FRAUDE PIX E ATRASO DE TI
-- ==============================================================================
-- Cruzamento entre o desempenho das squads de tecnologia bancária (SPI e CPI)
-- e os indicadores operacionais do banco:
--   1. Carteira de Crédito, Inadimplência Over 90 e Provisão PDD (Resolução CMN 4.966 / IFRS 9)
--   2. Monitoramento de Fraudes em Pagamentos Instantâneos (Pix), Acionamentos de MED (BACEN) e SLA

-- 1. Visão Consolidada da Carteira de Crédito e Provisão PDD por Modalidade (Outubro/2026)
SELECT modalidade_credito,
       superintendencia,
       COUNT(DISTINCT projeto_id)                                              AS programas_vinculados,
       ROUND(SUM(CAST(saldo_carteira_milhoes AS DECIMAL(18,2))), 2)            AS saldo_total_carteira_mi,
       ROUND(AVG(CAST(inadimplencia_over90_pct AS DECIMAL(10,2))), 2)          AS inadimplencia_media_over90_pct,
       ROUND(SUM(CAST(provisao_pdd_milhoes AS DECIMAL(18,2))), 2)              AS provisao_pdd_total_mi,
       ROUND(SUM(CAST(provisao_pdd_milhoes AS DECIMAL(18,2))) /
             SUM(CAST(saldo_carteira_milhoes AS DECIMAL(18,2))) * 100, 2)      AS indice_pdd_sobre_carteira_pct
FROM lakehouse_meridian.bronze.carteira_credito_pdd
WHERE competencia = '2026-10'
GROUP BY modalidade_credito, superintendencia
ORDER BY provisao_pdd_total_mi DESC;

-- 2. Distribuição por Estágio de Risco de Crédito (Resolução CMN 4.966 / IFRS 9)
SELECT estagio_cmn_4966,
       COUNT(*)                                                                AS carteiras_avaliadas,
       ROUND(SUM(CAST(saldo_carteira_milhoes AS DECIMAL(18,2))), 2)            AS exposicao_milhoes,
       ROUND(SUM(CAST(provisao_pdd_milhoes AS DECIMAL(18,2))), 2)              AS pdd_constituida_milhoes,
       ROUND(AVG(CAST(inadimplencia_over90_pct AS DECIMAL(10,2))), 2)          AS over90_medio_pct
FROM lakehouse_meridian.bronze.carteira_credito_pdd
WHERE competencia = '2026-10'
GROUP BY estagio_cmn_4966
ORDER BY estagio_cmn_4966;

-- 3. Impacto do Atraso de Projetos de TI Bancária (SPI/CPI) na Degradação de Fraude Pix e SLA
WITH kpi_ti AS (
    SELECT projeto_id,
           ROUND(SUM(horas * pct_concluido / 100) /
                 SUM(horas * GREATEST(0, LEAST(1, datediff(DATE'2026-10-16', inicio_baseline) /
                                                  datediff(fim_baseline, inicio_baseline)))), 2) AS spi
    FROM lakehouse_meridian.bronze.rascunho_tarefas
    GROUP BY projeto_id
),
telemetria_recente AS (
    SELECT projeto_id,
           canal_bancario,
           superintendencia,
           ROUND(SUM(CAST(volume_transacoes_mil AS DOUBLE)), 1)          AS transacoes_mil_8sem,
           ROUND(SUM(CAST(fraude_bloqueada_mil AS DOUBLE)) / 1000, 2)    AS fraude_evitada_milhoes,
           ROUND(SUM(CAST(perda_liquida_fraude_mil AS DOUBLE)) / 1000, 2) AS perda_liquida_fraude_milhoes,
           SUM(CAST(acionamentos_med_bacen AS INT))                      AS total_med_bacen,
           ROUND(AVG(CAST(latencia_p99_ms AS DOUBLE)), 1)                AS latencia_media_p99_ms,
           ROUND(MIN(CAST(disponibilidade_sla_pct AS DOUBLE)), 2)        AS pior_sla_semanal_pct
    FROM lakehouse_meridian.bronze.monitoramento_fraude_pix
    WHERE CAST(semana AS DATE) >= DATE'2026-08-21'
    GROUP BY projeto_id, canal_bancario, superintendencia
)
SELECT p.projeto_id,
       p.nome_projeto,
       t.canal_bancario,
       k.spi                                                             AS spi_cronograma,
       t.latencia_media_p99_ms,
       t.pior_sla_semanal_pct,
       t.fraude_evitada_milhoes,
       t.perda_liquida_fraude_milhoes,
       t.total_med_bacen
FROM telemetria_recente t
JOIN lakehouse_meridian.bronze.projetos p USING (projeto_id)
JOIN kpi_ti k USING (projeto_id)
WHERE p.status = 'em_andamento'
ORDER BY t.perda_liquida_fraude_milhoes DESC, k.spi ASC;
