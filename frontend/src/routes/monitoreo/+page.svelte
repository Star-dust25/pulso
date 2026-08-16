<script lang="ts">
  import { onMount } from "svelte";
  import DashboardContainer from "$lib/components/DashboardContainer.svelte";
  import { assetUrl, getJSON } from "$lib/api";

  let mapasData: Record<string, any> = $state({});
  let loading = $state(true);
  let error = $state("");

  let tabActiva = $state("LITORAL"); // LITORAL, MONTES, ANDES
  let periodoActivo = $state("actual_2026"); // actual_2026, nino_2017, nino_2015_16

  const etiquetas: Record<
    string,
    { titulo: string; unidad: string; sensor: string; res: string }
  > = {
    LITORAL: {
      titulo: "Temperatura Superficial del Mar",
      unidad: "°C",
      sensor: "NOAA OISST v2.1",
      res: "0.25° (~28 km) · Diario",
    },
    MONTES: {
      titulo: "Vigor Vegetal Bosque Seco (MSAVI)",
      unidad: "",
      sensor: "Landsat 8 C2 L2",
      res: "30 m · Mediana mensual",
    },
    ANDES: {
      titulo: "Humedad del Páramo (NDMI)",
      unidad: "",
      sensor: "Landsat 8 C2 L2",
      res: "30 m · Mediana mensual",
    },
  };

  // Los periodos que genera construir_mapas.py. El orden importa: es el
  // orden en que aparecen las píldoras.
  const PERIODOS: Record<string, string> = {
    actual_2026: "Actual",
    nino_2017: "El Niño 2017",
    nino_2015_16: "El Niño 2015-16",
  };

  const leyendas: Record<
    string,
    { min: string; max: string; gradiente: string }
  > = {
    LITORAL: {
      min: "17 °C",
      max: "29 °C",
      gradiente: "from-[#2C5D73] via-[#5B8FA8] via-[#D68910] to-[#C0392B]",
    },
    MONTES: {
      min: "0.0",
      max: "0.6",
      gradiente: "from-[#8C6D46] via-[#B08D57] via-[#7D9E73] to-[#ACC8A2]",
    },
    ANDES: {
      min: "-0.2",
      max: "0.4",
      gradiente: "from-[#C0392B] via-[#D68910] via-[#5B8FA8] to-[#2C5D73]",
    },
  };

  onMount(async () => {
    try {
      mapasData = await getJSON("/api/mapas/indice");
    } catch (err) {
      // El mensaje real. "No se pudo cargar el índice" no distingue
      // entre backend apagado, 500 y CORS: tres problemas distintos
      // con tres arreglos distintos.
      error = err instanceof Error ? err.message : String(err);
      console.error(err);
    } finally {
      loading = false;
    }
  });

  // La clave se CONSTRUYE, no se busca.
  //
  // Antes esto era `Object.keys(mapasData).find(k => k.startsWith(tabActiva))`,
  // que devolvía siempre el primer periodo del ecosistema. Con tres
  // periodos por ecosistema, seis de los nueve mapas eran inalcanzables
  // desde la interfaz: los de 2017 y 2015-16, justo los que sostienen
  // el argumento de dosis-respuesta.
  let claveActual = $derived(`${tabActiva}__${periodoActivo}`);
  let mapaActual = $derived(mapasData[claveActual] ?? null);

  // Solo ofrecemos los periodos que el backend realmente publicó para
  // este ecosistema. Una píldora que lleva a un hueco es peor que una
  // píldora ausente.
  let periodosDisponibles = $derived(
    Object.keys(PERIODOS).filter((p) => `${tabActiva}__${p}` in mapasData),
  );

  let urlMapa = $derived(assetUrl(mapaActual?.url));
</script>

<svelte:head>
  <title>Monitoreo Satelital — Pulso</title>
</svelte:head>

<div class="max-w-6xl mx-auto mt-4 px-4 sm:px-6 lg:px-8 py-8">
  <header class="mb-10">
    <h1 class="text-4xl font-bold font-slab text-slate-900 tracking-tight mb-3">
      Monitoreo Satelital
    </h1>
    <p class="text-slate-500 max-w-3xl text-[15px] leading-relaxed">
      Visor de capas de observación de la Tierra. Mapas pre-generados para
      maximizar la velocidad de respuesta.
    </p>
  </header>

  <div class="border-b border-slate-100 pb-8 mb-8 space-y-4">
    <!-- Ecosistema -->
    <div class="flex flex-wrap gap-3">
      {#each Object.keys(etiquetas) as tab}
        <button
          class="px-5 py-2.5 rounded-full text-sm font-semibold transition-all shadow-sm {tabActiva ===
          tab
            ? 'bg-slate-800 text-white shadow-md'
            : 'bg-white border border-slate-200 text-slate-500 hover:text-slate-800 hover:border-slate-300'}"
          onclick={() => (tabActiva = tab)}
        >
          {tab}
        </button>
      {/each}
    </div>

    <!-- Periodo -->
    {#if periodosDisponibles.length > 1}
      <div class="flex flex-wrap items-center gap-2">
        <span
          class="text-xs font-semibold uppercase tracking-wider text-slate-400 mr-1"
          >Periodo</span
        >
        {#each periodosDisponibles as p}
          <button
            class="px-4 py-1.5 rounded-full text-xs font-semibold transition-all {periodoActivo ===
            p
              ? 'bg-slate-100 text-slate-800 ring-1 ring-slate-300'
              : 'text-slate-400 hover:text-slate-700'}"
            onclick={() => (periodoActivo = p)}
          >
            {PERIODOS[p]}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  {#if loading}
    <div class="flex justify-center py-20">
      <div
        class="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800"
      ></div>
    </div>
  {:else if error}
    <div class="bg-red-50 text-red-700 p-5 rounded-xl border border-red-100">
      <p class="font-semibold mb-1">No se pudo cargar el índice de mapas</p>
      <p class="text-sm font-light">{error}</p>
    </div>
  {:else}
    <DashboardContainer
      titulo={etiquetas[tabActiva].titulo}
      subtitulo={`Sensor: ${etiquetas[tabActiva].sensor} — Resolución: ${etiquetas[tabActiva].res}`}
    >
      {#if !urlMapa}
        <div class="text-center py-20 text-slate-400">
          <p>
            No hay mapa disponible para {tabActiva} · {PERIODOS[
              periodoActivo
            ] ?? periodoActivo}.
          </p>
          {#if mapaActual?.error}
            <!-- El motivo del fallo, no un mensaje genérico.
                             Si la generación falló por un timeout de Earth
                             Engine, quien mira debe poder saberlo. -->
            <p class="text-xs mt-2 font-mono text-slate-400">
              {mapaActual.error}
            </p>
          {/if}
          <p class="text-xs mt-2">
            La rutina diaria (GitHub Actions) volverá a intentarlo.
          </p>
        </div>
      {:else}
        <!-- Procedencia del dato.
                     El script ahora CONSERVA el mapa del día anterior si la
                     regeneración falla, en vez de borrarlo del índice. Ese
                     arreglo solo es honesto si la fecha se muestra: si no,
                     sería servir una imagen vieja en silencio. -->
        <div
          class="flex flex-wrap items-center gap-x-3 gap-y-1 mb-3 text-xs text-slate-400"
        >
          {#if mapaActual.generado}
            <span>Generado el {mapaActual.generado}</span>
          {/if}
          {#if mapaActual.desde && mapaActual.hasta}
            <span class="text-slate-300">·</span>
            <span>Composición {mapaActual.desde} → {mapaActual.hasta}</span>
          {/if}
          {#if mapaActual.kpi !== null && mapaActual.kpi !== undefined}
            <span class="text-slate-300">·</span>
            <span
              >Media {mapaActual.banda}:
              <strong class="text-slate-600">{mapaActual.kpi}</strong
              >{etiquetas[tabActiva].unidad}</span
            >
          {/if}
          {#if mapaActual.error_ultimo_intento}
            <span class="text-amber-600 font-medium">
              · La regeneración de hoy falló; se muestra la imagen anterior.
            </span>
          {/if}
        </div>

        <div
          class="bg-white border border-slate-200/80 rounded-2xl overflow-hidden shadow-sm h-[650px] relative"
        >
          <!-- object-contain, NO object-cover.
                         'cover' recorta los bordes para llenar el contenedor.
                         En una foto da igual; en un mapa geográfico significa
                         que estás mostrando menos territorio del que dice la
                         leyenda, sin avisar. Un mapa recortado miente sobre
                         su propia extensión. -->
          <img
            src={urlMapa}
            alt="Mapa de {etiquetas[tabActiva]
              .titulo} en Piura, periodo {PERIODOS[periodoActivo] ??
              periodoActivo}"
            class="w-full h-full object-contain bg-slate-50"
            loading="lazy"
          />

          <!-- Dynamic Legend -->
          <div
            class="absolute bottom-6 left-6 bg-white/95 backdrop-blur px-5 py-4 rounded-xl shadow-lg border border-slate-200/60 pointer-events-none w-64"
          >
            <p
              class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3"
            >
              Escala de Valores
            </p>
            <div
              class="h-3 w-full rounded-full bg-gradient-to-r {leyendas[
                tabActiva
              ].gradiente}"
            ></div>
            <div
              class="flex justify-between mt-2 text-xs font-semibold text-slate-500"
            >
              <span>{leyendas[tabActiva].min}</span>
              <span>{leyendas[tabActiva].max}</span>
            </div>
          </div>
        </div>
      {/if}
    </DashboardContainer>
  {/if}
</div>
