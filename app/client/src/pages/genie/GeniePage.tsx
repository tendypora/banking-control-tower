import { GenieChat } from '@databricks/appkit-ui/react';

export function GeniePage() {
  return (
    <div className="space-y-6 w-full max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Perguntar</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Genie &ldquo;Farol · Diretoria&rdquo;: projetos, custo do atraso, gente parada, causa do atraso no
          status semanal e o risco de estouro em 30 dias.
          Experimente: <i>&ldquo;Por que o PRJ-011 atrasou?&rdquo;</i>
        </p>
      </div>
      <div className="h-[min(640px,72vh)] border rounded-lg overflow-hidden">
        <GenieChat alias="default" />
      </div>
    </div>
  );
}
