<script lang="ts">
    import type { Snippet } from 'svelte';
    
    let { text, children } = $props<{
        text: string;
        children: Snippet;
    }>();
</script>

<div class="relative group inline-block">
    <!-- Target element to hover over -->
    <div class="cursor-pointer">
        {@render children()}
    </div>
    
    <!-- Tooltip popup -->
    <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-slate-800 text-white text-xs rounded shadow-lg 
                opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50 text-center font-sans">
        {text}
        
        <!-- Arrow pointing down -->
        <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800"></div>
    </div>
</div>
