<script lang="ts">
    let { valor, minVal, maxVal, umbral, titulo, valorTexto, subtitulo, colores = [] } = $props<{
        valor: number;
        minVal: number;
        maxVal: number;
        umbral: number;
        titulo: string;
        valorTexto: string;
        subtitulo: string;
        colores?: Array<[number, number, string, string]>;
    }>();

    // Math for SVG
    let v_clamp = $derived(Math.max(minVal, Math.min(maxVal, valor)));
    let porcentaje = $derived((v_clamp - minVal) / (maxVal - minVal));
    let angulo = $derived(180 - (porcentaje * 180));

    const cx = 150, cy = 120, radio = 100, grosor = 35;

    function polarToCartesian(cx: number, cy: number, r: number, angleInDegrees: number) {
        var angleInRadians = (angleInDegrees * Math.PI) / 180.0;
        return {
            x: cx + r * Math.cos(angleInRadians),
            y: cy - r * Math.sin(angleInRadians)
        };
    }

    // Generate arcs
    let arcos = $derived(colores.map(([v_ini, v_fin, col, nombre]) => {
        let p_ini = Math.max(0.0, Math.min(1.0, (v_ini - minVal) / (maxVal - minVal)));
        let p_fin = Math.max(0.0, Math.min(1.0, (v_fin - minVal) / (maxVal - minVal)));
        if (p_ini === p_fin) return null;

        let a_ini = 180 - (p_ini * 180);
        let a_fin = 180 - (p_fin * 180);

        let start = polarToCartesian(cx, cy, radio, a_ini);
        let end = polarToCartesian(cx, cy, radio, a_fin);
        
        // svg arc flag
        let d = `M ${start.x} ${start.y} A ${radio} ${radio} 0 0 1 ${end.x} ${end.y}`;
        
        let a_medio = 180 - ((p_ini + p_fin)/2 * 180);
        let mid = polarToCartesian(cx, cy, radio + grosor/2 + 10, a_medio);

        return { d, col, nombre, mid };
    }).filter(Boolean));

    let aguja = $derived.by(() => {
        let tip = polarToCartesian(cx, cy, radio - 5, angulo);
        let left = polarToCartesian(cx, cy, 5, angulo + 90);
        let right = polarToCartesian(cx, cy, 5, angulo - 90);
        return `${left.x},${left.y} ${tip.x},${tip.y} ${right.x},${right.y}`;
    });
</script>

<div class="text-center py-2 flex-1">
    <svg viewBox="0 0 300 160" class="w-full max-w-[300px] mx-auto h-[200px]">
        {#each arcos as arco}
            {#if arco}
            <path d={arco.d} fill="none" stroke={arco.col} stroke-width={grosor} />
            <text x={arco.mid.x} y={arco.mid.y} text-anchor="middle" dominant-baseline="middle" class="font-sans text-[10px] fill-gray-500">{arco.nombre}</text>
            {/if}
        {/each}
        
        <polygon points={aguja} fill="#1F2937" />
        <circle {cx} {cy} r="6" fill="#1F2937" />

        <text x={cx} y={cy + 25} text-anchor="middle" class="font-sans font-bold text-xl fill-gray-900">{valorTexto}</text>
        <text x={cx} y={cy + 40} text-anchor="middle" class="font-sans font-medium text-xs fill-gray-500">{titulo}</text>
    </svg>
    <div class="text-[13px] text-gray-500 mt-2 leading-relaxed">
        {@html subtitulo}
    </div>
</div>
