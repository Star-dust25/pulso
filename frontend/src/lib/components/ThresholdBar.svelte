<script lang="ts">
  let {
    valor,
    minVal,
    maxVal,
    umbral,
    titulo,
    valorTexto,
    estadoActivo,
    estadoTexto,
    umbralTexto,
    fechaTexto,
    fuenteTexto = "",
    state = "normal",
    theme = "blue",
    tourIdPrefix = "",
  } = $props<{
    valor: number;
    minVal: number;
    maxVal: number;
    umbral: number;
    titulo: string;
    valorTexto: string;
    estadoActivo: boolean;
    estadoTexto: string;
    umbralTexto: string;
    fechaTexto: string;
    fuenteTexto?: string;
    state?: "normal" | "alerta";
    theme?: "red" | "green";
    tourIdPrefix?: string;
  }>();

  // Clamp value for visual representation (cappeado al 88% para que nunca se llene hasta el borde)
  let v_clamp = $derived(Math.max(minVal, Math.min(maxVal, valor)));
  let percentage = $derived(
    Math.min(88, Math.max(0, ((v_clamp - minVal) / (maxVal - minVal)) * 100))
  );
  let umbralPercentage = $derived(
    ((umbral - minVal) / (maxVal - minVal)) * 100,
  );

  let colorFill = $derived(theme === "red" ? "bg-red-500" : "bg-emerald-500");

  let colorText = $derived(
    theme === "red" ? "text-red-500" : "text-emerald-500",
  );

  let activeBadge = $derived(
    estadoActivo
      ? theme === "red"
        ? "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400"
        : "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400"
      : "bg-slate-50 dark:bg-white/5 text-slate-500 dark:text-slate-400",
  );
</script>

<div
  class="flex flex-col flex-1 w-full bg-white dark:bg-[#1C1C1E] p-6 sm:p-8 rounded-3xl shadow-sm border border-slate-200/60 dark:border-white/5 h-full"
>
  <!-- Header -->
  <div class="flex justify-between items-end mb-6">
    <div>
      <h3
        class="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-1"
      >
        {titulo}
      </h3>
      <div id="{tourIdPrefix ? tourIdPrefix + '-valor' : ''}" class="text-5xl font-semibold tracking-tight {colorText}">
        {valorTexto}
      </div>
    </div>
  </div>

  <!-- Threshold Bar Container -->
  <div id="{tourIdPrefix ? tourIdPrefix + '-barra' : ''}"
    class="relative w-full h-4 bg-[#F5F5F7] dark:bg-black rounded-full overflow-hidden my-4"
  >
    <!-- Progress Fill -->
    <div
      class="absolute top-0 left-0 h-full rounded-full transition-all duration-1000 ease-out {colorFill}"
      style="width: {percentage}%"
    ></div>

    <!-- Threshold Marker -->
    <div
      class="absolute top-0 bottom-0 w-[2px] bg-slate-900 dark:bg-white z-10"
      style="left: {umbralPercentage}%"
    ></div>
  </div>

  <!-- Threshold Label -->
  <div
    class="relative w-full h-6 text-[11px] text-slate-500 dark:text-slate-400 font-medium tracking-wide"
  >
    <div
      class="absolute -translate-x-1/2 flex flex-col items-center"
      style="left: {umbralPercentage}%"
    >
      <div class="w-px h-2 bg-slate-300 dark:bg-slate-600 mb-1"></div>
      Umbral ({umbral > 0 ? "+" : ""}{umbral})
    </div>
  </div>

  <!-- Subtitle / Details Card -->
  <div id="{tourIdPrefix ? tourIdPrefix + '-detalles' : ''}"
    class="mt-4 flex flex-col justify-center gap-4 bg-[#F5F5F7] dark:bg-black border border-slate-200/60 dark:border-white/5 p-5 rounded-2xl flex-1"
  >
    <div
      class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
    >
      <span class="text-[13px] text-slate-500 dark:text-slate-400 font-medium"
        >Estado actual</span
      >
      <span
        class="px-3 py-1 rounded-full text-[12px] font-semibold tracking-wider uppercase {activeBadge}"
      >
        {estadoTexto}
      </span>
    </div>

    <div
      class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-5 border-t border-slate-200/60 dark:border-white/5 pt-4"
    >
      <span class="text-[13px] text-slate-500 dark:text-slate-400 font-medium"
        >Criterio</span
      >
      <span
        class="text-[13px] font-semibold text-slate-900 dark:text-white text-left sm:text-right"
        >{umbralTexto}</span
      >
    </div>

    <div
      class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-4 border-t border-slate-200/60 dark:border-white/5 pt-4"
    >
      <span class="text-[13px] text-slate-500 dark:text-slate-400 font-medium"
        >Última medición</span
      >
      <span class="text-[13px] font-semibold text-slate-900 dark:text-white"
        >{fechaTexto}</span
      >
    </div>

    {#if fuenteTexto}
      <div
        class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-4 border-t border-slate-200/60 dark:border-white/5 pt-4"
      >
        <span class="text-[13px] text-slate-500 dark:text-slate-400 font-medium"
          >Fuente de datos</span
        >
        <span class="text-[13px] font-semibold text-slate-900 dark:text-white"
          >{fuenteTexto}</span
        >
      </div>
    {/if}

  </div>
</div>
