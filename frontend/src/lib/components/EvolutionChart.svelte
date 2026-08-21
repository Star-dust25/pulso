<script lang="ts">
  import { onMount } from "svelte";
  import Chart from "chart.js/auto";

  // 'umbral_magnitud' vuelve a existir, esta vez con el valor real que
  // envia el backend (UMBRAL_MAGNITUD = 2.0 de core_alerta.py), no un
  // valor por defecto inventado como antes. Dibuja la segunda linea de
  // referencia que ya aparece en los paneles ETAPA 1 del backtest
  // historico ("Umbral magnitud"), y que aqui faltaba.
  let { data, umbral_precursor, umbral_magnitud } = $props<{
    data: Array<{ fecha: string; anomalia: number; precursor: number }>;
    umbral_precursor: number;
    umbral_magnitud: number;
  }>();

  let canvasRef: HTMLCanvasElement;
  let chartInstance: Chart | null = null;

  // Lectura del punto donde esta el cursor, mostrada en una fila FIJA
  // fuera del lienzo (ver el markup mas abajo), en vez del globo
  // flotante por defecto de Chart.js. El globo por defecto se dibuja
  // pegado al cursor sin importar que haya debajo, asi que cuando la
  // linea sube (como en el episodio actual) el propio globo terminaba
  // tapando la parte del grafico que se queria leer. Una fila fija
  // nunca se superpone a nada, porque no comparte espacio con el canvas.
  let hoverInfo = $state<{
    fecha: string;
    anomalia: number;
    precursor: number;
  } | null>(null);

  const MESES = [
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
  ];

  function formatFecha(fecha: string): string {
    // Parseo manual en vez de `new Date(fecha)`: el constructor de
    // Date interpreta 'YYYY-MM-DD' como medianoche UTC, y en un huso
    // horario negativo como el de Peru eso puede mostrar el dia
    // anterior al convertir a hora local. Separar el string a mano
    // evita ese corrimiento.
    const [anio, mes, dia] = fecha.split("-");
    return `${parseInt(dia, 10)} ${MESES[parseInt(mes, 10) - 1]} ${anio}`;
  }

  onMount(() => {
    if (!canvasRef) return;

    const ctx = canvasRef.getContext("2d");
    if (!ctx) return;

    const labels = data.map((d) => d.fecha);
    const anomaliaData = data.map((d) => d.anomalia);
    const precursorData = data.map((d) => d.precursor);

    chartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Anomalía Diaria",
            data: anomaliaData,
            borderColor: "#94a3b8",
            backgroundColor: "#94a3b8",
            borderWidth: 1,
            pointRadius: 0,
            tension: 0.1,
          },
          {
            label: "Precursor Oceánico (30 días)",
            data: precursorData,
            borderColor: "#0f172a",
            backgroundColor: "#0f172a",
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.4,
            fill: {
              target: { value: umbral_precursor },
              above: "rgba(239, 68, 68, 0.2)", // Red fill above threshold
              below: "rgba(0,0,0,0)",
            },
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          legend: {
            position: "top",
            labels: {
              font: { family: "'Rethink Sans', sans-serif" },
              usePointStyle: true,
              pointStyle: "line",
              padding: 20,
            },
          },
          tooltip: {
            // enabled: false + external: se apaga el globo
            // flotante de Chart.js y se usa este gancho solo
            // para actualizar 'hoverInfo', que es lo que
            // realmente se pinta (la fila fija de arriba).
            // El 'mode: index' del bloque 'interaction' de
            // arriba sigue aplicando: dispara con el mismo
            // criterio de cercania que antes.
            enabled: false,
            external: (context) => {
              const modelo = context.tooltip;
              const puntos = modelo?.dataPoints;
              if (!modelo || modelo.opacity === 0 || !puntos?.length) {
                hoverInfo = null;
                return;
              }
              hoverInfo = data[puntos[0].dataIndex] ?? null;
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              maxTicksLimit: 8,
              font: { family: "'Rethink Sans', sans-serif" },
            },
          },
          y: {
            grid: { color: "#f1f5f9" },
            border: { display: false },
            // El eje son ANOMALIAS (desviacion respecto a la
            // climatologia), no temperaturas absolutas. Sin el
            // signo, un -0.5 se puede leer como medio grado de
            // agua, que seria absurdo.
            ticks: {
              font: { family: "'Rethink Sans', sans-serif" },
              callback: (v) => `${Number(v) > 0 ? "+" : ""}${v} °C`,
            },
          },
        },
      },
      plugins: [
        {
          id: "thresholdLines",
          // beforeDatasetsDraw, ni beforeDraw ni afterDraw.
          //
          // beforeDraw se probo primero: la cuadricula se dibuja
          // DESPUES y tapaba la linea si coincidia con un tick (le
          // paso al umbral de magnitud, en +2).
          //
          // afterDraw se probo despues para arreglar eso, pero se fue
          // al otro extremo: se dibuja al final, ENCIMA de las curvas
          // de datos y del tooltip. Una linea de referencia no deberia
          // competir visualmente con el dato real ni con el tooltip.
          //
          // beforeDatasetsDraw es el punto intermedio correcto: la
          // cuadricula ya esta pintada (no hay riesgo de que la tape),
          // pero las curvas de anomalia y precursor se dibujan
          // DESPUES de este hook, asi que quedan por encima de la
          // linea de referencia, tal como se espera.
          beforeDatasetsDraw: (chart) => {
            const ctx = chart.ctx;
            const xAxis = chart.scales.x;
            const yAxis = chart.scales.y;

            const yPrecursor = yAxis.getPixelForValue(umbral_precursor);
            const yMagnitud = yAxis.getPixelForValue(umbral_magnitud);
            const yZero = yAxis.getPixelForValue(0);

            ctx.save();
            // Zero line
            ctx.beginPath();
            ctx.moveTo(xAxis.left, yZero);
            ctx.lineTo(xAxis.right, yZero);
            ctx.strokeStyle = "#cbd5e1";
            ctx.lineWidth = 1;
            ctx.stroke();

            // Umbral de ALERTA (persistencia): activa la Etapa 1.
            ctx.beginPath();
            ctx.moveTo(xAxis.left, yPrecursor);
            ctx.lineTo(xAxis.right, yPrecursor);
            ctx.strokeStyle = "#f59e0b";
            ctx.setLineDash([5, 5]);
            ctx.lineWidth = 1;
            ctx.stroke();

            // Umbral de MAGNITUD: pico minimo para escalar a
            // Etapa 2. Punteado mas corto que la linea de alerta,
            // para distinguirla a simple vista, igual que en el
            // backtest (alli es '--' vs ':').
            ctx.beginPath();
            ctx.moveTo(xAxis.left, yMagnitud);
            ctx.lineTo(xAxis.right, yMagnitud);
            ctx.strokeStyle = "#c0392b";
            ctx.setLineDash([2, 3]);
            ctx.lineWidth = 1;
            ctx.stroke();

            ctx.restore();
          },
        },
      ],
    });

    return () => {
      if (chartInstance) chartInstance.destroy();
    };
  });
</script>

<div class="flex flex-col gap-6">
  <!-- Lectura del cursor, en su propia fila y de altura fija. Nunca se
         superpone al grafico porque no vive dentro del canvas: el globo
         flotante que traia Chart.js por defecto ya no se usa. -->
  <div
    class="flex flex-wrap items-center justify-between gap-x-6 gap-y-1 text-sm px-1 min-h-[24px]"
  >
    <span class="text-slate-400 font-medium">
      {hoverInfo
        ? formatFecha(hoverInfo.fecha)
        : "Pase el cursor sobre el gráfico"}
    </span>
    {#if hoverInfo}
      <span class="flex items-center gap-4">
        <span class="text-slate-500">
          Anomalía:
          <strong class="text-slate-800">
            {hoverInfo.anomalia > 0 ? "+" : ""}{hoverInfo.anomalia.toFixed(2)} °C
          </strong>
        </span>
        <span class="text-slate-500">
          Precursor 30d:
          <strong class="text-slate-900">
            {hoverInfo.precursor > 0 ? "+" : ""}{hoverInfo.precursor.toFixed(2)}
            °C
          </strong>
        </span>
      </span>
    {/if}
  </div>

  <div class="w-full h-80 relative">
    <canvas bind:this={canvasRef}></canvas>
  </div>

  <div
    class="flex items-start gap-3 text-sm text-slate-600 bg-slate-50/80 border border-slate-200/60 rounded-xl p-5 shadow-sm"
  >
    <div class="w-2 h-2 rounded-full bg-slate-400 mt-1.5 shrink-0"></div>
    <p class="leading-relaxed">
      <strong class="font-bold text-slate-800">¿Cómo leer este gráfico?</strong>
      La línea gris delgada es la
      <strong class="text-slate-700">anomalía</strong>
      diaria del mar: cuánto se desvía la temperatura respecto a lo normal para
      esa fecha del año, no la temperatura en sí. Es muy volátil y cambia
      bruscamente. Para evitar falsas alarmas, calculamos la línea negra gruesa,
      que es su promedio de los últimos 30 días. El precursor de El Niño Costero
      se activa únicamente cuando esa línea negra supera la marca naranja de
      <strong class="text-amber-600">+{umbral_precursor} °C</strong>
      y se mantiene por encima durante al menos 15 días consecutivos. La línea
      roja punteada, en
      <strong class="text-red-600">+{umbral_magnitud} °C</strong>, es el umbral
      de magnitud: el pico mínimo que necesita el precursor para escalar a la
      segunda etapa de confirmación territorial.
    </p>
  </div>
</div>
