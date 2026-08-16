<script lang="ts">
    import { onMount } from 'svelte';
    import Chart from 'chart.js/auto';

    let { data, umbral_precursor, umbral_magnitud = 0.4 } = $props<{
        data: Array<{ fecha: string, anomalia: number, precursor: number }>;
        umbral_precursor: number;
        umbral_magnitud?: number;
    }>();

    let canvasRef: HTMLCanvasElement;
    let chartInstance: Chart | null = null;

    onMount(() => {
        if (!canvasRef) return;

        const ctx = canvasRef.getContext('2d');
        if (!ctx) return;

        const labels = data.map(d => d.fecha);
        const anomaliaData = data.map(d => d.anomalia);
        const precursorData = data.map(d => d.precursor);

        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Anomalía Diaria',
                        data: anomaliaData,
                        borderColor: '#94a3b8',
                        backgroundColor: '#94a3b8',
                        borderWidth: 1,
                        pointRadius: 0,
                        tension: 0.1
                    },
                    {
                        label: 'Precursor Oceánico',
                        data: precursorData,
                        borderColor: '#0f172a',
                        backgroundColor: '#0f172a',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4,
                        fill: {
                            target: { value: umbral_precursor },
                            above: 'rgba(239, 68, 68, 0.2)', // Red fill above threshold
                            below: 'rgba(0,0,0,0)'
                        }
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            font: { family: "'Rethink Sans', sans-serif" },
                            usePointStyle: true,
                            pointStyle: 'line',
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleFont: { family: "'Rethink Sans', sans-serif", size: 14 },
                        bodyFont: { family: "'Rethink Sans', sans-serif", size: 13 },
                        padding: 12,
                        cornerRadius: 8,
                        usePointStyle: true,
                        boxPadding: 6
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { maxTicksLimit: 8, font: { family: "'Rethink Sans', sans-serif" } }
                    },
                    y: {
                        grid: { color: '#f1f5f9' },
                        border: { display: false },
                        ticks: { font: { family: "'Rethink Sans', sans-serif" } }
                    }
                }
            },
            plugins: [{
                id: 'thresholdLines',
                beforeDraw: (chart) => {
                    const ctx = chart.ctx;
                    const xAxis = chart.scales.x;
                    const yAxis = chart.scales.y;
                    
                    const yPrecursor = yAxis.getPixelForValue(umbral_precursor);
                    const yZero = yAxis.getPixelForValue(0);

                    ctx.save();
                    // Zero line
                    ctx.beginPath();
                    ctx.moveTo(xAxis.left, yZero);
                    ctx.lineTo(xAxis.right, yZero);
                    ctx.strokeStyle = '#cbd5e1';
                    ctx.lineWidth = 1;
                    ctx.stroke();

                    // Threshold Precursor
                    ctx.beginPath();
                    ctx.moveTo(xAxis.left, yPrecursor);
                    ctx.lineTo(xAxis.right, yPrecursor);
                    ctx.strokeStyle = '#f59e0b';
                    ctx.setLineDash([5, 5]);
                    ctx.lineWidth = 1;
                    ctx.stroke();
                    ctx.restore();
                }
            }]
        });

        return () => {
            if (chartInstance) chartInstance.destroy();
        };
    });
</script>

<div class="flex flex-col gap-6">
    <div class="w-full h-80 relative">
        <canvas bind:this={canvasRef}></canvas>
    </div>
    
    <div class="flex items-start gap-3 text-sm text-slate-600 bg-slate-50/80 border border-slate-200/60 rounded-xl p-5 shadow-sm">
        <div class="w-2 h-2 rounded-full bg-slate-400 mt-1.5 shrink-0"></div>
        <p class="leading-relaxed">
            <strong class="font-bold text-slate-800">¿Cómo leer este gráfico?</strong> 
            La línea azul delgada representa la temperatura diaria del mar, la cual es muy volátil y cambia bruscamente. Para evitar falsas alarmas, calculamos la línea negra gruesa, que representa un promedio estabilizado. 
            El precursor de El Niño Costero se activa únicamente cuando esta línea negra logra superar la marca naranja de <strong class="text-amber-600">+{umbral_precursor} °C</strong> y se mantiene por encima durante al menos 15 días consecutivos.
        </p>
    </div>
</div>
