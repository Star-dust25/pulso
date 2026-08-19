<script lang="ts">
  import { onMount } from "svelte";
  import { getJSON } from "$lib/api";
  import DashboardContainer from "$lib/components/DashboardContainer.svelte";
  import ThresholdBar from "$lib/components/ThresholdBar.svelte";
  import EvolutionChart from "$lib/components/EvolutionChart.svelte";

  let data: any = $state(null);
  let loading = $state(true);
  let error = $state("");

  onMount(async () => {
    try {
      data = await getJSON("/api/alerta/estado");
    } catch (err) {
      // getJSON ya distingue entre backend caido, 500 y CORS.
      // Reemplazarlo por un mensaje generico seria perder esa informacion.
      error = err instanceof Error ? err.message : String(err);
      console.error(err);
    } finally {
      loading = false;
    }
  });

  let nivel = $derived(
    data?.etapa1_activa && data?.etapa2_activa
      ? "rojo"
      : data?.etapa1_activa
        ? "ambar"
        : "verde",
  );
</script>

<svelte:head>
  <title>Pulso</title>
</svelte:head>

<div class="max-w-5xl mx-auto mt-4">
  <!-- Header -->
  <header class="mb-12 mt-6 relative">
    <!-- Decorative accent -->
    <div
      class="absolute -top-10 -left-10 w-32 h-32 bg-gradient-to-br from-amber-200 to-red-100 rounded-full blur-3xl opacity-40 pointer-events-none"
    ></div>

    <div class="relative">
      <p
        class="text-slate-700 max-w-4xl text-lg sm:text-xl leading-relaxed font-light"
      >
        <strong class="font-semibold text-slate-900"
          >Sistema de Alerta Temprana ante El Niño Costero.</strong
        >
        Detección en dos etapas: anomalía térmica del litoral y respuesta del bosque
        seco, sobre datos satelitales de NOAA y USGS y la cartografía de ecosistemas
        del Gobierno Regional de Piura.
      </p>
    </div>
  </header>

  {#if loading}
    <div class="flex flex-col justify-center items-center py-32 space-y-4">
      <div
        class="animate-spin rounded-full h-10 w-10 border-b-2 border-slate-800"
      ></div>
      <span class="text-slate-400 font-medium text-sm tracking-wide"
        >Cargando datos de monitoreo...</span
      >
    </div>
  {:else if error}
    <div
      class="bg-red-50 text-red-600 p-5 rounded-xl border border-red-100 shadow-sm"
    >
      {error}
    </div>
  {:else if data}
    <!-- Alerta general (Banda principal) -->
    <div
      class="rounded-3xl p-6 mb-12 shadow-sm border relative overflow-hidden flex flex-col justify-center
                {nivel === 'ambar'
        ? 'bg-gradient-to-br from-amber-50/80 to-white border-amber-200/60'
        : nivel === 'rojo'
          ? 'bg-gradient-to-br from-red-50/80 to-white border-red-200/60'
          : 'bg-gradient-to-br from-emerald-50/80 to-white border-emerald-200/60'}"
    >
      <div class="flex items-center gap-3 mb-3">
        <!-- Status dot -->
        <span class="relative flex h-3 w-3">
          <span
            class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75
                        {nivel === 'ambar'
              ? 'bg-amber-400'
              : nivel === 'rojo'
                ? 'bg-red-400'
                : 'bg-emerald-400'}"
          ></span>
          <span
            class="relative inline-flex rounded-full h-3 w-3
                        {nivel === 'ambar'
              ? 'bg-amber-500'
              : nivel === 'rojo'
                ? 'bg-red-500'
                : 'bg-emerald-500'}"
          ></span>
        </span>
        <span
          class="text-xs font-bold tracking-[0.2em] uppercase
                        {nivel === 'ambar'
            ? 'text-amber-700'
            : nivel === 'rojo'
              ? 'text-red-700'
              : 'text-emerald-700'}"
        >
          {nivel === "ambar"
            ? "Vigilancia Activa"
            : nivel === "rojo"
              ? "Alerta Crítica"
              : "Condiciones Normales"}
        </span>
      </div>

      <div
        class="text-3xl font-bold font-slab text-slate-900 mb-2 tracking-tight leading-tight"
      >
        {nivel === "ambar"
          ? "Precursor oceánico activo: Sin confirmación territorial."
          : nivel === "rojo"
            ? "Alerta Roja: Mar y Territorio coinciden."
            : "Litoral y bosque seco en balance estacional."}
      </div>

      <div
        class="text-slate-600 text-base max-w-4xl leading-relaxed font-light"
      >
        {nivel === "ambar"
          ? "El mar presenta una anomalía térmica sostenida, pero el bosque seco aún no responde. Seguimos monitoreando de cerca la propagación del impacto."
          : nivel === "rojo"
            ? "El precursor oceánico ha sido confirmado por la reacción anómala de la vegetación en la costa norte. Riesgo de lluvias extremas."
            : "Tanto el litoral oceánico como la vegetación del bosque seco mantienen un comportamiento habitual para la temporada. Sin anomalías detectadas."}
      </div>
    </div>

    <!-- Dashboard Content -->
    <DashboardContainer
      titulo="Monitor de Etapas de Alerta"
      subtitulo="Evaluación del precursor térmico oceánico y confirmación posterior en el bosque seco."
      tooltip="Fuentes: NOAA OISST v2.1 (Mar) y LANDSAT 8 C2 L2 (Bosque Seco). El umbral de la Etapa 1 opera sobre la anomalía diaria y es un parámetro operativo de Pulso; no es el criterio mensual del ICEN oficial."
    >
      <div class="flex flex-col md:flex-row justify-between gap-8 py-2">
        <!-- Threshold 1: Precursor Oceánico -->
        <!--
          maxVal=5.0, no 4.0. En agosto de 2026 el precursor llego a +3.84 °C
          con anomalias diarias por encima de +4.2: con el techo en 4.0 la
          barra se satura y parece averiada justo cuando el episodio es mas
          intenso. El rango es solo escala visual, no afecta a ningun calculo.
        -->
        <ThresholdBar
          valor={data.precursor}
          minVal={-1.0}
          maxVal={5.0}
          umbral={data.umbral_precursor}
          titulo="1. Precursor Oceánico"
          valorTexto="{data.precursor > 0 ? '+' : ''}{data.precursor.toFixed(
            2,
          )} °C"
          estadoActivo={data.etapa1_activa}
          estadoTexto={data.etapa1_activa ? "ACTIVA" : "INACTIVA"}
          umbralTexto="Anomalía diaria > +{data.umbral_precursor} °C durante 15 días"
          fechaTexto={data.fecha_precursor}
          state={data.etapa1_activa ? "alerta" : "normal"}
        />

        <!-- Divider -->
        <div class="hidden md:block w-px bg-slate-100 self-stretch my-4"></div>

        <!-- Threshold 2: Confirmación Territorial -->
        <!--
          maxVal=4.0 para que quepan los valores historicos: 2017 llego a 3.35
          y 2023 a 3.69. Con el techo en 3.5 el segundo se saldria de escala.
        -->
        <ThresholdBar
          valor={data.z_msavi}
          minVal={-1.5}
          maxVal={4.0}
          umbral={data.umbral_msavi}
          titulo="2. Confirmación Territorial"
          valorTexto="{data.z_msavi > 0 ? '+' : ''}{data.z_msavi.toFixed(2)} σ"
          estadoActivo={data.etapa2_activa}
          estadoTexto={data.etapa2_activa ? "CONFIRMA" : "NO CONFIRMA"}
          umbralTexto="Anomalía z(MSAVI) ≥ {data.umbral_msavi}"
          fechaTexto={data.fecha_msavi}
          state={data.etapa2_activa ? "alerta" : "normal"}
        />
      </div>
    </DashboardContainer>

    {#if data.historico && data.historico.length > 0}
      <!-- Dashboard Content: Evolución Histórica -->
      <DashboardContainer
        titulo="Evolución Diaria del Precursor"
        subtitulo="Tendencia térmica en la región Niño 1+2 durante los últimos meses."
        tooltip="La línea punteada naranja representa el umbral operativo de Pulso (+{data.umbral_precursor} °C sobre la anomalía diaria)."
      >
        <div class="pt-2">
          <EvolutionChart
            data={data.historico}
            umbral_precursor={data.umbral_precursor}
          />
        </div>
      </DashboardContainer>
    {/if}
  {/if}
</div>
