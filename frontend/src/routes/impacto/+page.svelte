<script lang="ts">
  import DashboardContainer from "$lib/components/DashboardContainer.svelte";
  import { api } from "$lib/api";
</script>

<svelte:head>
  <title>Validación y Acoplamiento</title>
</svelte:head>

<div class="max-w-6xl mx-auto mt-4 px-4 sm:px-6 lg:px-8 py-8">
  <header class="mb-10">
    <h1 class="text-4xl font-bold font-slab text-slate-900 tracking-tight mb-3">
      Validación y Acoplamiento
    </h1>
    <p class="text-slate-500 max-w-3xl text-[15px] leading-relaxed">
      Correlación medida del acoplamiento mar-tierra y validación externa contra
      el índice oficial (ICEN).
    </p>
  </header>

  <div class="grid grid-cols-1 gap-8">
    <DashboardContainer
      titulo="Validación externa contra el índice oficial (ICEN)"
      subtitulo="Reconstruimos el Índice Costero El Niño desde datos satelitales crudos, aplicando el mismo criterio de cálculo: media móvil de 3 meses de la anomalía SST en la región Niño 1+2."
    >
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <!-- Metric Card 1: Correlación -->
          <div
            class="bg-white p-5 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 relative overflow-hidden group hover:shadow-md transition-shadow"
          >
            <div
              class="absolute left-0 top-0 bottom-0 w-1.5 bg-slate-400"
            ></div>
            <div
              class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2 pl-2"
            >
              Correlación
            </div>
            <div
              class="text-3xl font-oswald font-bold text-slate-800 mb-2 pl-2"
            >
              r = 0.971
            </div>
            <div class="text-[13px] text-slate-500 pl-2 leading-relaxed">
              Contra el ICEN oficial del IGP.
            </div>
          </div>

          <!-- Metric Card 2: Muestra -->
          <div
            class="bg-white p-5 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 relative overflow-hidden group hover:shadow-md transition-shadow"
          >
            <div
              class="absolute left-0 top-0 bottom-0 w-1.5 bg-slate-300"
            ></div>
            <div
              class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2 pl-2"
            >
              Muestra
            </div>
            <div
              class="text-3xl font-oswald font-bold text-slate-800 mb-2 pl-2"
            >
              532 meses
            </div>
            <div class="text-[13px] text-slate-500 pl-2 leading-relaxed">
              Periodo evaluado: 1982 — 2026.
            </div>
          </div>

          <!-- Metric Card 3: Acoplamiento -->
          <div
            class="bg-white p-5 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 relative overflow-hidden group hover:shadow-md transition-shadow"
          >
            <div
              class="absolute left-0 top-0 bottom-0 w-1.5 bg-emerald-500"
            ></div>
            <div
              class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2 pl-2"
            >
              Acoplamiento mar→bosque
            </div>
            <div
              class="text-3xl font-oswald font-bold text-slate-800 mb-2 pl-2"
            >
              r = 0.512
            </div>
            <div class="text-[13px] text-slate-500 pl-2 leading-relaxed">
              lag +1 mes · n=160 · p &lt; 0.0001
            </div>
          </div>
        </div>

        <div
          class="rounded-2xl overflow-hidden border border-slate-200/80 shadow-sm bg-white mb-8"
        >
          <img
            src={api("/static/mapas/3_validacion_icen.png")}
            alt="Validación ICEN"
            class="w-full h-auto"
            loading="lazy"
            onerror={(e) =>
              ((e.currentTarget as HTMLElement).style.display = "none")}
          />
        </div>

        <div class="max-w-4xl">
          <h3
            class="font-slab font-bold text-2xl text-slate-900 mb-4 tracking-tight"
          >
            Acoplamiento medido, no asumido
          </h3>
          <p class="text-slate-600 text-[15px] mb-4 leading-relaxed">
            El desfase de un mes entre la señal oceánica y la respuesta del
            bosque seco no se asumió: se obtuvo probando trece desfases
            distintos y conservando el que arrojó la relación más fuerte.
          </p>
          <p class="text-slate-600 text-[15px] mb-4 leading-relaxed">
            El páramo andino, en cambio, no muestra acoplamiento con la anomalía
            oceánica. Lo reportamos aunque contradice nuestra hipótesis inicial:
            esperábamos que también respondiera. La lectura más plausible es que
            su humedad, saturada durante buena parte del año, lo haga funcionar
            como regulador y no como receptor de la señal de El Niño.
          </p>
        </div>

        <div class="mt-8 text-[12px] text-slate-400 leading-relaxed max-w-4xl">
          Nota metodológica: el ENFEN calcula el ICEN oficial con ERSSTv5. Pulso
          lo reconstruye con OISST v2.1, de resolución diaria. Se trata por
          tanto de una reconstrucción independiente, no de una réplica del
          índice oficial; la correlación reportada mide precisamente cuánto se
          aproxima una a la otra.
        </div>
      </div>
    </DashboardContainer>
  </div>
</div>
