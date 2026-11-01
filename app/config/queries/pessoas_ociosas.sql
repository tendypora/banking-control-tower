-- Gente parada nas últimas 12 semanas (até 16/10/2026): utilização abaixo de 20%.
-- horas_paradas_semana e custo_ocioso_semana são MÉDIAS por semana: é o que deixa
-- de ser desperdiçado em cada semana em que a pessoa trabalha num projeto que precisa dela.
SELECT colaborador_id, nome, papel, senioridade,
       projeto_id AS projeto_origem, projeto AS projeto_origem_nome,
       ROUND(SUM(horas_apontadas) / SUM(horas_disponiveis), 3)            AS utilizacao_media,
       ROUND(SUM(horas_ociosas) / COUNT(DISTINCT semana), 1)              AS horas_paradas_semana,
       ROUND(SUM(custo_ocioso) / COUNT(DISTINCT semana), 2)               AS custo_ocioso_semana,
       MAX(custo_hora)                                                    AS custo_hora
FROM lakehouse_meridian.gold.utilizacao_pessoa_semana
WHERE semana > DATE'2026-07-24'
GROUP BY colaborador_id, nome, papel, senioridade, projeto_id, projeto
HAVING SUM(horas_apontadas) / SUM(horas_disponiveis) < 0.2
ORDER BY utilizacao_media
