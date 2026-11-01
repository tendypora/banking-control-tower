# Meridian Bank Control Tower · Aplicação Web (Databricks Apps + Lakebase)

Aplicação Full-Stack (**React + TypeScript + Express + Lakebase PostgreSQL**) construída sobre o **Databricks AppKit** para governança de programas bancários, simulação de realocação de especialistas (SRE / Segurança / Risco), consulta conversacional via Genie e trilha de auditoria de decisões executivas no **Lakebase**.

```text
app/
├── config/queries/                   Consultas parametrizadas no SQL Warehouse (tipadas via typegen)
│   ├── kpis.sql · projetos_risco.sql · pessoas_ociosas.sql
├── server/
│   ├── server.ts                     Configuração dos plugins analytics, genie, lakebase e rotas REST
│   ├── routes/score.ts               Integração com o score preditivo (gold.score_estouro_30d)
│   ├── routes/decisoes.ts            Persistência transacional no Lakebase Postgres (schema torre.decisoes)
│   └── decisoes.test.ts              Testes automatizados de contrato e validação (Vitest + Zod)
├── client/src/pages/                 Interfaces: Programas em Risco · Simulador · Decisões · Assistente Genie
├── scripts/
│   ├── conceder-acesso.sh            Concessão de privilégios (GRANTs) no Unity Catalog ao Service Principal
│   ├── subir-tudo.sh                 Provisionamento automatizado (Lakebase + Genie Space ID + App Deploy)
│   └── ver_decisoes.py               Auditoria direta dos registros persistidos no PostgreSQL Serverless
├── databricks.yml                    Definição do Databricks Asset Bundle da aplicação
└── app.yaml                          Especificação de runtime e variáveis de ambiente do Databricks App
```

## Deploy Automatizado

```bash
databricks apps list --profile meridian
bash app/scripts/subir-tudo.sh meridian
```

## Desenvolvimento e Testes Locais

```bash
cd app
npm test
databricks apps validate --profile meridian
databricks apps deploy   --profile meridian
```
