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
              r = 0.499
            </div>
            <div class="text-[13px] text-slate-500 pl-2 leading-relaxed">
              lag +1 mes · n = 162 · Bonferroni sobre 13 desfases
            </div>
          </div>
        </div>

        <div
          class="rounded-2xl overflow-hidden border border-slate-200/80 shadow-sm bg-white mb-8 -mx-4 sm:mx-0"
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
            distintos y conservando el que arrojó la relación más fuerte. Probar
            trece hipótesis infla la probabilidad de encontrar una significativa
            por azar, así que aplicamos la corrección de Bonferroni: el umbral
            real de significancia es p &lt; 0.0038, no 0.05. Ambas series se
            desestacionalizaron antes de correlacionarlas, para que el ciclo
            anual compartido no fabricara un desfase que no existe.
          </p>
          <p class="text-slate-600 text-[15px] mb-4 leading-relaxed">
            El páramo andino, en cambio, no muestra acoplamiento con la anomalía
            oceánica. Lo reportamos aunque contradice nuestra hipótesis inicial:
            esperábamos que también respondiera. La lectura más plausible es que
            su humedad, saturada durante buena parte del año, lo haga funcionar
            como regulador y no como receptor de la señal de El Niño.
          </p>
          <p class="text-slate-600 text-[15px] mb-4 leading-relaxed">
            Que ese control salga nulo es precisamente lo que da valor al
            resultado del bosque seco. Si todas las series correlacionaran entre
            sí, la señal sería ruido: el contraste entre una respuesta fuerte y
            una respuesta plana es lo que permite atribuirla al mecanismo y no a
            una tendencia común.
          </p>
        </div>

        <div class="mt-8 text-[12px] text-slate-400 leading-relaxed max-w-4xl">
          <p class="mb-3">
            Nota metodológica: el ENFEN calcula el ICEN oficial con ERSSTv5 y
            climatologías escalonadas cada cinco años; Pulso lo reconstruye con
            OISST v2.1 y una sola climatología 1991-2020. Se trata por tanto de
            una reconstrucción independiente, no de una réplica del índice
            oficial; la correlación reportada mide precisamente cuánto se
            aproxima una a la otra. El sesgo entre ambas series deriva con el
            tiempo y cambia de signo, por lo que se recalcula sobre la ventana
            reciente y se resta antes de publicar cualquier valor.
          </p>
          <p>
            Los valores p del acoplamiento asumen observaciones independientes.
            Las series mensuales están autocorrelacionadas, así que el número
            efectivo de observaciones es menor que n = 162 y esos valores están
            subestimados. Lo defendible es el coeficiente, la forma del
            correlograma y el contraste con el control.
          </p>
        </div>
    </DashboardContainer>
  </div>
</div>
