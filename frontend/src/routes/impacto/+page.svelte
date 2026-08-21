<script lang="ts">
  import DashboardContainer from "$lib/components/DashboardContainer.svelte";
  import { api } from "$lib/api";
</script>

<svelte:head>
  <title>Validación y Acoplamiento</title>
</svelte:head>

<div class="max-w-6xl mx-auto mt-4 px-4 sm:px-6 lg:px-8 py-8">
  <header class="mb-10">
    <h1 class="text-3xl sm:text-4xl font-bold font-slab text-slate-900 tracking-tight mb-3">
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
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 mt-2">
          <!-- Metric Card 1: Correlación -->
          <div
            class="bg-white p-6 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 group hover:shadow-md transition-shadow"
          >
            <div
              class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2"
            >
              Correlación
            </div>
            <div class="text-3xl font-oswald font-bold text-slate-800 mb-2">
              r = 0.971
            </div>
            <div class="text-[14px] text-slate-500 leading-relaxed">
              Contra el ICEN oficial del IGP.
            </div>
          </div>

          <!-- Metric Card 2: Muestra -->
          <div
            class="bg-white p-6 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 group hover:shadow-md transition-shadow"
          >
            <div
              class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2"
            >
              Muestra
            </div>
            <div class="text-3xl font-oswald font-bold text-slate-800 mb-2">
              532 meses
            </div>
            <div class="text-[14px] text-slate-500 leading-relaxed">
              Periodo evaluado: 1982 — 2026.
            </div>
          </div>

          <!-- Metric Card 3: Acoplamiento -->
          <div
            class="bg-white p-6 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 group hover:shadow-md transition-shadow"
          >
            <div
              class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2"
            >
              Acoplamiento mar→bosque
            </div>
            <div class="text-3xl font-oswald font-bold text-slate-800 mb-2">
              r = 0.499
            </div>
            <div class="text-[14px] text-slate-500 leading-relaxed">
              lag +1 mes · n = 162 · Bonferroni sobre 13 desfases
            </div>
          </div>
        </div>

        <div
          class="rounded-2xl border border-slate-200/80 shadow-sm bg-white mb-8 overflow-x-auto"
        >
          <img
            src={api("/static/mapas/3_validacion_icen.png")}
            alt="Validación ICEN"
            class="w-full h-auto min-w-[800px] lg:min-w-full"
            loading="lazy"
            onerror={(e) =>
              ((e.currentTarget as HTMLElement).style.display = "none")}
          />
        </div>

        <div class="max-w-4xl">
          <h3
            class="font-slab font-bold text-3xl text-slate-900 mb-6 tracking-tight"
          >
            Acoplamiento medido, no asumido
          </h3>
          <p class="text-slate-700 text-lg mb-6 leading-relaxed">
            El desfase de un mes entre la señal oceánica y la respuesta del
            bosque seco no se asumió: se obtuvo probando trece desfases
            distintos y conservando el que arrojó la relación más fuerte. Probar
            trece hipótesis infla la probabilidad de encontrar una significativa
            por azar, así que aplicamos la corrección estricta de Bonferroni: el umbral
            real de significancia es p &lt; 0.0038, no el clásico 0.05. Además, ambas series se
            desestacionalizaron antes de correlacionarlas, para que el ciclo
            anual compartido no fabricara un espejismo estadístico que no existe.
          </p>
          <p class="text-slate-700 text-lg mb-6 leading-relaxed">
            El páramo andino, en cambio, no muestra acoplamiento con la anomalía
            oceánica. Lo reportamos abiertamente aunque contradice nuestra hipótesis inicial:
            esperábamos que también respondiera. La lectura más plausible es que
            su humedad constante, saturada durante buena parte del año, lo hace funcionar
            como un "amortiguador" del clima y no como un amplificador sensible de la señal de El Niño.
          </p>
          <p class="text-slate-700 text-lg mb-10 leading-relaxed font-semibold">
            Que ese control en la sierra salga nulo es precisamente lo que da valor al
            resultado del bosque seco en la costa. Si todos los ecosistemas correlacionaran, 
            la señal podría ser simple ruido o una tendencia climática global. 
            El contraste claro entre una reacción violenta (costa) y una reacción plana (sierra) 
            es lo que permite demostrar que el mecanismo de alerta en la Etapa 2 es real y geográficamente específico.
          </p>
        </div>

        <div class="mt-12 text-[15px] text-slate-600 leading-relaxed max-w-4xl">
          <h4 class="font-bold text-slate-800 mb-3">Notas metodológicas y limitaciones</h4>
          <ul class="list-disc pl-5 space-y-4">
            <li>
              <strong class="text-slate-700">Reconstrucción independiente:</strong> El ENFEN calcula el ICEN oficial combinando datos ERSSTv5 y
              climatologías escalonadas cada cinco años; Pulso reconstruye el índice usando los datos satelitales 
              OISST v2.1 y una climatología base estable (1991-2020). No es una réplica exacta; 
              la correlación mide qué tan cerca estamos de la fuente original. El pequeño sesgo inevitable 
              se recalcula dinámicamente sobre la ventana reciente y se resta antes de publicar cualquier dato en la plataforma.
            </li>
            <li>
              <strong class="text-slate-700">Autocorrelación temporal:</strong> Los valores P (significancia estadística) asumen observaciones independientes.
              Como las series climáticas mensuales están fuertemente autocorrelacionadas (lo que pasa hoy depende de lo que pasó ayer), 
              el número de observaciones 100% independientes es menor que n = 162. Por lo tanto, la significancia real podría estar ligeramente subestimada. 
              Lo verdaderamente defendible del hallazgo no es solo el valor P, sino el coeficiente de correlación (r = 0.499), 
              la forma del correlograma cruzado, y el contraste claro con el control de ecosistemas andinos que arrojó nulo.
            </li>
          </ul>
        </div>
    </DashboardContainer>
  </div>
</div>
