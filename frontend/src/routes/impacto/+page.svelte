<script lang="ts">
  import DashboardContainer from "$lib/components/DashboardContainer.svelte";
</script>

<svelte:head>
  <title>Impacto y Validación</title>
</svelte:head>

<div class="max-w-6xl mx-auto mt-4 px-4 sm:px-6 lg:px-8 py-8">
  <header class="mb-10">
    <h1 class="text-4xl font-bold font-slab text-slate-900 tracking-tight mb-3">
      Matriz de Impacto y Validación
    </h1>
    <p class="text-slate-500 max-w-3xl text-[15px] leading-relaxed">
      Correlación matemática del acoplamiento mar-tierra y validación externa
      contra el índice oficial (ICEN).
    </p>
  </header>

  <div class="grid grid-cols-1 gap-8">
    <DashboardContainer
      titulo="Validación externa contra el índice oficial (ICEN)"
      subtitulo="Reconstruimos el Índice Costero El Niño desde datos satelitales crudos, con la metodología oficial: media móvil de 3 meses de la anomalía SST."
    >
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <!-- Metric Card 1: Correlación -->
          <div class="bg-white p-5 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 relative overflow-hidden group hover:shadow-md transition-shadow">
            <div class="absolute left-0 top-0 bottom-0 w-1.5 bg-slate-400"></div>
            <div class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2 pl-2">Correlación</div>
            <div class="text-3xl font-oswald font-bold text-slate-800 mb-2 pl-2">r = 0.971</div>
            <div class="text-[13px] text-slate-500 pl-2 leading-relaxed">Contra el ICEN oficial del IGP.</div>
          </div>

          <!-- Metric Card 2: Muestra -->
          <div class="bg-white p-5 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 relative overflow-hidden group hover:shadow-md transition-shadow">
            <div class="absolute left-0 top-0 bottom-0 w-1.5 bg-slate-300"></div>
            <div class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2 pl-2">Muestra</div>
            <div class="text-3xl font-oswald font-bold text-slate-800 mb-2 pl-2">532 meses</div>
            <div class="text-[13px] text-slate-500 pl-2 leading-relaxed">Periodo evaluado: 1982 — 2026.</div>
          </div>

          <!-- Metric Card 3: Acoplamiento -->
          <div class="bg-white p-5 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 relative overflow-hidden group hover:shadow-md transition-shadow">
            <div class="absolute left-0 top-0 bottom-0 w-1.5 bg-emerald-500"></div>
            <div class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2 pl-2">Acoplamiento mar→bosque</div>
            <div class="text-3xl font-oswald font-bold text-slate-800 mb-2 pl-2">r = 0.512</div>
            <div class="text-[13px] text-slate-500 pl-2 leading-relaxed">lag +1 mes · n=160 · p &lt; 0.0001</div>
          </div>
        </div>

        <div class="rounded-2xl overflow-hidden border border-slate-200/80 shadow-sm bg-white mb-8">
          <img
            src="http://127.0.0.1:8000/static/mapas/3_validacion_icen.png"
            alt="Validación ICEN"
            class="w-full h-auto"
            loading="lazy"
            onerror={(e) =>
              ((e.currentTarget as HTMLElement).style.display = "none")}
          />
        </div>

        <div class="max-w-4xl">
          <h3 class="font-slab font-bold text-2xl text-slate-900 mb-4 tracking-tight">
            Acoplamiento medido, no asumido
          </h3>
          <p class="text-slate-600 text-[15px] mb-4 leading-relaxed">
            El ecosistema del páramo andino no responde a la anomalía oceánica. Su
            humedad está saturada de forma permanente y actúa como regulador, no
            como receptor de la señal de El Niño.
          </p>
        </div>
      </div>
    </DashboardContainer>
  </div>
</div>
