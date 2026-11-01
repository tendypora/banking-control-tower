import { useAnalyticsQuery, Card, CardContent, CardHeader, CardTitle, Skeleton } from '@databricks/appkit-ui/react';
import { useEffect, useState } from 'react';
import { z } from 'zod';
import { CAUSAS, corSituacao, indice, milhoes, num, pct } from '../../lib/dados';

// Valida a disponibilidade da tabela de escoragem preditiva (gold.score_estouro_30d).
const ScoreSchema = z.object({
  disponivel: z.boolean(),
  linhas: z.array(z.object({ projeto_id: z.string(), prob_estouro_30d: z.coerce.number() })),
});

function Kpi({ titulo, valor, detalhe, alerta }: { titulo: string; valor: string; detalhe: string; alerta?: boolean }) {
  return (
    <Card className={alerta ? 'border-red-300 dark:border-red-800' : ''}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{titulo}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-foreground">{valor}</div>
        <p className="text-xs text-muted-foreground mt-1">{detalhe}</p>
      </CardContent>
    </Card>
  );
}

const corFarol = (f: string | null) =>
  f === 'verde' ? 'text-emerald-700 dark:text-emerald-300' : f === 'amarelo' ? 'text-amber-700 dark:text-amber-300' : 'text-red-700 dark:text-red-300';

export function ProjetosPage() {
  const kpis = useAnalyticsQuery('kpis', {});
  const projetos = useAnalyticsQuery('projetos_risco', {});
  const [probPorProjeto, setProb] = useState(new Map<string, number>());
  const [temModelo, setTemModelo] = useState(false);

  useEffect(() => {
    fetch('/api/score-estouro')
      .then((r) => r.json())
      .then((j) => {
        const s = ScoreSchema.safeParse(j);
        if (s.success && s.data.disponivel) {
          setProb(new Map(s.data.linhas.map((l) => [l.projeto_id, l.prob_estouro_30d])));
          setTemModelo(true);
        }
      })
      .catch(() => setTemModelo(false));
  }, []);
  const k = kpis.data?.[0];

  return (
    <div className="space-y-6 w-full max-w-7xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Projetos em risco</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Fotografia de 16/10/2026, com Excel, ClickUp e MS Project integrados. SPI ou CPI abaixo de 0,9 é atenção; abaixo de 0,8 é crítico.
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.loading || !k ? (
          Array.from({ length: 4 }, (_, i) => <Skeleton key={i} className="h-28" />)
        ) : (
          <>
            <Kpi titulo="Projetos em risco" valor={`${num(k.projetos_em_risco)} de ${num(k.projetos_em_andamento)}`}
                 detalhe={`${num(k.projetos_criticos)} críticos · ${num(k.projetos_melancia)} com farol verde`} alerta />
            <Kpi titulo="Estouro previsto" valor={milhoes(k.estouro_previsto)} detalhe="EAC − orçamento, só quem estoura" alerta />
            <Kpi titulo="Carteira em andamento" valor={milhoes(k.carteira)}
                 detalhe="valor de contrato dos projetos em andamento" />
            <Kpi titulo="Alto risco em 30 dias" valor={String(num(k.alto_risco_30d))}
                 detalhe="faixa alta no modelo de estouro em 30 dias" />
          </>
        )}
      </div>

      {kpis.error && <div className="text-destructive bg-destructive/10 p-3 rounded-md">Erro: {String(kpis.error)}</div>}

      <Card>
        <CardHeader>
          <CardTitle>Todos os projetos em andamento</CardTitle>
          <p className="text-xs text-muted-foreground">
            Causa = a mais frequente no status semanal dos últimos 90 dias (extraída por IA). Farol = o que o gerente publicou nesta sexta.
            {temModelo ? ' Probabilidade de estouro em 30 dias estimada pelo modelo MLflow.' : ' Probabilidade de estouro: aguardando o modelo (—).'}
          </p>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          {projetos.loading && <Skeleton className="h-64" />}
          {projetos.error && <div className="text-destructive">Erro: {String(projetos.error)}</div>}
          {projetos.data && (
            <table className="w-full table-fixed text-sm">
              <thead className="text-left text-muted-foreground border-b">
                <tr>
                  <th className="py-2 w-[27%]">Projeto</th>
                  <th className="w-[9%]">Situação</th>
                  <th className="w-[6%] text-right">SPI</th>
                  <th className="w-[6%] text-right">CPI</th>
                  <th className="w-[8%] pl-3">Farol</th>
                  <th className="w-[10%] text-right">Estouro</th>
                  <th className="w-[8%] text-right">Atraso</th>
                  <th className="w-[15%] pl-3">Causa (status)</th>
                  <th className="w-[11%] text-right">P(estouro)</th>
                </tr>
              </thead>
              <tbody>
                {projetos.data.map((o) => {
                  const p = probPorProjeto.get(o.projeto_id);
                  return (
                    <tr key={o.projeto_id} className="border-b last:border-0">
                      <td className="py-2 truncate" title={`${o.projeto} · ${o.cliente} · ${o.ferramenta}`}>{o.projeto}</td>
                      <td><span className={`px-2 py-0.5 rounded text-xs font-medium ${corSituacao(o.situacao)}`}>{o.situacao}</span></td>
                      <td className={`text-right ${num(o.spi) < 0.9 ? 'font-semibold text-red-700 dark:text-red-300' : ''}`}>{indice(o.spi)}</td>
                      <td className={`text-right ${num(o.cpi) < 0.9 ? 'font-semibold text-red-700 dark:text-red-300' : ''}`}>{indice(o.cpi)}</td>
                      <td className={`pl-3 ${corFarol(o.farol_do_gerente)}`} title={`pelo número: ${o.farol_calculado}`}>
                        {o.farol_do_gerente}{String(o.melancia) === 'true' ? ' 🍉' : ''}
                      </td>
                      <td className="text-right">{num(o.estouro_previsto) > 0 ? milhoes(o.estouro_previsto) : '—'}</td>
                      <td className="text-right">{num(o.atraso_projetado_dias) > 0 ? `+${num(o.atraso_projetado_dias)} d` : '—'}</td>
                      <td className="pl-3 truncate" title={`dias de impacto por falta de SRE: ${num(o.dias_falta_sre)}`}>
                        {CAUSAS[o.causa_principal] ?? o.causa_principal}
                      </td>
                      <td className="text-right">{p == null ? '—' : pct(p)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
