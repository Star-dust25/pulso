<script lang="ts">
  import type { Snippet } from "svelte";
  import Tooltip from "./Tooltip.svelte";

  let {
    titulo,
    subtitulo = "",
    tooltip = "",
    children,
  } = $props<{
    titulo: string;
    subtitulo?: string;
    tooltip?: string;
    children?: Snippet;
  }>();
</script>

<div
  class="border border-slate-100/80 rounded-2xl bg-white/70 backdrop-blur-xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] mb-8 transition-shadow hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)]"
>
  <!-- Header -->
  <div
    class="border-b border-slate-100 px-4 sm:px-8 py-6 sm:py-8 bg-gradient-to-b from-slate-50/50 to-white/50 rounded-t-2xl"
  >
    <div class="flex items-start sm:items-center">
      <span
        class="font-slab text-xl md:text-3xl font-bold text-slate-900 tracking-tight mb-2 sm:mb-0"
      >
        {titulo}
      </span>
      {#if tooltip}
        <div class="ml-4 mt-2 sm:mt-0">
          <Tooltip text={tooltip}>
            <div
              class="w-6 h-6 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center font-sans font-bold text-sm hover:bg-slate-200 hover:text-slate-600 transition-colors cursor-help"
            >
              ?
            </div>
          </Tooltip>
        </div>
      {/if}
    </div>
    {#if subtitulo}
      <div
        class="text-xl text-slate-600 mt-4 font-light leading-relaxed max-w-4xl"
      >
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
