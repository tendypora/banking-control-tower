-- ============================================
-- AUDITORIA E RECUPERAÇÃO COM DELTA TIME TRAVEL
-- ============================================
-- Demonstração de governança e resiliência na camada Bronze utilizando versionamento
-- transacional do Delta Lake: DESCRIBE HISTORY, VERSION AS OF e RESTORE TABLE.
-- Cenário: carga duplicada acidental de um contrato (PRJ-021) inflando o valor da carteira,
-- seguida de auditoria do log transacional e restauração atômica da versão íntegra.

-- 1. Uma cópia do cadastro de projetos. Ela nasce na versão 0.
DROP TABLE IF EXISTS lakehouse_meridian.bronze.projetos_copia;
CREATE TABLE lakehouse_meridian.bronze.projetos_copia AS
SELECT * FROM lakehouse_meridian.bronze.projetos;

-- 2. Como está hoje: 60 projetos, carteira de R$ 305,2 mi
SELECT COUNT(*)                                                 AS projetos,
       ROUND(SUM(CAST(valor_contrato AS DECIMAL(18,2))) / 1e6, 1) AS carteira_mi
FROM lakehouse_meridian.bronze.projetos_copia;

-- 3. O erro: alguém rodou a carga do PRJ-021 duas vezes. O projeto agora aparece duplicado.
INSERT INTO lakehouse_meridian.bronze.projetos_copia
SELECT * FROM lakehouse_meridian.bronze.projetos_copia
WHERE projeto_id = 'PRJ-021';

-- 4. O estrago: 61 projetos, e a carteira "cresceu" de R$ 305,2 mi para R$ 318,8 mi sem nenhum contrato novo
SELECT COUNT(*)                                                 AS projetos,
       ROUND(SUM(CAST(valor_contrato AS DECIMAL(18,2))) / 1e6, 1) AS carteira_mi
FROM lakehouse_meridian.bronze.projetos_copia;

-- 5. O histórico: cada linha é uma versão. Versão 0 = a cópia; versão 1 = o INSERT errado.
--    Repare nas colunas operation (CREATE TABLE AS SELECT, WRITE) e operationMetrics (numOutputRows: 1).
DESCRIBE HISTORY lakehouse_meridian.bronze.projetos_copia;

-- 6. A viagem no tempo: a tabela como ela era ANTES do erro. Sem restaurar nada, só olhando.
SELECT COUNT(*)                                                 AS projetos,
       ROUND(SUM(CAST(valor_contrato AS DECIMAL(18,2))) / 1e6, 1) AS carteira_mi
FROM lakehouse_meridian.bronze.projetos_copia VERSION AS OF 0;

-- 7. Volta para a versão 0 de verdade.
RESTORE TABLE lakehouse_meridian.bronze.projetos_copia TO VERSION AS OF 0;

-- 8. Conferindo: 60 projetos de novo. E o histórico ganhou mais uma linha (RESTORE):
--    voltar no tempo também fica registrado.
SELECT COUNT(*)                                                 AS projetos,
       ROUND(SUM(CAST(valor_contrato AS DECIMAL(18,2))) / 1e6, 1) AS carteira_mi
FROM lakehouse_meridian.bronze.projetos_copia;

DESCRIBE HISTORY lakehouse_meridian.bronze.projetos_copia;

-- 9. Arrumando a casa: a cópia não faz parte da bronze. (Antes de apagar, dá uma olhada
--    na aba History dela no Catalog: é o mesmo histórico, pela interface.)
DROP TABLE lakehouse_meridian.bronze.projetos_copia;
