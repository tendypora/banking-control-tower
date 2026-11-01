-- Os números do topo da Torre (fotografia de 16/10/2026).
WITH score AS (   -- modelo preditivo: projetos na faixa alta de risco de estouro em 30 dias
  SELECT COUNT_IF(faixa_risco = 'alto') AS alto_risco_30d
  FROM lakehouse_meridian.gold.score_estouro_30d
  WHERE data_referencia = (SELECT MAX(data_referencia) FROM lakehouse_meridian.gold.score_estouro_30d)
)
SELECT COUNT(*)                                                    AS projetos_em_andamento,
       COUNT_IF(situacao IN ('crítico', 'atenção'))                AS projetos_em_risco,
       COUNT_IF(situacao = 'crítico')                              AS projetos_criticos,
       COUNT_IF(melancia)                                          AS projetos_melancia,
       SUM(estouro_previsto)                                       AS estouro_previsto,
       SUM(valor_contrato)                                         AS carteira,
       (SELECT alto_risco_30d FROM score)                          AS alto_risco_30d
FROM lakehouse_meridian.gold.projeto_situacao_atual
WHERE status = 'em_andamento'
