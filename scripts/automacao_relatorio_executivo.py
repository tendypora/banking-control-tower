#!/usr/bin/env python3
"""Automação Bancária de Análise de Dados e Relatórios Executivos (Excel & PDF).

Uso:
    python scripts/automacao_relatorio_executivo.py

Este script demonstra a automação ponta a ponta de um fluxo analítico bancário em Python:
  1. Garante a geração das 11 fontes bancárias (Excel, ClickUp JSON, MS Project XML,
     Carteira de Crédito/PDD Resolução CMN 4.966 e Monitoramento de Fraude Pix / MED BACEN).
  2. Unifica e limpa automaticamente os cronogramas das 3 ferramentas e consolida os indicadores
     de Risco de Crédito (Inadimplência Over 90, Provisão PDD Stages 1-3) e Fraude Pix.
  3. Exporta automaticamente dois entregáveis para o Comitê Executivo e de Risco (CTO / CRO):
     - Planilha Gerencial de Portfólio e Risco em Excel (.xlsx)
     - Relatório Executivo para Comitê do Banco em PDF (.pdf)
"""
from __future__ import annotations

import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "data_generator"))

import gerar_dataset  # noqa: E402
import validar_padroes  # noqa: E402
from pdf_simples import escrever_pdf  # noqa: E402
from xlsx_simples import escrever_xlsx  # noqa: E402


def executar_automacao(pasta_dados: pathlib.Path, pasta_saida: pathlib.Path) -> dict:
    if not (pasta_dados / "operacoes_bancarias" / "carteira_credito_pdd.csv").exists():
        gerar_dataset.gerar(pasta_dados, seed=42)

    proj = {p["projeto_id"]: p for p in validar_padroes.ler(pasta_dados, "pmo/projetos.csv")}
    tarefas = validar_padroes.centralizar(pasta_dados, proj)

    custos_por_proj: dict[str, float] = {}
    for c in validar_padroes.ler(pasta_dados, "financeiro/custos.csv"):
        if validar_padroes.data(c["data"]) <= validar_padroes.HOJE:
            pid = c["projeto_id"]
            custos_por_proj[pid] = custos_por_proj.get(pid, 0.0) + float(c["valor"].replace(",", "."))

    farol_atual: dict[str, str] = {}
    for s in validar_padroes.ler(pasta_dados, "pmo/status_semanal.csv"):
        if s["data_status"] == "2026-10-16":
            farol_atual[s["projeto_id"]] = s["farol"].lower()

    credito_out: dict[str, dict] = {}
    for c in validar_padroes.ler(pasta_dados, "operacoes_bancarias/carteira_credito_pdd.csv"):
        if c["competencia"] == "2026-10":
            credito_out[c["projeto_id"]] = c

    perda_pix_por_proj: dict[str, float] = {}
    med_por_proj: dict[str, int] = {}
    for f in validar_padroes.ler(pasta_dados, "operacoes_bancarias/monitoramento_fraude_pix.csv"):
        pid = f["projeto_id"]
        perda_pix_por_proj[pid] = perda_pix_por_proj.get(pid, 0.0) + float(f["perda_liquida_fraude_mil"]) / 1000.0
        med_por_proj[pid] = med_por_proj.get(pid, 0) + int(f["acionamentos_med_bacen"])

    linhas_excel = [[
        "ID Programa", "Programa Bancário", "Superintendência", "Ferramenta",
        "SPI (Prazo)", "CPI (Custo)", "Farol Comitê", "Situação Real", "Melancia?",
        "Estouro TI (R$)", "Saldo Carteira (R$ mi)", "Over 90 (%)", "Estágio CMN 4.966",
        "Provisão PDD (R$ mi)", "Perda Fraude Pix (R$ mi)", "Acionamentos MED BACEN"
    ]]

    ativos = []
    estouro_total = 0.0
    pdd_total_mi = 0.0
    criticos, atencao, melancias = 0, 0, []

    for pid, p in sorted(proj.items()):
        if p["status"] != "em_andamento":
            continue
        ts = tarefas[pid]
        h_tot = sum(t["horas"] for t in ts)
        h_ag = sum(t["horas"] * t["pct"] / 100.0 for t in ts)
        h_pl = sum(
            t["horas"] * max(0.0, min(1.0, (validar_padroes.HOJE - t["ini_b"]).days / max(1, (t["fim_b"] - t["ini_b"]).days)))
            for t in ts
        )
        orc = float(p["orcamento_custo"])
        ac = custos_por_proj.get(pid, 0.0)
        ev = orc * (h_ag / h_tot)
        spi = round(h_ag / h_pl, 2) if h_pl else 1.0
        cpi = round(ev / ac, 2) if ac else 1.0
        eac = round(orc / (ev / ac), 2) if ev > 0 and ac > 0 else orc
        estouro = max(0.0, round(eac - orc, 2))
        estouro_total += estouro

        menor = min(h_ag / h_pl, ev / ac)
        situacao = "CRÍTICO" if menor < 0.8 else ("ATENÇÃO" if menor < 0.9 else "OK")
        if situacao == "CRÍTICO":
            criticos += 1
        elif situacao == "ATENÇÃO":
            atencao += 1

        farol = farol_atual.get(pid, "verde")
        eh_melancia = farol == "verde" and (h_ag / h_pl) < 0.9
        if eh_melancia:
            melancias.append(pid)

        cred = credito_out.get(pid, {})
        saldo_mi = float(cred.get("saldo_carteira_milhoes", 0.0))
        over90 = float(cred.get("inadimplencia_over90_pct", 0.0))
        estagio = cred.get("estagio_cmn_4966", "Stage 1 - Risco Normal")
        pdd_mi = float(cred.get("provisao_pdd_milhoes", 0.0))
        pdd_total_mi += pdd_mi
        perda_pix = round(perda_pix_por_proj.get(pid, 0.0), 2)
        meds = med_por_proj.get(pid, 0)

        ativos.append((menor, pid, p["nome_projeto"], p["cliente"], spi, cpi, farol, situacao, estouro, pdd_mi, over90, estagio))
        linhas_excel.append([
            pid, p["nome_projeto"], p["cliente"], p["ferramenta"],
            spi, cpi, farol.upper(), situacao, "SIM" if eh_melancia else "NÃO",
            estouro, saldo_mi, over90, estagio, pdd_mi, perda_pix, meds
        ])

    ativos.sort(key=lambda x: x[0])
    pasta_saida.mkdir(parents=True, exist_ok=True)
    caminho_xlsx = pasta_saida / "relatorio_executivo_bancario.xlsx"
    escrever_xlsx(caminho_xlsx, linhas_excel)

    blocos_pdf = [
        ("titulo", "Meridian Bank S.A. - Relatorio Executivo de TI, Risco de Credito (PDD) e Pix"),
        ("subtitulo", "Data-base: 16/10/2026 | Automacao em Python para Comite de Risco (CRO) e Tecnologia (CTO)"),
        ("espaco", ""),
        ("subtitulo", "1. INDICADORES CONSOLIDADOS DO PORTFOLIO BANCARIO"),
        ("normal", f"Programas estrategicos em andamento: {len(ativos)} (Excel, ClickUp e MS Project)."),
        ("normal", f"Programas CRITICOS (SPI ou CPI < 0,80): {criticos} | Em ATENCAO (< 0,90): {atencao}."),
        ("normal", f"Estouro orcamentario projetado em TI Bancaria (EAC - Orcamento): R$ {estouro_total / 1e6:.2f} milhoes."),
        ("normal", f"Provisao PDD total constituida nas carteiras ativas (Res. CMN 4.966): R$ {pdd_total_mi:,.2f} milhoes."),
        ("normal", f"Programas 'Melancia' (Farol Verde no Comite com SPI < 0,90): {len(melancias)} ({', '.join(melancias)})."),
        ("espaco", ""),
        ("subtitulo", "2. TOP 10 PROGRAMAS CRITICOS E EXPOSICAO DE CREDITO / PDD"),
    ]
    for _, pid, nome, sup, spi, cpi, farol, sit, est, pdd_mi, over90, estagio in ativos[:10]:
        blocos_pdf.append((
            "normal",
            f"{pid} ({sup}) | SPI: {spi:.2f} | CPI: {cpi:.2f} | Over90: {over90:.1f}% | PDD: R$ {pdd_mi:.1f} mi ({estagio[:7]})"
        ))

    caminho_pdf = pasta_saida / "relatorio_comite_risco_e_ti.pdf"
    escrever_pdf(caminho_pdf, blocos_pdf)
    return {
        "programas_ativos": len(ativos),
        "criticos": criticos,
        "atencao": atencao,
        "melancias": len(melancias),
        "estouro_ti_milhoes": round(estouro_total / 1e6, 2),
        "provisao_pdd_milhoes": round(pdd_total_mi, 2),
        "xlsx": str(caminho_xlsx),
        "pdf": str(caminho_pdf),
    }


if __name__ == "__main__":
    res = executar_automacao(RAIZ / "dados", RAIZ / "relatorios_automatizados")
    print("Automação bancária concluída com sucesso!")
    for k, v in res.items():
        print(f"  {k:<22}: {v}")
