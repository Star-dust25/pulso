<script lang="ts">
  import { onMount } from "svelte";
  import Chart from "chart.js/auto";

  let { data, umbral_msavi } = $props<{
    data: Array<{ mes: string; z_msavi: number | null }>;
    umbral_msavi: number;
  }>();

  let canvasRef: HTMLCanvasElement;
  let chartInstance: Chart | null = null;

  // Meses en español, abreviados, para que el eje coincida con el estilo
  // que ya usan los graficos del backtest (Mar-15, May-15, etc).
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

  function etiquetaMes(mes: string): string {
    // mes viene como 'YYYY-MM'
    const [anio, m] = mes.split("-");
    const nombre = MESES[parseInt(m, 10) - 1];
    return `${nombre}-${anio.slice(2)}`;
  }

  onMount(() => {
    if (!canvasRef) return;

    const ctx = canvasRef.getContext("2d");
    if (!ctx) return;

    const labels = data.map((d) => etiquetaMes(d.mes));
    const valores = data.map((d) => d.z_msavi);

    // Un color por barra segun si confirma o no. Los valores null
    // (meses futuros o sin escenas utiles) no generan barra: Chart.js
    // salta la categoria en un grafico de barras cuando el dato es null.
    const colores = valores.map((v) =>
      v === null ? "rgba(0,0,0,0)" : v >= umbral_msavi ? "#c0392b" : "#94a3b8",
    );

    // El eje Y DEBE incluir siempre el umbral, o su linea se dibuja
    // fuera del area visible sin ningun aviso.
    //
    // Chart.js autoescala el eje al rango de los datos que recibe. Si
    // ningun mes reciente se acerca a +1.5 (el caso normal, porque la
    // Etapa 2 rara vez confirma), el eje se ajusta a algo como -0.4 a
    // 1.0 y la linea del umbral queda por encima del borde superior:
    // no desaparece por un error, simplemente cae fuera del lienzo.
    //
    // La correccion es fijar el maximo del eje por encima del umbral,
    // con margen, y dejar que crezca mas alla si algun mes lo supera.
    const valoresValidos = valores.filter((v): v is number => v !== null);
    const maxDatos = valoresValidos.length ? Math.max(...valoresValidos) : 0;
    const minDatos = valoresValidos.length ? Math.min(...valoresValidos) : 0;

    const yMax = Math.max(maxDatos, umbral_msavi) + 0.5;
    const yMin = Math.min(minDatos, 0) - 0.3;

    chartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "z(MSAVI)",
            data: valores,
            backgroundColor: colores,
            borderRadius: 3,
            maxBarThickness: 28,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(15, 23, 42, 0.9)",
            titleFont: { family: "'Rethink Sans', sans-serif", size: 14 },
            bodyFont: { family: "'Rethink Sans', sans-serif", size: 13 },
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              label: (item) => {
                const v = item.raw as number | null;
                if (v === null) return "Sin dato";
                const estado = v >= umbral_msavi ? "Confirma" : "No confirma";
                return `z = ${v.toFixed(2)} · ${estado}`;
              },
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              font: { family: "'Rethink Sans', sans-serif", size: 11 },
              maxRotation: 0,
              autoSkip: true,
              maxTicksLimit: 10,
            },
          },
          y: {
            // suggestedMax/suggestedMin en vez de max/min fijos:
            // si un mes futuro supera el margen calculado, el
            // eje puede seguir creciendo en vez de recortar la
            // barra.
            suggestedMax: yMax,
            suggestedMin: yMin,
            grid: { color: "#f1f5f9" },
            border: { display: false },
            ticks: { font: { family: "'Rethink Sans', sans-serif" } },
          },
        },
      },
      plugins: [
        {
          id: "umbralLine",
          // beforeDatasetsDraw: la cuadricula ya esta pintada aqui
          // (evita el bug de la linea tapada por un tick), y las
          // barras se dibujan DESPUES de este hook, asi que quedan
          // por encima de la linea de referencia en vez de que la
          // linea se superponga a las barras. Ver la nota extendida
          // en EvolutionChart.svelte, que tuvo el mismo ajuste.
          beforeDatasetsDraw: (chart) => {
            const ctx = chart.ctx;
            const xAxis = chart.scales.x;
            const yAxis = chart.scales.y;

            const yUmbral = yAxis.getPixelForValue(umbral_msavi);
            const yZero = yAxis.getPixelForValue(0);

            ctx.save();

            // Linea de cero, para leer las barras negativas.
            ctx.beginPath();
            ctx.moveTo(xAxis.left, yZero);
            ctx.lineTo(xAxis.right, yZero);
            ctx.strokeStyle = "#cbd5e1";
            ctx.lineWidth = 1;
            ctx.stroke();

            // Umbral de confirmacion. Solo se dibuja si cae dentro
            // del area visible: aunque el calculo de yMax deberia
            // garantizarlo siempre, esta guarda evita una linea
            // fantasma si en el futuro se cambia el margen.
            //
            // OJO: la guarda debe compararse contra chart.chartArea,
            // no contra xAxis.top/bottom. Para un eje de categorias
            // (el eje X), esas propiedades NO representan el borde
            // superior del area de trazado, asi que la comparacion
            // fallaba siempre y la linea nunca llegaba a dibujarse,
            // aunque el eje Y si tenia el rango correcto.
            const { top, bottom } = chart.chartArea;
            if (yUmbral >= top && yUmbral <= bottom) {
              ctx.beginPath();
              ctx.moveTo(xAxis.left, yUmbral);
              ctx.lineTo(xAxis.right, yUmbral);
              ctx.strokeStyle = "#c0392b";
              ctx.setLineDash([5, 5]);
              ctx.lineWidth = 1;
              ctx.stroke();
            }

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
  <div class="w-full h-72 relative">
    <canvas bind:this={canvasRef}></canvas>
  </div>

  <div
    class="flex items-start gap-3 text-sm text-slate-600 bg-slate-50/80 border border-slate-200/60 rounded-xl p-5 shadow-sm"
  >
    <div class="w-2 h-2 rounded-full bg-slate-400 mt-1.5 shrink-0"></div>
    <p class="leading-relaxed">
      <strong class="font-bold text-slate-800">¿Cómo leer este gráfico?</strong>
      Cada barra es el compuesto satelital mensual del bosque seco, expresado como
      anomalía z(MSAVI). Las barras rojas alcanzan o superan el umbral de confirmación
      de <strong class="text-red-600">+{umbral_msavi}</strong>; las grises
      quedan por debajo. Los meses sin barra todavía no han ocurrido o no
      cuentan con suficientes escenas satelitales libres de nubes.
    </p>
  </div>
</div>
