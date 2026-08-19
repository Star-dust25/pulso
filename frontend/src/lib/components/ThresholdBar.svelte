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
    state = "normal",
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
    state?: "normal" | "alerta";
  }>();

  // Clamp value for visual representation
  let v_clamp = $derived(Math.max(minVal, Math.min(maxVal, valor)));
  let percentage = $derived(((v_clamp - minVal) / (maxVal - minVal)) * 100);
  let umbralPercentage = $derived(
    ((umbral - minVal) / (maxVal - minVal)) * 100,
  );

  // El valor real excede el rango representable: la barra se satura y deja
  // de reflejar la magnitud. Se avisa en lugar de dibujar una barra llena
  // (o vacia) que sugiere un tope que no existe.
  //
  // Se comprueban LOS DOS extremos. Antes solo se miraba por arriba, y el
  // caso de abajo tambien ocurre: durante La Niña la anomalia del precursor
  // baja de -1.0, que es el minimo de la barra, y una barra vacia se lee
  // como "cero" en vez de "fuera de escala".
  let fueraPorArriba = $derived(valor > maxVal);
  let fueraPorAbajo = $derived(valor < minVal);
  let fueraDeRango = $derived(fueraPorArriba || fueraPorAbajo);

  let colorFill = $derived(
    state === "alerta"
      ? "bg-gradient-to-r from-orange-500 to-red-600"
      : "bg-gradient-to-r from-slate-300 to-slate-400",
  );
</script>

<div class="flex flex-col flex-1 w-full p-2">
  <!-- Header -->
  <div class="flex justify-between items-end mb-6">
    <div>
      <h3
        class="text-sm font-bold text-slate-500 uppercase tracking-[0.15em] mb-1"
      >
        {titulo}
      </h3>
      <!-- The value itself in Oswald -->
      <div
        class="text-5xl sm:text-6xl font-oswald font-bold tracking-tight {state ===
        'alerta'
          ? 'text-red-600'
          : 'text-slate-800'}"
      >
        {valorTexto}
      </div>
    </div>
  </div>

  <!-- Threshold Bar Container -->
  <div
    class="relative w-full h-4 bg-slate-100 rounded-full shadow-[inset_0_2px_4px_rgba(0,0,0,0.06)] overflow-hidden my-3"
  >
    <!-- Progress Fill -->
    <div
      class="absolute top-0 left-0 h-full rounded-full transition-all duration-1000 ease-out {colorFill}"
      style="width: {percentage}%"
    ></div>

    <!-- Threshold Marker -->
    <div
      class="absolute top-0 bottom-0 w-[3px] bg-slate-800 z-10 shadow-sm"
      style="left: {umbralPercentage}%"
    ></div>
  </div>

  <!-- Threshold Label -->
  <div
    class="relative w-full h-8 text-xs text-slate-400 font-semibold tracking-wide"
  >
    <div
      class="absolute -translate-x-1/2 mt-1 flex flex-col items-center"
      style="left: {umbralPercentage}%"
    >
      <div class="w-px h-2 bg-slate-300 mb-1"></div>
      Umbral ({umbral > 0 ? "+" : ""}{umbral})
    </div>
  </div>

  <!-- Subtitle / Details Card -->
  <div
    class="mt-4 flex flex-col gap-3 bg-white border border-slate-200/60 shadow-sm p-5 rounded-2xl"
  >
    <div class="flex items-center justify-between gap-3">
      <span class="text-sm text-slate-500 font-medium shrink-0"
        >Estado actual</span
      >
      <span
        class="px-3 py-1 rounded-full text-xs font-bold tracking-widest uppercase
                {estadoActivo
          ? state === 'alerta'
            ? 'bg-red-50 text-red-600 border border-red-100'
            : 'bg-amber-50 text-amber-600 border border-amber-100'
          : 'bg-slate-50 text-slate-600 border border-slate-200'}"
      >
        {estadoTexto}
      </span>
    </div>

    <div class="h-px w-full bg-slate-100"></div>

    <div class="flex items-start justify-between gap-4">
      <span class="text-sm text-slate-500 font-medium shrink-0"
        >Criterio umbral</span
      >
      <span class="text-sm font-semibold text-slate-700 text-right leading-snug"
        >{umbralTexto}</span
      >
    </div>

    <div class="h-px w-full bg-slate-100"></div>

    <div class="flex items-center justify-between gap-3">
      <span class="text-sm text-slate-500 font-medium shrink-0"
        >Último dato disponible</span
      >
      <span class="text-xs text-slate-400 uppercase tracking-wider"
        >{fechaTexto}</span
      >
    </div>

    {#if fueraDeRango}
      <div class="h-px w-full bg-slate-100"></div>
      <p class="text-[11px] text-slate-400 leading-relaxed">
        El valor queda fuera del rango representable en la barra ({minVal} a {maxVal});
        la barra aparece {fueraPorArriba ? "completa" : "vacía"} y no refleja la
        magnitud real.
      </p>
    {/if}
  </div>
</div>
