<script lang="ts">
    import DashboardContainer from '$lib/components/DashboardContainer.svelte';
</script>

<svelte:head>
    <title>Backtest Histórico — Pulso</title>
</svelte:head>

<div class="max-w-6xl mx-auto mt-4 px-4 sm:px-6 lg:px-8 py-8">
    <header class="mb-10">
        <h1 class="text-4xl font-bold font-slab text-slate-900 tracking-tight mb-3">Backtest y Validación</h1>
        <p class="text-slate-500 max-w-3xl text-[15px] leading-relaxed">
            Análisis retrospectivo del sistema de alerta frente a los grandes episodios del pasado (Niño 1982, 1997, 2017 y 2023).
        </p>
    </header>

    <div class="grid grid-cols-1 gap-8">
        <DashboardContainer 
            titulo="El Niño Costero 2017" 
            subtitulo="Desborde del Río Piura, 27 de marzo (3,468 m³/s)"
        >
            <div class="p-6">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <!-- Metric Card 1: Regla ICEN -->
                    <div class="bg-white p-5 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 relative overflow-hidden group hover:shadow-md transition-shadow">
                        <div class="absolute left-0 top-0 bottom-0 w-1.5 bg-slate-400"></div>
                        <div class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2 pl-2">Regla ICEN (3 meses)</div>
                        <div class="text-3xl font-oswald font-bold text-slate-800 mb-2 pl-2">−5 días</div>
                        <div class="text-[13px] text-slate-500 pl-2 leading-relaxed">El índice de DIAGNÓSTICO habría llegado tarde.</div>
                    </div>

                    <!-- Metric Card 2: Pulso -->
                    <div class="bg-white p-5 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 relative overflow-hidden group hover:shadow-md transition-shadow">
                        <div class="absolute left-0 top-0 bottom-0 w-1.5 bg-amber-500"></div>
                        <div class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2 pl-2">Precursor Diario Pulso</div>
                        <div class="text-3xl font-oswald font-bold text-slate-800 mb-2 pl-2">+68 días</div>
                        <div class="text-[13px] text-slate-500 pl-2 leading-relaxed">Etapa 1 · alerta temprana el 18-ene-2017.</div>
                    </div>

                    <!-- Metric Card 3: Confirmación -->
                    <div class="bg-white p-5 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] border border-slate-200/60 relative overflow-hidden group hover:shadow-md transition-shadow">
                        <div class="absolute left-0 top-0 bottom-0 w-1.5 bg-red-500"></div>
                        <div class="text-[11px] font-bold tracking-widest text-slate-500 uppercase mb-2 pl-2">Confirmación Territorial</div>
                        <div class="text-3xl font-oswald font-bold text-slate-800 mb-2 pl-2">+26 días</div>
                        <div class="text-[13px] text-slate-500 pl-2 leading-relaxed">Etapa 2 · compuesto de feb-2017, disponible el 1-marzo.</div>
                    </div>
                </div>

                <!-- Info Block -->
                <div class="flex items-start bg-slate-50/50 p-5 rounded-2xl border border-slate-100 mb-10">
                    <div class="text-slate-400 mr-4 mt-0.5">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    </div>
                    <div class="text-[14px] text-slate-600 leading-relaxed">
                        <span class="font-semibold text-slate-800">Esta comparación no es contra el ENFEN.</span> El ICEN es un índice de DIAGNÓSTICO: sirve para declarar oficialmente que hubo un Niño costero, no para alertar de forma temprana. Lo que Pulso demuestra aquí es que la alta cadencia (diaria) recupera semanas vitales, pero el hallazgo central del proyecto está en la Etapa 2.
                    </div>
                </div>

                <!-- Text Content -->
                <div class="max-w-4xl">
                    <h3 class="font-slab font-bold text-2xl text-slate-900 mb-4 tracking-tight">Por qué la anomalía oceánica no basta</h3>
                    <p class="text-slate-600 text-[15px] mb-8 leading-relaxed">
                        El Niño de 2015-16 calentó <strong class="text-slate-800 font-semibold">MÁS</strong> el mar que el de 2017, pero no causó desastre en la costa. El ICEN oficial lo clasificó como FUERTE (2.17), mientras que a 2017 lo clasificó como MODERADO (1.38). Ningún indicador puramente oceánico distingue un Niño costero de uno inofensivo. La confirmación territorial, sí.
                    </p>
                </div>

                <!-- Image -->
                <div class="rounded-2xl overflow-hidden border border-slate-200/80 shadow-sm bg-white">
                    <img 
                        src="http://127.0.0.1:8000/static/mapas/5_dos_etapas_2015_vs_2017.png" 
                        alt="Comparación 2015 vs 2017" 
                        class="w-full h-auto"
                        loading="lazy"
                        onerror={(e) => (e.currentTarget as HTMLElement).style.display = 'none'}
                    />
                </div>
                
                <!-- Footer Note -->
                <div class="mt-8 text-[12px] text-slate-400 leading-relaxed">
                    La Etapa 2 solo pudo probarse sobre DOS eventos (2017 y 2023): Landsat 8 inicia operaciones en 2013, de modo que 1983 y 1998 quedan fuera de su alcance. Lo declaramos abiertamente: esto es una prueba de concepto, no una validación estadística robusta aún. Lo defendible es el margen — los no-desastres alcanzan z = 1.36 y los desastres arrancan en z = 3.34, sin solape.
                </div>
            </div>
        </DashboardContainer>
    </div>
</div>
