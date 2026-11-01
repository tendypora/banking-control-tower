#!/usr/bin/env python3
"""Gera o dataset corporativo simulado do Meridian Bank S.A. (Torre de Controle Bancária).

Uso:
    python3 data_generator/gerar_dataset.py --saida ./dados --seed 42

Utiliza apenas biblioteca padrão do Python com seed determinística (42) para
reprodutibilidade completa dos arquivos e indicadores analíticos.

Cenário Bancário (TI Bancária + Risco de Crédito/PDD + Prevenção a Fraudes Pix):
O Meridian Bank S.A. gerencia 60 programas estratégicos de tecnologia e operações
bancárias com 520 especialistas (Engenharia Core Bancário, Risco de Crédito,
Prevenção a Fraudes/PLD, Open Finance e Meios de Pagamento). Os cronogramas das
squads estão descentralizados em 20 planilhas Excel, 25 listas no ClickUp e
15 cronogramas no MS Project, além das bases operacionais de Carteira de Crédito
(Inadimplência Over 90 e Provisão PDD - Resolução CMN 4.966) e Monitoramento
Transacional de Fraudes Pix/MED BACEN.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import pathlib
import random
import shutil
import sys
import unicodedata

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pdf_simples import escrever_pdf  # noqa: E402
from xlsx_simples import escrever_xlsx, serial_excel  # noqa: E402

HOJE = dt.date(2026, 10, 16)          # o "hoje" do dataset (sexta-feira)
N_PROJETOS = 60
N_COLABORADORES = 520
CUSTO_HORA_REF = 150.0                 # R$/h usado para converter orçamento em horas planejadas

CPI_CAINDO = ["PRJ-002", "PRJ-005", "PRJ-009", "PRJ-014", "PRJ-018", "PRJ-021", "PRJ-027", "PRJ-033"]
ECOMMERCE_FREEZE = ["PRJ-003", "PRJ-011", "PRJ-024"]
SQUAD_ROTATIVIDADE = ["PRJ-016", "PRJ-030"]
PROJETO_SRE_OCIOSO = "PRJ-007"         # ainda no discovery, não precisa de SRE
PROJETO_SEM_SRE = "PRJ-011"            # em implantação, reclama de falta de SRE
SRES_OCIOSOS = ["COL0017", "COL0018"]
TROCA_SRE = HOJE - dt.timedelta(weeks=12)          # sexta em que os SREs saíram do PRJ-011
FREEZE_2025 = (dt.date(2025, 11, 1), dt.date(2026, 1, 10))
FREEZE_2026 = (dt.date(2026, 11, 1), dt.date(2027, 1, 10))
CONSULTORIA_ATRASADA = "CodeForge Consultoria Ltda"
GRAFIAS_CODEFORGE = [CONSULTORIA_ATRASADA, "Codeforge Consultoria", "CODEFORGE CONSULTORIA LTDA", "Code Forge Consultoria"]
FERRAMENTAS = {"excel": 20, "clickup": 25, "msproject": 15}
PASTAS_GERADAS = ["pmo", "excel", "clickup", "msproject", "rh", "timesheet", "financeiro", "compras",
                  "documentos", "operacoes_bancarias"]

# ---------------------------------------------------------------- cadastros bancários

CLIENTES = {
    "varejo": ["Diretoria de Cartões & Adquirência", "Superintendência Pix & Pagamentos", "Diretoria de Crédito PF & CDC",
               "Superintendência de Canais Digitais", "Diretoria de Empréstimo Consignado"],
    "financeiro": ["Diretoria de Risco de Crédito (CRO)", "Superintendência de Tesouraria & ALM", "Diretoria de Crédito Imobiliário",
                   "Superintendência de Open Finance", "Diretoria de Atacado & Corporate PJ"],
    "saude": ["Superintendência de Prevenção a Fraudes", "Diretoria de Segurança Cibernética", "Superintendência de PLD/FT & KYC"],
    "logistica": ["Diretoria de Operações & Liquidação SPI", "Superintendência de Cobrança & Recuperação", "Diretoria de Atendimento & CRM Bancário"],
    "industria": ["Superintendência de Compliance BACEN", "Diretoria de Core Bancário & Mainframe", "Superintendência de Basileia & PDD (IFRS 9)"],
}
TIPOS_PROJETO = {
    "varejo": ["Motor de Limite Dinâmico de Cartões", "Onboarding Digital com Biometria Facial", "Migração do Core de Consignado para Cloud",
               "Plataforma de Renegociação de Dívidas PF", "Scoring de Crédito Instantâneo Varejo"],
    "financeiro": ["Core Bancário - Módulo de Crédito PJ", "Plataforma de Investimentos & Renda Fixa", "Barramento de APIs Open Finance Fase 4",
                   "Motor de Cálculo de PDD (Res. CMN 4.966)", "Descomissionamento de Alta Plataforma Mainframe"],
    "saude": ["Motor Antifraude Pix em Tempo Real", "Monitoramento de PLD/FT e Alertas COAF", "Detecção de Conta Laranja e Golpe do MED",
              "Autenticação Biométrica e Tokenização"],
    "logistica": ["Liquidação Intradia SPI / Banco Central", "Régua Digital de Cobrança Preditiva", "Conciliação Automática de Boletos e Arranjos",
                  "Portal de Crédito com Garantia e Recebíveis"],
    "industria": ["Adequação Regulatória Basileia III / BACEN", "Modernização do Sistema de Informes (SCR/CADOC)", "Data Lakehouse de Risco e Capital",
                  "Modelagem Preditiva de Inadimplência (PD/LGD)"],
}
TIPOS_ECOMMERCE = ["Motor de Liquidação Pix Instantâneo (SPI)", "Autorizador de Cartões Alta Disponibilidade", "Gateway de Checkout e Pix Automático"]
NOMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fábio", "Gabriela", "Henrique", "Isabela", "João",
         "Karina", "Leonardo", "Marina", "Nelson", "Olívia", "Paulo", "Renata", "Sérgio", "Tatiana", "Vítor",
         "Amanda", "Caio", "Débora", "Felipe", "Juliana", "Lucas", "Patrícia", "Rafael", "Sabrina", "Thiago"]
SOBRENOMES = ["Almeida", "Barros", "Cardoso", "Duarte", "Esteves", "Ferraz", "Gomes", "Lacerda", "Moura",
              "Nogueira", "Pacheco", "Queiroz", "Rezende", "Siqueira", "Teixeira", "Vasconcelos", "Monteiro",
              "Ribeiro", "Santana", "Xavier"]

# fase: (fração de início, fração de fim) do prazo baseline, peso no orçamento
FASES = {
    "discovery": (0.00, 0.14, 0.06),
    "arquitetura": (0.06, 0.28, 0.08),
    "desenvolvimento": (0.15, 0.80, 0.45),
    "integracao": (0.40, 0.86, 0.15),
    "testes": (0.50, 0.93, 0.14),
    "implantacao": (0.84, 1.00, 0.12),
}
ATIVIDADES = {
    "discovery": ["Mapeamento de normas do Banco Central (BACEN)", "Workshop com Superintendência de Risco", "Levantamento de regras de crédito e PDD",
                  "Definição de escopo regulatório e SLA", "Análise de impacto em segurança e LGPD"],
    "arquitetura": ["Desenho da arquitetura no Core Bancário", "Modelagem de dados de crédito e garantias", "Prova de conceito de baixa latência (SPI)",
                    "Arquitetura de integração Open Finance", "Revisão de segurança cibernética e criptografia"],
    "desenvolvimento": ["API de concessão e motor de crédito", "Fluxo de autenticação e token de segurança", "Módulo de liquidação Pix e MED",
                        "Serviço de mensageria ISO 20022", "Backoffice de mesa de crédito e fraude", "Relatórios regulatórios CADOC e SCR",
                        "Consulta a bureaus de crédito e KYC", "Cálculo de provisão PDD (Stage 1, 2 e 3)", "Motor de regras antifraude em tempo real",
                        "Cadastro positivo e dossiê de clientes", "Painel gerencial de inadimplência Over 90", "Integração de identidade e biometria"],
    "integracao": ["Integração com legado Mainframe / COBOL", "Conectividade com RSFN / SPI Banco Central", "Integração com Bureaus de Crédito (Serasa/SCR)",
                   "Mensageria Kafka entre Core e Canais", "Carga histórica da carteira de crédito", "Integração com processadora de cartões"],
    "testes": ["Testes integrados de liquidação financeira", "Teste de estresse de TPS (Pix / Black Friday)", "Homologação com áreas de Risco e Compliance",
               "Testes de regressão contábil e PDD", "Pentest e auditoria de segurança bancária", "Saneamento de apontamentos de auditoria"],
    "implantacao": ["Esteira de deploy seguro em produção", "Plano de cutover e janela do BACEN", "Migração de saldos e contratos ativos",
                    "Capacitação de agências e mesa de operações", "Go-live assistido em produção", "Monitoramento pós-implantação (Hypercare)"],
}
# papel: (custo/hora R$ faixa)
PAPEIS = {
    "tech_lead": (150, 210), "product_owner": (120, 170), "qa": (80, 120), "sre": (140, 200),
    "dev_backend": (90, 160), "dev_frontend": (85, 150), "dev_mobile": (90, 155), "designer_ux": (85, 130),
    "engenheiro_dados": (100, 165), "arquiteto": (170, 230), "agilista": (100, 140), "gestor_engenharia": (190, 260),
}
PAPEIS_DEV = ("dev_backend", "dev_frontend", "dev_mobile", "engenheiro_dados", "qa")
# fornecedor: (fase em que entrega, prazo contratado em dias, serviço)
FORNECEDORES = {
    CONSULTORIA_ATRASADA: ("desenvolvimento", 30, "Sprint"),
    "Pixel Design Studio": ("arquitetura", 20, "Pacote de telas"),
    "QualiTest Brasil": ("testes", 20, "Ciclo de testes"),
    "SecureOps Segurança": ("testes", 25, "Pentest"),
    "DataPrime Analytics": ("integracao", 30, "Lote de integração"),
}
NUVEM = "NuvemSul Cloud"


# ----------------------------------------------------------------- utilidades

def sextas(inicio: dt.date, fim: dt.date) -> list[dt.date]:
    d = inicio + dt.timedelta(days=(4 - inicio.weekday()) % 7)
    out = []
    while d <= fim:
        out.append(d)
        d += dt.timedelta(days=7)
    return out


def iso(d: dt.date | None) -> str:
    return d.isoformat() if d else ""


def br(d: dt.date) -> str:
    return d.strftime("%d/%m/%Y")


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def ms(d: dt.date) -> str:
    """Data como o ClickUp devolve: milissegundos desde 1970, em texto (meio-dia UTC)."""
    return str(int(dt.datetime(d.year, d.month, d.day, 12, tzinfo=dt.timezone.utc).timestamp() * 1000))


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "".join(c if c.isalnum() else "_" for c in t).strip("_").lower()


def em_freeze(d: dt.date) -> bool:
    return FREEZE_2025[0] <= d <= FREEZE_2025[1] + dt.timedelta(days=6)


def fim_de_ano(d: dt.date) -> bool:
    return (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 6)


def escrever_csv(caminho: pathlib.Path, cabecalho: list[str], linhas: list[list]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cabecalho)
        w.writerows(linhas)


def pessoa(rng: random.Random) -> str:
    return f"{rng.choice(NOMES)} {rng.choice(SOBRENOMES)}"


# ----------------------------------------------------------------- projetos

def gerar_projetos(rng: random.Random) -> list[dict]:
    segmentos = ["varejo"] * 15 + ["financeiro"] * 17 + ["saude"] * 9 + ["logistica"] * 9 + ["industria"] * 10
    rng.shuffle(segmentos)
    ferramentas = [f for f, n in FERRAMENTAS.items() for _ in range(n)]
    rng.shuffle(ferramentas)
    # quem precisa estar em qual ferramenta (a história atravessa as três)
    fixas = {"PRJ-011": "excel", "PRJ-007": "msproject", "PRJ-003": "clickup", "PRJ-024": "msproject",
             "PRJ-016": "clickup", "PRJ-030": "excel"}
    for pid, f in fixas.items():
        i = int(pid[4:]) - 1
        if ferramentas[i] != f:
            j = next(k for k, g in enumerate(ferramentas)
                     if g == f and f"PRJ-{k + 1:03d}" not in fixas)
            ferramentas[i], ferramentas[j] = ferramentas[j], ferramentas[i]
    projetos, usados = [], set()
    for i in range(N_PROJETOS):
        pid = f"PRJ-{i + 1:03d}"
        seg = "varejo" if pid in ECOMMERCE_FREEZE else segmentos[i]
        if pid in ECOMMERCE_FREEZE:
            tipo = TIPOS_ECOMMERCE[ECOMMERCE_FREEZE.index(pid)]
        else:
            tipo = rng.choice(TIPOS_PROJETO[seg])
        cliente = rng.choice(CLIENTES[seg])
        nome = f"{tipo} - {cliente}"
        while nome in usados:
            cliente = rng.choice(CLIENTES[seg])
            tipo = rng.choice(TIPOS_PROJETO[seg])
            nome = f"{tipo} - {cliente}"
        usados.add(nome)
        if pid in CPI_CAINDO:
            inicio = dt.date(2024, 12, 2) + dt.timedelta(days=rng.randint(0, 180))
            meses = rng.randint(18, 22)
        elif pid in ECOMMERCE_FREEZE:
            inicio = dt.date(2025, 3, 3) + dt.timedelta(days=rng.randint(0, 120))
            meses = rng.randint(16, 19)
        elif pid == PROJETO_SRE_OCIOSO:
            inicio, meses = dt.date(2026, 5, 4), 14
        elif pid == PROJETO_SEM_SRE:
            inicio, meses = dt.date(2025, 4, 7), 17
        elif pid in SQUAD_ROTATIVIDADE:
            inicio = dt.date(2025, 5, 5) + dt.timedelta(days=rng.randint(0, 60))
            meses = rng.randint(16, 18)
        else:
            inicio = dt.date(2024, 12, 2) + dt.timedelta(days=rng.randint(0, 500))
            meses = rng.randint(10, 22)
        duracao = int(meses * 30.4)
        valor = round(rng.lognormvariate(math.log(4.6e6), 0.5) / 1000) * 1000
        valor = clamp(valor, 1.2e6, 18e6)
        orcamento = round(valor * rng.uniform(0.72, 0.82), 2)
        if pid in CPI_CAINDO:
            vel = rng.uniform(0.95, 1.02)
        elif pid in SQUAD_ROTATIVIDADE:
            vel = rng.uniform(0.78, 0.84)
        elif pid == PROJETO_SEM_SRE:
            vel = rng.uniform(0.86, 0.90)
        else:
            vel = rng.uniform(0.84, 1.04)
        projetos.append(dict(
            id=pid, segmento=seg, tipo=tipo, cliente=cliente, nome=nome, ferramenta=ferramentas[i],
            valor=valor, orcamento=orcamento, inicio=inicio, duracao=duracao,
            fim_baseline=inicio + dt.timedelta(days=duracao), vel=vel,
            custo_base=rng.uniform(0.96, 1.035), gerente=pessoa(rng),
        ))
    return projetos


def gerar_tarefas(projetos: list[dict], rng: random.Random) -> dict[str, list[dict]]:
    pesos = [(f, v[2]) for f, v in FASES.items()]
    soma_pesos = sum(v[2] for v in FASES.values())
    tarefas = {}
    for p in projetos:
        brutos = []
        for _ in range(rng.randint(60, 110)):
            fase = rng.choices([f for f, _ in pesos], [w for _, w in pesos])[0]
            ini_f, fim_f, _ = FASES[fase]
            a = rng.uniform(ini_f, fim_f - 0.04)
            dur = clamp(rng.uniform(0.04, 0.18), 0.03, fim_f - a)
            brutos.append((fase, a, dur, rng.lognormvariate(0, 0.6)))
        brutos.sort(key=lambda x: (x[1], x[0]))
        soma_fase = {}
        for fase, _, _, w in brutos:
            soma_fase[fase] = soma_fase.get(fase, 0) + w
        lista = []
        for n, (fase, a, dur, w) in enumerate(brutos, 1):
            vp = p["orcamento"] * FASES[fase][2] / soma_pesos * w / soma_fase[fase]
            horas = max(8, round(vp / CUSTO_HORA_REF))
            lista.append(dict(
                n=n, fase=fase, atividade=rng.choice(ATIVIDADES[fase]),
                a=a * p["duracao"], L=max(7.0, dur * p["duracao"]),
                u=rng.uniform(0.92, 1.12), horas=horas,
                ini_real=None, fim_real=None, pct=0.0,
            ))
        tot = sum(t["horas"] for t in lista)
        for t in lista:                 # valor planejado proporcional às horas previstas no baseline
            t["vp"] = p["orcamento"] * t["horas"] / tot
        tarefas[p["id"]] = lista
    return tarefas


def simular(projetos: list[dict], tarefas: dict, rng: random.Random) -> dict[str, list[dict]]:
    """Avanço semanal: um relógio `tau` anda com a velocidade da semana; cada tarefa avança com ele."""
    hist = {}
    for p in projetos:
        pid = p["id"]
        tau = 0.0
        semanas = []
        concluido = None
        for sexta in sextas(p["inicio"], HOJE):
            segunda = sexta - dt.timedelta(days=4)
            dias_semana = len([d for d in range(5) if segunda + dt.timedelta(days=d) >= p["inicio"]])
            vel = p["vel"] * rng.gauss(1, 0.06)
            freeze = pid in ECOMMERCE_FREEZE and em_freeze(sexta)
            if freeze:
                vel *= 0.30
            if fim_de_ano(sexta):
                vel *= 0.55
            sem_sre = pid == PROJETO_SEM_SRE and sexta > TROCA_SRE
            if sem_sre:
                vel *= 0.62
            if pid in SQUAD_ROTATIVIDADE and sexta > HOJE - dt.timedelta(days=270):
                vel *= 0.85                                  # gente saindo e gente nova chegando
            vel = clamp(vel, 0.10, 1.25)
            tau += 7 * vel * (dias_semana / 5)
            dia_proj = (sexta - p["inicio"]).days
            ev = pv = 0.0
            ev_fase = {}
            for t in tarefas[pid]:
                pct = clamp((tau - t["a"]) / (t["L"] * t["u"]), 0.0, 1.0)
                if pct > 0 and t["ini_real"] is None:
                    t["ini_real"] = segunda + dt.timedelta(days=rng.randint(0, 4))
                if pct >= 1 and t["fim_real"] is None:
                    t["fim_real"] = sexta - dt.timedelta(days=rng.randint(0, 2))
                t["pct"] = pct
                ev += t["vp"] * pct
                pv += t["vp"] * clamp((dia_proj - t["a"]) / t["L"], 0.0, 1.0)
                ev_fase[t["fase"]] = ev_fase.get(t["fase"], 0) + t["vp"] * pct
            mes = dia_proj / 30.4
            fator = p["custo_base"] * rng.gauss(1, 0.025)
            if pid in CPI_CAINDO and mes >= 6:
                fator += min(0.40, 0.034 * (mes - 6 + 1))
            semanas.append(dict(sexta=sexta, segunda=segunda, vel=vel, ev=ev, pv=pv, ev_fase=ev_fase,
                                fator=fator, freeze=freeze, sem_sre=sem_sre, mes=mes))
            if all(t["pct"] >= 1 for t in tarefas[pid]):
                concluido = sexta
                break
        p["concluido"] = concluido
        hist[pid] = semanas
    return hist


# ----------------------------------------------------------------- custos

def gerar_custos(projetos, hist, rng):
    custos = []
    cat_pesos = [("pessoal", 0.62), ("consultoria", 0.14), ("cloud", 0.12), ("licencas", 0.07), ("despesas", 0.05)]
    descricao = {"pessoal": "Folha alocada", "consultoria": "Horas de consultoria", "cloud": f"Fatura {NUVEM}",
                 "licencas": "Licenças de software", "despesas": "Viagens e despesas"}
    nlanc = 0
    for p in projetos:
        queima = p["orcamento"] * 7 / p["duracao"]
        ev_ant = 0.0
        for s in hist[p["id"]]:
            dev = s["ev"] - ev_ant
            ev_ant = s["ev"]
            ociosidade = queima * 0.30 * max(0.0, 0.95 - s["vel"])   # gente parada continua custando
            ac = dev * s["fator"] + ociosidade
            extra = dev * max(0.0, s["fator"] - p["custo_base"] - 0.06)  # escopo que cresceu sem aditivo
            for cat, w in cat_pesos:
                valor = ac * w
                if cat == "consultoria":
                    valor += extra * 0.5
                if cat == "pessoal":
                    valor += extra * 0.2 - extra * 0.7 * w
                if valor <= 0:
                    continue
                partes = rng.randint(1, 2) if cat in ("pessoal", "consultoria") else 1
                for _ in range(partes):
                    nlanc += 1
                    v = round(valor / partes * rng.uniform(0.9, 1.1), 2)
                    d = s["segunda"] + dt.timedelta(days=rng.randint(0, 4))
                    txt = f"{v:.2f}"
                    if rng.random() < 0.03:                 # sujeira: decimal com vírgula
                        txt = txt.replace(".", ",")
                    custos.append([f"L{nlanc:07d}", p["id"], iso(d), cat,
                                   f"{descricao[cat]} {p['id']} semana {iso(s['segunda'])}", txt,
                                   f"CC-{p['id'][4:]}-{cat[:3].upper()}"])
                    if rng.random() < 0.015:                # estorno (é informação, não erro)
                        nlanc += 1
                        custos.append([f"L{nlanc:07d}", p["id"], iso(min(HOJE, d + dt.timedelta(days=rng.randint(3, 20)))),
                                       cat, f"ESTORNO ref L{nlanc - 1:07d}", f"{-round(v * rng.uniform(0.2, 1.0), 2):.2f}",
                                       f"CC-{p['id'][4:]}-{cat[:3].upper()}"])
    return custos


# ----------------------------------------------------------------- pessoas

def gerar_pessoas(projetos, hist, rng):
    """Colaboradores, alocações e timesheet semanal."""
    colaboradores, alocacoes = [], []
    pid_idx = {p["id"]: p for p in projetos}

    def novo(papel, admissao, senioridade=None):
        cid = f"COL{len(colaboradores) + 1:04d}"
        lo, hi = PAPEIS[papel]
        sen = senioridade or rng.choices(["junior", "pleno", "senior", "especialista"], [0.2, 0.42, 0.3, 0.08])[0]
        mult = {"junior": 0.75, "pleno": 1.0, "senior": 1.25, "especialista": 1.45}[sen]
        colaboradores.append(dict(id=cid, nome=pessoa(rng), papel=papel, senioridade=sen,
                                  custo=round(rng.uniform(lo, hi) * mult / 1.1, 2), admissao=admissao,
                                  desligamento=None))
        return colaboradores[-1]

    for p in projetos:
        pid = p["id"]
        fim_proj = p["concluido"]
        n = rng.randint(5, 11)
        papeis = ["tech_lead", "product_owner", "qa"]
        if rng.random() < 0.35 and pid not in (PROJETO_SEM_SRE, PROJETO_SRE_OCIOSO):
            papeis.append("sre")
        while len(papeis) < n:
            papeis.append(rng.choices(["dev_backend", "dev_frontend", "dev_mobile", "designer_ux", "engenheiro_dados"],
                                      [0.40, 0.25, 0.15, 0.08, 0.12])[0])
        for papel in papeis:
            adm = p["inicio"] - dt.timedelta(days=rng.randint(20, 1600))
            c = novo(papel, adm)
            pct = 50 if papel in ("product_owner", "designer_ux") and rng.random() < 0.5 else 100
            sai = None
            if pid in SQUAD_ROTATIVIDADE and rng.random() < 0.55:
                sai = HOJE - dt.timedelta(days=rng.randint(10, 240))
            elif rng.random() < 0.06:
                sai = p["inicio"] + dt.timedelta(days=rng.randint(30, max(31, (HOJE - p["inicio"]).days)))
            if sai and sai <= p["inicio"] + dt.timedelta(days=14):
                sai = None
            if sai and fim_proj and sai > fim_proj:
                sai = None
            if sai:
                c["desligamento"] = min(sai, HOJE)
            fim = c["desligamento"] or fim_proj
            alocacoes.append([c["id"], pid, p["inicio"], fim, pct])
            if c["desligamento"]:                         # reposição: alguém novo entra semanas depois
                entra = c["desligamento"] + dt.timedelta(days=rng.randint(14, 35))
                if entra < HOJE and (not fim_proj or entra < fim_proj):
                    r = novo(papel, entra - dt.timedelta(days=rng.randint(0, 5)), rng.choice(["junior", "pleno"]))
                    alocacoes.append([r["id"], pid, entra, fim_proj, pct])

    # os dois SREs da história: saem do PRJ-011 e vão para o PRJ-007, que ainda está no desenho
    p11, p07 = pid_idx[PROJETO_SEM_SRE], pid_idx[PROJETO_SRE_OCIOSO]
    for cid in SRES_OCIOSOS:
        c = next(x for x in colaboradores if x["id"] == cid)
        c.update(papel="sre", senioridade="senior", custo=round(rng.uniform(185, 200), 2),
                 admissao=dt.date(2022, 3, 1) + dt.timedelta(days=rng.randint(0, 300)), desligamento=None)
        alocacoes[:] = [a for a in alocacoes if a[0] != cid]
        alocacoes.append([cid, PROJETO_SEM_SRE, p11["inicio"], TROCA_SRE, 100])
        alocacoes.append([cid, PROJETO_SRE_OCIOSO, TROCA_SRE + dt.timedelta(days=3), None, 100])
    del p07

    # quem não está em projeto: plataforma, arquitetura, gestão
    while len(colaboradores) < N_COLABORADORES:
        novo(rng.choice(["arquiteto", "sre", "agilista", "gestor_engenharia", "sre"]),
             dt.date(2020, 1, 6) + dt.timedelta(days=rng.randint(0, 2000)))

    # timesheet semanal
    apontamentos = []
    papel_de = {c["id"]: c["papel"] for c in colaboradores}
    for cid, pid, ini, fim, pct in alocacoes:
        for s in hist[pid]:
            if s["sexta"] < ini or (fim and s["segunda"] > fim):
                continue
            disp = 40.0 * pct / 100
            papel = papel_de[cid]
            util = 0.55 + 0.40 * min(s["vel"], 1.05) / 1.05 + rng.gauss(0, 0.05)
            if s["freeze"] and papel in PAPEIS_DEV:
                util -= 0.30
            if s["sem_sre"] and papel in PAPEIS_DEV:
                util -= 0.22
            if cid in SRES_OCIOSOS and pid == PROJETO_SRE_OCIOSO:
                util = rng.uniform(0.02, 0.09)
            util = clamp(util, 0.02, 1.15)                # >1 = hora extra, é legítimo
            apontamentos.append([cid, pid, iso(s["segunda"]), disp, round(disp * util, 1)])
    return colaboradores, alocacoes, apontamentos


# ----------------------------------------------------------------- fornecedores

def frac_planejada(tarefas_p, fases, dia_proj):
    tot = sum(t["vp"] for t in tarefas_p if t["fase"] in fases)
    acc = sum(t["vp"] * clamp((dia_proj - t["a"]) / t["L"], 0, 1) for t in tarefas_p if t["fase"] in fases)
    return acc / tot if tot else 0.0


def gerar_fornecedores(projetos, tarefas, hist, rng):
    entregas = []
    atrasos = {}            # (pid, sexta) -> True se há entrega da CodeForge vencida e não entregue
    usa = {}
    n = 0
    for p in projetos:
        pid = p["id"]
        usa[pid] = [f for f in FORNECEDORES
                    if rng.random() < (0.45 if f == CONSULTORIA_ATRASADA else 0.28)
                    or (f == CONSULTORIA_ATRASADA and pid in CPI_CAINDO)]   # escopo extra vira hora de consultoria
        for forn in usa[pid]:
            fase, prazo, servico = FORNECEDORES[forn]
            tot = sum(t["vp"] for t in tarefas[pid] if t["fase"] == fase)
            prox = None
            lote = 0
            for s in hist[pid]:
                frac = s["ev_fase"].get(fase, 0) / tot if tot else 0
                if not (0.0 < frac < 0.97):
                    continue
                if prox is None or s["sexta"] >= prox:
                    lote += 1
                    n += 1
                    fator = rng.uniform(1.30, 1.52) if forn == CONSULTORIA_ATRASADA else rng.uniform(0.85, 1.12)
                    dped = s["sexta"] - dt.timedelta(days=rng.randint(0, 3))
                    dprom = dped + dt.timedelta(days=prazo)
                    dent = dped + dt.timedelta(days=round(prazo * fator))
                    entregue = dent <= HOJE
                    nome = rng.choice(GRAFIAS_CODEFORGE) if forn == CONSULTORIA_ATRASADA else forn
                    item = f"{servico} {lote} - {rng.choice(ATIVIDADES[fase])}"
                    valor = round(rng.uniform(60e3, 260e3) * (p["valor"] / 4.6e6) ** 0.5, 2)
                    entregas.append([f"ENT{n:05d}", pid, nome, item, f"{valor:.2f}", iso(dped), iso(dprom),
                                     iso(dent) if entregue else "", prazo, "entregue" if entregue else "em_aberto"])
                    if forn == CONSULTORIA_ATRASADA:
                        for s2 in hist[pid]:
                            if dprom < s2["sexta"] < dent:
                                atrasos[(pid, s2["sexta"])] = nome
                    prox = s["sexta"] + dt.timedelta(weeks=rng.randint(3, 6))
    return entregas, atrasos, usa


# ----------------------------------------------------------------- textos

FRASES = {
    "change_freeze": ["Change freeze da Black Friday: deploys em produção suspensos pelo cliente até 10/01.",
                      "Janela de mudança fechada pelo cliente (congelamento de fim de ano); {ativ} pronta, mas sem poder subir.",
                      "Freeze de produção do cliente travou o deploy de {ativ}.",
                      "Sem janela de deploy por causa do congelamento da Black Friday."],
    "falta_sre": ["Sem SRE alocado: pipeline de deploy quebrado e ninguém para corrigir.",
                  "Ambiente de homologação fora do ar há {n} dias, sem responsável de infraestrutura.",
                  "Deploy de {ativ} parado aguardando alguém de SRE para configurar o cluster.",
                  "Time de dev ocioso esperando ambiente; pedimos SRE de novo ao PMO."],
    "dependencia_fornecedor": ["Entrega da {forn} atrasada; {ativ} bloqueada aguardando o módulo.",
                               "Consultoria ({forn}) ainda não entregou a sprint prometida; integração parada.",
                               "{forn} pediu mais {n} dias para entregar {ativ}."],
    "rotatividade": ["Saída de {n2} desenvolvedores no mês; {ativ} ficou sem dono.",
                     "Onboarding de pessoas novas consumindo o tech lead; velocidade caiu.",
                     "Rotatividade alta no squad, {ativ} replanejada."],
    "mudanca_escopo": ["Cliente pediu nova integração fora do escopo; change request ainda não aprovado e o time já está trabalhando nela.",
                       "Escopo de {ativ} cresceu depois da reunião com o cliente, sem aditivo.",
                       "Retrabalho por mudança de regra de negócio pedida pelo cliente."],
    "bug_retrabalho": ["Bugs críticos na homologação de {ativ}; sprint dedicada a correções.",
                       "Teste de regressão reprovou {ativ}, refazendo."],
    "aprovacao_cliente": ["Aguardando aprovação do cliente para seguir com {ativ}.",
                          "Homologação do cliente atrasada, usuários-chave sem agenda."],
}
IMPACTOS = ["Impacto estimado: 1 semana.", "Impacto estimado de {d} dias no cronograma.",
            "Sem impacto no caminho crítico.", "", ""]
SEM_BLOQUEIO = ["Bloqueios: nenhum.", "Sem bloqueios.", "Bloqueios: nada relevante.", "Semana produtiva, sem bloqueios."]


def gerar_status(projetos, tarefas, hist, atrasos, rng):
    linhas = []
    for p in projetos:
        pid = p["id"]
        tot = sum(t["vp"] for t in tarefas[pid])
        for s in hist[pid]:
            pct = round(s["ev"] / tot * 100)
            spi = s["ev"] / s["pv"] if s["pv"] > 0 else 1.0
            # o farol é do gerente, e gerente é otimista: só fica vermelho bem depois do número
            farol = "verde" if spi >= 0.86 else ("amarelo" if spi >= 0.76 else "vermelho")
            fase = max(s["ev_fase"], key=lambda f: 0 if s["ev_fase"][f] >= sum(t["vp"] for t in tarefas[pid] if t["fase"] == f) * 0.999 else 1 + FASES[f][0]) \
                if s["ev_fase"] else "discovery"
            ativ = rng.choice(ATIVIDADES[fase]).lower()
            causa = None
            r = rng.random()
            if s["freeze"] and r < 0.85:
                causa = "change_freeze"
            elif s["sem_sre"] and r < 0.90:
                causa = "falta_sre"
            elif (pid, s["sexta"]) in atrasos and r < 0.35:
                causa = "dependencia_fornecedor"
            elif pid in SQUAD_ROTATIVIDADE and s["sexta"] > HOJE - dt.timedelta(days=270) and r < 0.45:
                causa = "rotatividade"
            elif pid in CPI_CAINDO and s["mes"] >= 6 and r < 0.35:
                causa = "mudanca_escopo"
            else:
                r2 = rng.random()
                causa = ("bug_retrabalho" if r2 < 0.06 else "aprovacao_cliente" if r2 < 0.14 else
                         "mudanca_escopo" if r2 < 0.17 else None)
            partes = [f"Status semanal {pid} - {br(s['sexta'])}.", f"Avanço: {pct}%.", f"Farol: {farol}.",
                      f"Entregas da semana: {rng.choice(ATIVIDADES[fase])}; {rng.choice(ATIVIDADES[fase])}."]
            if causa:
                partes.append("Bloqueios: " + rng.choice(FRASES[causa]).format(
                    ativ=ativ, n=rng.randint(2, 6), n2=rng.randint(2, 4), forn=atrasos.get((pid, s["sexta"]), "consultoria")))
                partes.append(rng.choice(IMPACTOS).format(d=rng.randint(3, 10)))
            else:
                partes.append(rng.choice(SEM_BLOQUEIO))
            texto = " ".join(x for x in partes if x)
            farol_txt = farol
            r = rng.random()
            if r < 0.01:                                   # sujeira: status não preenchido
                texto = rng.choice(["", "N/A", "ver ata da reunião"])
            elif r < 0.03:
                texto = texto.upper()
            if rng.random() < 0.12:
                farol_txt = rng.choice([farol.capitalize(), farol.upper()])
            linhas.append([pid, iso(s["sexta"]), p["gerente"], farol_txt, pct, texto])
    return linhas


# ----------------------------------------------------------------- arquivos por ferramenta

def escrever_excel(saida, p, tarefas_p, rng, codigo):
    cab = ["ID", "Fase", "Tarefa", "Responsável", "Início previsto", "Término previsto", "Início real",
           "Término real", "% Concluído", "Horas previstas"]
    linhas = [cab]

    def data(d):
        if d is None:
            return None
        return br(d) if rng.random() < 0.6 else serial_excel(d)   # sujeira: texto ou número de série

    for t in tarefas_p:
        pct = round(t["pct"] * 100, 1)
        pct_cel = f"{pct:g}%".replace(".", ",") if rng.random() < 0.7 else round(pct / 100, 3)
        if rng.random() < 0.006:                           # sujeira: % acima de 100
            pct_cel = f"{round(100 + rng.uniform(1, 18)):d}%"
        horas = t["horas"] if rng.random() > 0.03 else f"{t['horas']}h"
        linhas.append([t["n"], t["fase"].capitalize(), t["atividade"], t["resp"],
                       data(p["inicio"] + dt.timedelta(days=round(t["a"]))),
                       data(p["inicio"] + dt.timedelta(days=round(t["a"] + t["L"]))),
                       data(t["ini_real"]), data(t["fim_real"]), pct_cel, horas])
    linhas.append([None, None, "TOTAL", None, None, None, None, None, None, sum(t["horas"] for t in tarefas_p)])
    escrever_xlsx(saida / "excel" / codigo, linhas)


def escrever_clickup(saida, p, tarefas_p, rng, codigo, list_id):
    tasks = []
    for t in tarefas_p:
        pct = round(t["pct"] * 100)
        if pct >= 100:
            st = rng.choice([("done", "closed"), ("concluído", "closed"), ("Done", "closed"), ("closed", "closed")])
        elif pct == 0:
            st = rng.choice([("to do", "open"), ("backlog", "open"), ("a fazer", "open")])
        else:
            st = rng.choice([("in progress", "custom"), ("em andamento", "custom"), ("doing", "custom"),
                             ("review", "custom"), ("In Progress", "custom")])
        ini_b = p["inicio"] + dt.timedelta(days=round(t["a"]))
        fim_b = p["inicio"] + dt.timedelta(days=round(t["a"] + t["L"]))
        tasks.append({
            "id": f"86b{int(list_id) % 9973:04x}{t['n']:03d}",
            "name": t["atividade"],
            "status": {"status": st[0], "type": st[1]},
            "start_date": ms(t["ini_real"]) if t["ini_real"] else None,
            "due_date": ms(fim_b if pct < 100 else t["fim_real"]),
            "date_done": ms(t["fim_real"]) if t["fim_real"] else None,
            "time_estimate": t["horas"] * 3_600_000,
            "assignees": [{"username": t["resp"]}],
            "custom_fields": [
                {"name": "Fase", "type": "drop_down", "value": t["fase"]},
                {"name": "Progresso (%)", "type": "number", "value": pct if rng.random() < 0.7 else str(pct)},
                {"name": "Início baseline", "type": "date", "value": ms(ini_b)},
                {"name": "Fim baseline", "type": "date", "value": ms(fim_b)},
            ],
            "tags": [{"name": t["fase"]}],
        })
    doc = {"list": {"id": list_id, "name": p["nome"], "space": f"Delivery {p['segmento'].capitalize()}"},
           "exported_at": "2026-10-16T06:00:00Z", "tasks": tasks}
    caminho = saida / "clickup" / codigo
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")


def escrever_msproject(saida, p, tarefas_p, codigo):
    def dh(d, hora="08:00:00"):
        return f"{d.isoformat()}T{hora}" if d else None

    def tag(nome, valor):
        return f"<{nome}>{valor}</{nome}>" if valor is not None else ""

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    blocos = []
    uid = 0
    tot_h = sum(t["horas"] for t in tarefas_p)
    ev_h = sum(t["horas"] * t["pct"] for t in tarefas_p)
    blocos.append("<Task>" + tag("UID", 0) + tag("ID", 0) + tag("Name", esc(p["nome"])) + tag("OutlineLevel", 0)
                  + tag("Summary", 1) + tag("Start", dh(p["inicio"])) + tag("Finish", dh(p["fim_baseline"], "17:00:00"))
                  + tag("Work", f"PT{tot_h}H0M0S") + tag("PercentComplete", round(ev_h / tot_h * 100)) + "</Task>")
    for fase in FASES:
        lista = [t for t in tarefas_p if t["fase"] == fase]
        if not lista:
            continue
        uid += 1
        h = sum(t["horas"] for t in lista)
        ini = p["inicio"] + dt.timedelta(days=round(min(t["a"] for t in lista)))
        fim = p["inicio"] + dt.timedelta(days=round(max(t["a"] + t["L"] for t in lista)))
        blocos.append("<Task>" + tag("UID", uid) + tag("ID", uid) + tag("Name", fase.capitalize()) + tag("OutlineLevel", 1)
                      + tag("Summary", 1) + tag("Start", dh(ini)) + tag("Finish", dh(fim, "17:00:00"))
                      + tag("Work", f"PT{h}H0M0S")
                      + tag("PercentComplete", round(sum(t["horas"] * t["pct"] for t in lista) / h * 100))
                      + "<Baseline>" + tag("Number", 0) + tag("Start", dh(ini)) + tag("Finish", dh(fim, "17:00:00"))
                      + tag("Work", f"PT{h}H0M0S") + "</Baseline></Task>")
        for t in lista:
            uid += 1
            ini_b = p["inicio"] + dt.timedelta(days=round(t["a"]))
            fim_b = p["inicio"] + dt.timedelta(days=round(t["a"] + t["L"]))
            blocos.append("<Task>" + tag("UID", uid) + tag("ID", uid) + tag("Name", esc(t["atividade"])) + tag("OutlineLevel", 2)
                          + tag("Summary", 0) + tag("Start", dh(t["ini_real"] or ini_b)) + tag("Finish", dh(t["fim_real"] or fim_b, "17:00:00"))
                          + tag("ActualStart", dh(t["ini_real"])) + tag("ActualFinish", dh(t["fim_real"], "17:00:00"))
                          + tag("Work", f"PT{t['horas']}H0M0S") + tag("PercentComplete", round(t["pct"] * 100))
                          + "<Baseline>" + tag("Number", 0) + tag("Start", dh(ini_b)) + tag("Finish", dh(fim_b, "17:00:00"))
                          + tag("Work", f"PT{t['horas']}H0M0S") + "</Baseline></Task>")
    xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<Project xmlns="http://schemas.microsoft.com/project">'
           f"<Name>{esc(codigo)}</Name><Title>{esc(p['nome'])}</Title><Author>{esc(p['gerente'])}</Author>"
           f"<StartDate>{dh(p['inicio'])}</StartDate><Tasks>" + "\n".join(blocos) + "</Tasks></Project>\n")
    caminho = saida / "msproject" / codigo
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(xml, encoding="utf-8")


# ----------------------------------------------------------------- documentos

CONTRATOS = [
    # fornecedor, objeto, valor anual, fim vigência, renovação automática, aviso prévio (dias),
    # multa por atraso (% ao dia), teto da multa (%), SLA, reajuste
    (CONSULTORIA_ATRASADA, "prestação de serviços de desenvolvimento de software sob demanda, em sprints",
     14_800_000, dt.date(2027, 3, 31), True, 60, 0.5, 10, "entrega de cada sprint até a data acordada na ordem de serviço", "IPCA"),
    ("Pixel Design Studio", "design de interfaces e pesquisa com usuários", 2_100_000, dt.date(2027, 6, 30), True, 30,
     0.2, 5, "entrega de cada pacote de telas em até 20 dias corridos", "IPCA"),
    ("QualiTest Brasil", "testes funcionais e de regressão terceirizados", 3_400_000, dt.date(2026, 12, 31), False, 30,
     0.3, 8, "ciclo de testes concluído em até 20 dias corridos", "IGP-M"),
    ("SecureOps Segurança", "testes de invasão (pentest) e revisão de segurança", 1_250_000, dt.date(2027, 1, 31), True, 45,
     0.3, 10, "relatório de pentest em até 25 dias corridos", "IPCA"),
    ("DataPrime Analytics", "desenvolvimento de integrações e cargas de dados", 2_900_000, dt.date(2026, 11, 30), True, 60,
     0.25, 8, "lote de integração entregue em até 30 dias corridos", "IPCA"),
    (NUVEM, "serviços de computação em nuvem com compromisso anual de consumo", 18_500_000, dt.date(2026, 12, 31), True, 90,
     None, None, "disponibilidade mensal de 99,9%, com crédito de 10% da fatura por mês abaixo do SLA", "USD/PTAX"),
    ("Observa360", "plataforma de observabilidade (logs, métricas e alertas), 600 licenças", 1_980_000, dt.date(2026, 11, 30), True, 30,
     None, None, "disponibilidade mensal de 99,5%", "IPCA"),
    ("CodeVault", "repositórios de código e esteira de integração contínua, 520 licenças", 1_420_000, dt.date(2027, 2, 28), True, 60,
     None, None, "disponibilidade mensal de 99,9%", "IPCA"),
]


def contrato_pdf(c, rng):
    forn, objeto, valor, fim, renova, aviso, multa, teto, sla, reajuste = c
    inicio = fim.replace(year=fim.year - 1) + dt.timedelta(days=1)
    v = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    clausulas = [
        ("CLÁUSULA 1 - OBJETO", f"Contratação de {objeto} para os projetos de clientes da CONTRATANTE."),
        ("CLÁUSULA 2 - VALOR", f"O valor anual estimado do contrato é de {v}, faturado mensalmente conforme consumo "
                               f"ou ordens de serviço aprovadas."),
        ("CLÁUSULA 3 - VIGÊNCIA", f"Vigência de {br(inicio)} a {br(fim)}."),
        ("CLÁUSULA 4 - RENOVAÇÃO E AVISO PRÉVIO",
         (f"O contrato é renovado automaticamente por mais 12 meses, salvo manifestação contrária de qualquer das "
          f"partes com antecedência mínima de {aviso} dias do fim da vigência.") if renova else
         (f"O contrato não tem renovação automática. A intenção de renovar deve ser formalizada com {aviso} dias "
          f"de antecedência, sob pena de interrupção dos serviços.")),
        ("CLÁUSULA 5 - NÍVEL DE SERVIÇO (SLA)", f"A CONTRATADA se obriga a: {sla}."),
        ("CLÁUSULA 6 - MULTA POR ATRASO",
         (f"O atraso na entrega sujeita a CONTRATADA a multa de {str(multa).replace('.', ',')}% do valor da entrega "
          f"atrasada por dia corrido, limitada a {teto}% do valor da entrega. A multa é descontada da fatura seguinte.")
         if multa else
         "Não há multa por atraso. O descumprimento do SLA gera apenas os créditos previstos na cláusula 5."),
        ("CLÁUSULA 7 - REAJUSTE", f"Os preços são reajustados anualmente pelo índice {reajuste}."),
        ("CLÁUSULA 8 - RESCISÃO", f"A rescisão sem justa causa exige aviso prévio de {aviso} dias e pagamento de "
                                  f"{rng.choice([10, 15, 20])}% do valor remanescente do período contratado."),
        ("CLÁUSULA 9 - CONFIDENCIALIDADE E LGPD", "A CONTRATADA trata os dados pessoais dos clientes da CONTRATANTE "
                                                  "apenas para a execução do contrato, conforme a Lei 13.709/2018."),
    ]
    blocos = [("titulo", f"CONTRATO DE PRESTAÇÃO DE SERVIÇOS BANCÁRIOS Nº MRD-{slug(forn)[:10].upper()}-{inicio.year}"),
              ("subtitulo", f"CONTRATANTE: Meridian Bank S.A.  ·  CONTRATADA: {forn}"), ("espaco", "")]
    for titulo, texto in clausulas:
        blocos += [("subtitulo", titulo), ("normal", texto), ("espaco", "")]
    blocos += [("normal", f"São Paulo, {br(inicio - dt.timedelta(days=15))}."),
               ("normal", "Documento corporativo confidencial — Meridian Bank S.A.")]
    return blocos


MANUAL = [
    ("1. ARQUITETURA CORE BANCÁRIO E CANAIS", "Back-end de canais e motores de crédito em Java 21 (Spring Boot) ou Python 3.12. "
     "Integração com Alta Plataforma (Mainframe COBOL/CICS) e mensageria ISO 20022 via Kafka. Banco relacional padrão: "
     "PostgreSQL. Toda mudança em motor de crédito, PDD ou liquidação Pix exige aprovação do Comitê de Arquitetura e Risco."),
    ("2. AMBIENTES E SEGREGAÇÃO DE DADOS BANCÁRIOS", "Três ambientes segregados: desenvolvimento, homologação regulatória e produção na NuvemSul Cloud. "
     "Dados de sigilo bancário (Lei Complementar 105) e LGPD são estritamente mascarados fora de produção."),
    ("3. POLÍTICA DE DEPLOY E JANELA DO BANCO CENTRAL", "Deploy em produção apenas pela esteira homologada da CodeVault, com testes de regressão contábil e de estresse aprovados. "
     "Mudanças que afetam conectividade RSFN/SPI (Pix) ou envio de CADOC/SCR devem respeitar as janelas homologadas pelo BACEN."),
    ("4. FREEZE DE ALTA TEMPORADA BANCÁRIA E FECHAMENTO ANUAL", "De 1º de novembro a 10 de janeiro (pico transacional de Black Friday, 13º salário e fechamento contábil anual), "
     "mudanças em motores de liquidação Pix, autorizadores de cartão e checkout ficam congeladas, exceto correções emergenciais SEV1 ou determinações do BACEN."),
    ("5. ALOCAÇÃO DE SRE E ENGENHARIA DE CONFIABILIDADE", "Programas em fase de testes integrados (RSFN/Bureaus) ou implantação em produção exigem pelo menos um SRE dedicado. "
     "Iniciativas em fase de estudo regulatório (discovery) não devem reter SREs dedicados."),
    ("6. SEVERIDADE DE INCIDENTES OPERACIONAIS E PIX", "SEV1: indisponibilidade do motor Pix (SLA BACEN < 99,5%), falha no autorizador de cartões ou vazamento de dados; acionamento imediato 24x7 em 15 minutos. "
     "SEV2: degradação em concessão de crédito ou fila de PLD/Antifraude; resposta em 1 hora."),
    ("7. GESTÃO DE RISCO DE CRÉDITO E PDD (RES. CMN 4.966)", "Os modelos e sistemas de provisão para perdas esperadas (PDD - Stages 1, 2 e 3) e inadimplência Over 90 devem ser conciliados mensalmente com o balancete contábil e enviados ao SCR/BACEN."),
    ("8. GOVERNANÇA DE PORTFÓLIO E FAROL EXECUTIVO", "Todo gerente publica o status até sexta às 18h. Regra oficial do Comitê Executivo do Banco: "
     "farol verde exige SPI >= 0,95; amarelo entre 0,90 e 0,95; vermelho abaixo de 0,90."),
    ("9. GESTÃO DE FORNECEDORES E FINTECHS PARCEIRAS", "Consultorias de tecnologia bancária e bureaus entram por ordem de serviço vinculada a contrato-quadro. "
     "Atrasos em entregas críticas de sprints geram multa diária de SLA descontada em fatura."),
    ("10. SEGURANÇA CIBERNÉTICA, PLD/FT E SIGILO BANCÁRIO", "Todo sistema de movimentação financeira ou concessão de crédito passa por pentest obrigatório e validação de regras de Prevenção à Lavagem de Dinheiro (PLD/FT) antes do go-live."),
]


def manual_pdf():
    blocos = [("titulo", "Meridian Bank S.A. - Manual de Governança de TI, Risco e Operações Bancárias"),
              ("subtitulo", "Versão 4.2 · aprovado pelo Comitê de Risco e Arquitetura em 01/09/2026"), ("espaco", "")]
    for titulo, texto in MANUAL:
        blocos += [("subtitulo", titulo), ("normal", texto), ("espaco", "")]
    blocos += [("normal", "Documento corporativo interno — Meridian Bank S.A.")]
    return blocos


def gerar_operacoes_bancarias(projetos: list[dict], rng: random.Random) -> tuple[list[list], list[list]]:
    """Gera as duas bases operacionais bancárias (Carteira de Crédito/PDD e Monitoramento de Fraude Pix)."""
    modalidades = {
        "varejo": ("Cartão de Crédito & CDC Varejo", 4.8, 0.062),
        "financeiro": ("Capital de Giro & Corporate PJ", 8.5, 0.031),
        "saude": ("Crédito Pessoal Digital (PF)", 3.2, 0.074),
        "logistica": ("Antecipação de Recebíveis & Garantia", 5.1, 0.028),
        "industria": ("Financiamento Imobiliário & Consignado", 9.4, 0.019),
    }
    competencias = [dt.date(2025, 11, 1), dt.date(2025, 12, 1), dt.date(2026, 1, 1), dt.date(2026, 2, 1),
                    dt.date(2026, 3, 1), dt.date(2026, 4, 1), dt.date(2026, 5, 1), dt.date(2026, 6, 1),
                    dt.date(2026, 7, 1), dt.date(2026, 8, 1), dt.date(2026, 9, 1), dt.date(2026, 10, 1)]
    linhas_credito = []
    for p in projetos:
        pid = p["id"]
        mod_nome, saldo_base, over90_base = modalidades[p["segmento"]]
        fator_proj = (p["valor"] / 4.5e6) * rng.uniform(0.85, 1.20)
        for idx, comp in enumerate(competencias):
            # Projetos com CPI caindo ou atraso crítico apresentam deterioração de inadimplência/PDD
            agravamento = 1.0 + (0.045 * max(0, idx - 4) if pid in CPI_CAINDO else 0.0) + (0.03 if pid in SQUAD_ROTATIVIDADE else 0.0)
            saldo_mi = round(saldo_base * 100 * fator_proj * (1 + 0.012 * idx + rng.uniform(-0.01, 0.015)), 2)
            over90 = round(clamp(over90_base * 100 * agravamento * rng.uniform(0.94, 1.08), 0.8, 18.5), 2)
            if over90 >= 7.5:
                estagio = "Stage 3 - Risco Agravado (Default)"
                cobertura = rng.uniform(0.68, 0.85)
            elif over90 >= 4.0:
                estagio = "Stage 2 - Aumento Significativo de Risco"
                cobertura = rng.uniform(0.35, 0.55)
            else:
                estagio = "Stage 1 - Risco Normal"
                cobertura = rng.uniform(0.08, 0.22)
            pdd_mi = round(saldo_mi * (over90 / 100.0) * (1.0 + cobertura), 2)
            linhas_credito.append([
                comp.strftime("%Y-%m"), pid, mod_nome, p["cliente"], p["segmento"],
                f"{saldo_mi:.2f}", f"{over90:.2f}", estagio, f"{pdd_mi:.2f}", f"{round(cobertura * 100, 1):.1f}"
            ])

    canais = {
        "varejo": "Autorizador de Cartões & Checkout",
        "financeiro": "Open Finance & APIs de Crédito",
        "saude": "Motor Antifraude Pix & Biometria",
        "logistica": "Liquidação Instantânea SPI (Pix)",
        "industria": "Core Bancário & Informe Regulatório",
    }
    semanas_mon = sextas(dt.date(2026, 4, 17), HOJE)
    linhas_fraude = []
    for p in projetos[:30]:
        pid = p["id"]
        canal = canais[p["segmento"]]
        for sem in semanas_mon:
            vol_mil = round(rng.uniform(420, 2850) * (1.35 if pid in ECOMMERCE_FREEZE else 1.0), 1)
            val_mi = round(vol_mil * rng.uniform(0.18, 0.65), 2)
            tentativas = int(vol_mil * rng.uniform(1.2, 4.5))
            # Se é o PRJ-011 sem SRE ou squad com rotatividade, latência sobe e perda por fraude aumenta
            degradado = (pid == PROJETO_SEM_SRE and sem > TROCA_SRE) or (pid in SQUAD_ROTATIVIDADE)
            taxa_bloqueio = rng.uniform(0.82, 0.91) if degradado else rng.uniform(0.94, 0.992)
            fraude_bloq_mil = round(tentativas * rng.uniform(1.1, 2.8) * taxa_bloqueio, 2)
            perda_liq_mil = round(fraude_bloq_mil * ((1.0 - taxa_bloqueio) / max(taxa_bloqueio, 0.1)), 2)
            med_bacen = int(perda_liq_mil / rng.uniform(3.5, 6.0))
            latencia_ms = round(rng.uniform(280, 640) if degradado else rng.uniform(65, 195), 1)
            sla_pct = round(rng.uniform(98.40, 99.35) if degradado else rng.uniform(99.75, 99.99), 2)
            linhas_fraude.append([
                iso(sem), pid, canal, p["cliente"], f"{vol_mil:.1f}", f"{val_mi:.2f}",
                tentativas, f"{fraude_bloq_mil:.2f}", f"{perda_liq_mil:.2f}", med_bacen,
                f"{latencia_ms:.1f}", f"{sla_pct:.2f}"
            ])
    return linhas_credito, linhas_fraude


# ----------------------------------------------------------------- orquestração

def gerar(saida: pathlib.Path, seed: int) -> dict:
    def r(nome):                       # um gerador por assunto: mexer num não muda os outros
        return random.Random(f"{seed}:{nome}")

    projetos = gerar_projetos(r("projetos"))
    tarefas = gerar_tarefas(projetos, r("tarefas"))
    hist = simular(projetos, tarefas, r("simulacao"))
    custos = gerar_custos(projetos, hist, r("custos"))
    colaboradores, alocacoes, apontamentos = gerar_pessoas(projetos, hist, r("pessoas"))
    entregas, atrasos, _ = gerar_fornecedores(projetos, tarefas, hist, r("fornecedores"))
    status = gerar_status(projetos, tarefas, hist, atrasos, r("status"))

    # responsável de cada tarefa: alguém do squad
    rr = r("responsaveis")
    nome_de = {c["id"]: c["nome"] for c in colaboradores}
    squad = {}
    for cid, pid, *_ in alocacoes:
        squad.setdefault(pid, []).append(nome_de[cid])
    for p in projetos:
        for t in tarefas[p["id"]]:
            t["resp"] = rr.choice(squad.get(p["id"], [p["gerente"]]))

    # ---- arquivos por ferramenta + cadastro do PMO -------------------------------
    rs = r("sujeira")
    linhas_proj = []
    n_tarefas = 0
    sem_codigo = {"excel": None, "clickup": None}
    for p in projetos:
        f = p["ferramenta"]
        if f == "excel":
            codigo = f"Cronograma {p['id']}.xlsx" if rs.random() > 0.25 else f"{p['id']} - {p['nome'][:28].strip()} v{rs.randint(2, 7)} FINAL.xlsx"
            escrever_excel(saida, p, tarefas[p["id"]], r(f"excel:{p['id']}"), codigo)
        elif f == "clickup":
            list_id = str(901_200_000_000 + int(p["id"][4:]) * 7919)
            codigo = list_id
            escrever_clickup(saida, p, tarefas[p["id"]], r(f"clickup:{p['id']}"), f"lista_{list_id}.json", list_id)
        else:
            codigo = f"{p['id']}_{slug(p['tipo'])[:30]}.xml"
            escrever_msproject(saida, p, tarefas[p["id"]], codigo)
        n_tarefas += len(tarefas[p["id"]])
        codigo_txt = codigo
        if f in sem_codigo and sem_codigo[f] is None and p["id"] not in ("PRJ-011", "PRJ-007") and rs.random() < 0.2:
            sem_codigo[f] = p["id"]                         # sujeira: o PMO esqueceu de preencher o código
            codigo_txt = ""
        nome_ferr = {"excel": ["Excel", "excel", "Planilha"], "clickup": ["ClickUp", "Clickup", "click up"],
                     "msproject": ["MS Project", "Project", "msproject"]}[f]
        ferr_txt = nome_ferr[0] if rs.random() < 0.7 else rs.choice(nome_ferr[1:])
        data_ini = br(p["inicio"]) if rs.random() < 0.3 else iso(p["inicio"])   # sujeira: 2 formatos
        status_p = "concluido" if p["concluido"] else "em_andamento"
        linhas_proj.append([p["id"], p["nome"], p["cliente"], p["segmento"], p["tipo"], ferr_txt, codigo_txt,
                            f"{p['valor']:.2f}", f"{p['orcamento']:.2f}", data_ini, iso(p["fim_baseline"]),
                            status_p, p["gerente"]])
    escrever_csv(saida / "pmo/projetos.csv",
                 ["projeto_id", "nome_projeto", "cliente", "segmento", "tipo_projeto", "ferramenta", "codigo_ferramenta",
                  "valor_contrato", "orcamento_custo", "data_inicio", "data_fim_baseline", "status", "gerente_projeto"],
                 linhas_proj)
    escrever_csv(saida / "pmo/status_semanal.csv",
                 ["projeto_id", "data_status", "gerente", "farol", "pct_concluido", "texto_status"], status)

    linhas_col = []
    for c in colaboradores:
        linhas_col.append([c["id"], c["nome"], c["papel"], c["senioridade"], f"{c['custo']:.2f}", iso(c["admissao"]),
                           iso(c["desligamento"])])
    for cid in ("COL0102", "COL0257", "COL0433"):          # sujeira: pessoa duplicada no cadastro do RH
        o = next(x for x in linhas_col if x[0] == cid)
        linhas_col.append([o[0], o[1].upper(), o[2].upper(), o[3], o[4], o[5], o[6]])
    escrever_csv(saida / "rh/colaboradores.csv",
                 ["colaborador_id", "nome", "papel", "senioridade", "custo_hora", "data_admissao", "data_desligamento"],
                 linhas_col)
    escrever_csv(saida / "timesheet/apontamentos.csv",
                 ["colaborador_id", "projeto_id", "semana_inicio", "horas_disponiveis", "horas_apontadas"], apontamentos)
    escrever_csv(saida / "financeiro/custos.csv",
                 ["lancamento_id", "projeto_id", "data", "categoria", "descricao", "valor", "centro_custo"], custos)
    escrever_csv(saida / "compras/entregas_fornecedor.csv",
                 ["entrega_id", "projeto_id", "fornecedor", "item", "valor", "data_pedido", "data_prometida",
                  "data_entrega", "prazo_contratado_dias", "status"], entregas)

    rd = r("documentos")
    for c in CONTRATOS:
        escrever_pdf(saida / f"documentos/contratos/contrato_{slug(c[0])}.pdf", contrato_pdf(c, rd))
    escrever_pdf(saida / "documentos/manual/manual_de_tecnologias.pdf", manual_pdf())

    linhas_credito, linhas_fraude = gerar_operacoes_bancarias(projetos, r("operacoes_bancarias"))
    escrever_csv(
        saida / "operacoes_bancarias/carteira_credito_pdd.csv",
        ["competencia", "projeto_id", "modalidade_credito", "superintendencia", "segmento",
         "saldo_carteira_milhoes", "inadimplencia_over90_pct", "estagio_cmn_4966",
         "provisao_pdd_milhoes", "indice_cobertura_pdd_pct"],
        linhas_credito
    )
    escrever_csv(
        saida / "operacoes_bancarias/monitoramento_fraude_pix.csv",
        ["semana", "projeto_id", "canal_bancario", "superintendencia",
         "volume_transacoes_mil", "valor_transacionado_milhoes", "tentativas_fraude_detectadas",
         "fraude_bloqueada_mil", "perda_liquida_fraude_mil", "acionamentos_med_bacen",
         "latencia_p99_ms", "disponibilidade_sla_pct"],
        linhas_fraude
    )

    return dict(projetos=len(projetos), tarefas=n_tarefas, status_semanal=len(status), custos=len(custos),
                colaboradores=len(linhas_col), apontamentos=len(apontamentos),
                entregas_fornecedor=len(entregas), carteira_credito_pdd=len(linhas_credito),
                monitoramento_fraude_pix=len(linhas_fraude), pdf_contratos=len(CONTRATOS),
                arquivos_excel=FERRAMENTAS["excel"], arquivos_clickup=FERRAMENTAS["clickup"],
                arquivos_msproject=FERRAMENTAS["msproject"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--saida", default="./dados")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    saida = pathlib.Path(args.saida)
    for pasta in PASTAS_GERADAS + ["incidentes", "erp", "cronograma", "ponto", "frota", "almoxarifado", "rdo"]:
        if (saida / pasta).exists():                       # recomeça do zero (inclui pastas do case antigo)
            shutil.rmtree(saida / pasta)
    contagens = gerar(saida, args.seed)
    print(f"Dataset do Meridian Bank S.A. gerado em {saida}/ (seed {args.seed}, hoje = {HOJE.isoformat()})")
    for k, v in contagens.items():
        print(f"  {k:<20} {v:>9,}".replace(",", "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
