-- gold.risco_credito_e_operacional
-- Visão executiva integrada para o Comitê de Risco (CRO) e Tecnologia (CTO):
-- correlaciona o desempenho dos programas de TI bancária (SPI, CPI, EAC) com a
-- exposição de crédito, provisão PDD (Resolução CMN 4.966) e perdas por fraude Pix / MED BACEN.

CREATE OR REFRESH MATERIALIZED VIEW lakehouse_meridian.gold.risco_credito_e_operacional
COMMENT 'Visão consolidada por programa bancário unindo indicadores de engenharia (SPI, CPI, estouro previsto) com exposição da carteira de crédito (saldo, Over 90, estágio CMN 4.966, provisão PDD) e telemetria antifraude Pix (bloqueios, perdas líquidas, MED BACEN e SLA).'
AS WITH credito_atual AS (
  SELECT projeto_id,
         modalidade_credito,
         saldo_carteira_milhoes,
         inadimplencia_over90_pct,
         estagio_cmn_4966,
         provisao_pdd_milhoes,
         indice_cobertura_pdd_pct
  FROM carteira_credito_pdd
  WHERE competencia = '2026-10'
),
fraude_8s AS (
  SELECT projeto_id,
         MAX(canal_bancario)                                        AS canal_bancario,
         ROUND(SUM(volume_transacoes_mil), 1)                       AS transacoes_mil_8s,
         ROUND(SUM(fraude_bloqueada_mil) / 1000, 2)                 AS fraude_evitada_milhoes_8s,
         ROUND(SUM(perda_liquida_fraude_mil) / 1000, 2)             AS perda_liquida_fraude_milhoes_8s,
         SUM(acionamentos_med_bacen)                                AS total_med_bacen_8s,
         ROUND(AVG(latencia_p99_ms), 1)                             AS latencia_media_p99_ms,
         ROUND(MIN(disponibilidade_sla_pct), 2)                     AS pior_sla_semanal_pct
  FROM monitoramento_fraude_pix
  WHERE semana >= DATE'2026-08-21'
  GROUP BY projeto_id
)
SELECT p.projeto_id,
       p.projeto,
       p.cliente                                                    AS superintendencia,
       p.segmento,
       p.tipo_projeto,
       p.ferramenta,
       p.status,
       p.spi,
       p.cpi,
       p.situacao,
       p.estouro_previsto,
       p.melancia,
       c.modalidade_credito,
       c.saldo_carteira_milhoes,
       c.inadimplencia_over90_pct,
       c.estagio_cmn_4966,
       c.provisao_pdd_milhoes,
       c.indice_cobertura_pdd_pct,
       f.canal_bancario,
       f.transacoes_mil_8s,
       f.fraude_evitada_milhoes_8s,
       f.perda_liquida_fraude_milhoes_8s,
       f.total_med_bacen_8s,
       f.latencia_media_p99_ms,
       f.pior_sla_semanal_pct
FROM lakehouse_meridian.gold.projeto_situacao_atual p
LEFT JOIN credito_atual c USING (projeto_id)
LEFT JOIN fraude_8s f USING (projeto_id);
