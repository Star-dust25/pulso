<script lang="ts">
  import DashboardContainer from "$lib/components/DashboardContainer.svelte";
  import { api } from "$lib/api";
</script>

<svelte:head>
  <title>Backtest Histórico — Pulso</title>
</svelte:head>

<div class="max-w-6xl mx-auto mt-4 px-4 sm:px-6 lg:px-8 py-8">
  <header class="mb-10">
    <h1
      class="text-2xl sm:text-3xl font-bold font-slab text-slate-900 tracking-tight mb-3"
    >
      Análisis retrospectivo frente al Niño costero de 2017, el único desastre
      mayor que cae dentro del alcance de la Etapa 2 (Landsat 8 opera desde
      2013).
    </h1>
  </header>

  <div class="grid grid-cols-1 gap-8">
    <DashboardContainer
      titulo="El Niño Costero 2017"
      subtitulo="Desborde del Río Piura, 27 de marzo (3,468 m³/s)"
    >
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 mt-2">
        <!-- Metric Card 1: Regla ICEN -->
        <div
          class="bg-white p-6 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 group hover:shadow-md transition-shadow"
        >
          <div
            class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2"
          >
            Regla ICEN (3 meses)
          </div>
          <div class="text-3xl font-oswald font-bold text-slate-800 mb-2">
            −5 días
          </div>
          <div class="text-[14px] text-slate-500 leading-relaxed">
            El índice de DIAGNÓSTICO habría llegado tarde.
          </div>
        </div>

        <!-- Metric Card 2: Pulso -->
        <div
          class="bg-white p-6 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 group hover:shadow-md transition-shadow"
        >
          <div
            class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2"
          >
            Precursor Diario Pulso
          </div>
          <div class="text-3xl font-oswald font-bold text-slate-800 mb-2">
            +68 días
          </div>
          <div class="text-[14px] text-slate-500 leading-relaxed">
            Etapa 1 · alerta temprana el 18-ene-2017.
          </div>
        </div>

        <!-- Metric Card 3: Confirmación -->
        <div
          class="bg-white p-6 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 group hover:shadow-md transition-shadow"
        >
          <div
            class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2"
          >
            Confirmación Territorial
          </div>
          <div class="text-3xl font-oswald font-bold text-slate-800 mb-2">
            +26 días
          </div>
          <div class="text-[14px] text-slate-500 leading-relaxed">
            Etapa 2 · compuesto de feb-2017 (z = 3.17), disponible el 1-marzo.
          </div>
        </div>
      </div>

      <!-- Info Block -->
      <div
        class="flex items-start bg-slate-50/50 p-6 rounded-2xl border border-slate-200 mb-10"
      >
        <div class="text-slate-500 mr-4 mt-0.5">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            ><circle cx="12" cy="12" r="10"></circle><line
              x1="12"
              y1="16"
              x2="12"
              y2="12"
            ></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg
          >
        </div>
        <div class="text-base text-slate-700 leading-relaxed">
          <span class="font-bold text-slate-900"
            >No estamos compitiendo con el ENFEN.</span
          > El índice oficial (ICEN) está diseñado para <strong>diagnosticar</strong> y declarar que hubo un Niño costero mucho después de que ocurrió, no para emitir alertas tempranas. Pulso demuestra que monitorear el mar a diario nos hace ganar semanas vitales de anticipación, pero nuestro mayor descubrimiento está en observar la reacción del ecosistema (Etapa 2).
        </div>
      </div>

      <!-- Text Content -->
      <div class="max-w-4xl">
        <h3
          class="font-slab font-bold text-3xl text-slate-900 mb-6 tracking-tight"
        >
          Por qué la anomalía oceánica no basta
        </h3>
        <p class="text-slate-700 text-lg mb-6 leading-relaxed">
          Un mar caliente no siempre significa un desastre inminente. Por ejemplo, 
          El Niño de 2015-16 calentó <strong class="text-slate-900 font-bold">MÁS</strong> el mar que el devastador Niño costero de 2017, y sin embargo, el daño real en la población fue muchísimo menor.
        </p>
        
        <ul class="list-disc pl-6 mb-8 text-slate-700 text-lg flex flex-col gap-4">
          <li>
            <strong class="font-bold text-slate-900">La contradicción oceánica:</strong> Los indicadores tradicionales (como el ICEN) catalogaron al evento de 2015-16 como "FUERTE", y al desastre de 2017 apenas como "MODERADO".
          </li>
          <li>
            <strong class="font-bold text-slate-900">La realidad en tierra:</strong> A pesar de tener un mar catalogado como menos peligroso, en 2017 hubo cerca de 73,000 damnificados en un solo mes, <strong>doce veces más</strong> que en el peor momento de 2015-16.
          </li>
        </ul>
        
        <p class="text-slate-700 text-lg mb-10 leading-relaxed font-semibold">
          La conclusión es clara: ningún indicador puramente oceánico puede anticipar la magnitud real de un desastre. 
          Monitorear cómo reacciona el territorio (la confirmación de la Etapa 2), sí.
        </p>
      </div>

      <!-- Image -->
      <div
        class="rounded-2xl border border-slate-200/80 shadow-sm bg-white mb-8 overflow-x-auto"
      >
        <img
          src={api("/static/mapas/5_dos_etapas_2015_vs_2017.png")}
          alt="Comparación 2015 vs 2017"
          class="w-full h-auto min-w-[800px] lg:min-w-full"
          loading="lazy"
          onerror={(e) =>
            ((e.currentTarget as HTMLElement).style.display = "none")}
        />
      </div>

      <!-- Footer Note -->
      <div class="mt-12 text-[15px] text-slate-600 leading-relaxed max-w-4xl">
        <h4 class="font-bold text-slate-800 mb-3">Transparencia y limitaciones del estudio</h4>
        <ul class="list-disc pl-5 space-y-3 mb-6">
          <li>
            <strong class="text-slate-700">Falta de historial largo:</strong> El satélite Landsat 8 (necesario para la Etapa 2) opera recién desde 2013. Esto significa que los devastadores Niños de 1983 y 1998 no pueden ser medidos con esta técnica. Es una prueba de concepto muy sólida, pero necesita más años de datos para ser estadísticamente definitiva.
          </li>
          <li>
            <strong class="text-slate-700">El caso atípico de 2015-16:</strong> Este evento oceánico fue tan extenso que abarcó dos temporadas de lluvias distintas. Nuestra Etapa 1 detectó el peligro en abril de 2015, lo que significa que el daño ocurrido un mes antes (marzo) no fue anticipado a tiempo por el algoritmo en ese año específico.
          </li>
        </ul>
        <div class="p-5 bg-slate-50 border border-slate-200 rounded-xl">
          <p class="font-medium text-slate-800">
            A pesar de estas limitaciones, la relación es innegable: a mayor señal satelital del bosque seco, mayor es la escala del desastre. Los episodios sin daños graves no superan la barrera de +1.10 de anomalía, mientras que años catastróficos como 2017 y 2023 rompieron por completo la escala, disparándose por encima de +3.35.
          </p>
        </div>
      </div>
    </DashboardContainer>
  </div>
</div>
