<script lang="ts">
    import type { Snippet } from 'svelte';
    import Tooltip from './Tooltip.svelte';
    
    let { titulo, subtitulo = '', tooltip = '', children } = $props<{
        titulo: string;
        subtitulo?: string;
        tooltip?: string;
        children?: Snippet;
    }>();
</script>

<div class="border border-slate-100/80 rounded-2xl bg-white/70 backdrop-blur-xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] mb-8 transition-shadow hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)]">
    <!-- Header -->
    <div class="border-b border-slate-100 px-4 sm:px-6 py-4 sm:py-5 bg-gradient-to-b from-slate-50/50 to-white/50 rounded-t-2xl">
        <div class="flex items-center">
            <span class="font-slab text-2xl font-bold text-slate-800 tracking-tight">
                {titulo}
            </span>
            {#if tooltip}
                <div class="ml-3">
                    <Tooltip text={tooltip}>
                        <div class="w-5 h-5 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center font-sans font-bold text-xs hover:bg-slate-200 hover:text-slate-600 transition-colors">
                            ?
                        </div>
                    </Tooltip>
                </div>
            {/if}
        </div>
        {#if subtitulo}
            <div class="text-[15px] text-slate-500 mt-2 font-sans leading-relaxed max-w-3xl">
                {subtitulo}
            </div>
        {/if}
    </div>
    
    <!-- Body -->
    <div class="p-4 sm:p-6">
        {#if children}
            {@render children()}
        {/if}
    </div>
</div>
