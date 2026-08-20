<script lang="ts">
  import "./layout.css";
  import { page } from "$app/stores";
  import { fly } from "svelte/transition";
  import type { Snippet } from "svelte";

  let { children } = $props<{ children: Snippet }>();

  let isMobileMenuOpen = $state(false);

  $effect(() => {
    // Cerrar el menú al cambiar de ruta
    $page.url.pathname;
    isMobileMenuOpen = false;
  });

  // Navigation routes
  const navItems = [
    { path: "/", label: "Resumen" },
    { path: "/monitoreo", label: "Monitoreo Satelital" },
    { path: "/backtest", label: "Backtest" },
    { path: "/impacto", label: "Validación" },
  ];
</script>

<div
  class="min-h-screen flex flex-col bg-[#F8FAFC] font-sans selection:bg-amber-100 selection:text-amber-900 overflow-x-hidden"
>
  <!-- Navbar -->
  <nav
    class="bg-white/80 backdrop-blur-lg border-b border-slate-200/60 sticky top-0 z-50 shadow-sm"
  >
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <!-- Logo -->
        <div class="flex-shrink-0 flex items-center gap-2">
          <span
            class="font-slab font-bold text-5xl tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-slate-900 via-slate-800 to-slate-600"
            >Pulso.</span
          >
        </div>

        <!-- Mobile Menu Button -->
        <div class="flex items-center sm:hidden">
          <button
            type="button"
            class="inline-flex items-center justify-center p-2 rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-red-500 transition-colors"
            onclick={() => isMobileMenuOpen = !isMobileMenuOpen}
            aria-expanded={isMobileMenuOpen}
          >
            <span class="sr-only">Open main menu</span>
            {#if isMobileMenuOpen}
              <svg class="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            {:else}
              <svg class="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            {/if}
          </button>
        </div>

        <!-- Desktop Nav -->
        <div class="hidden sm:flex sm:space-x-8">
          {#each navItems as item}
            <a
              href={item.path}
              class="relative inline-flex items-center px-2 py-2 text-lg font-medium transition-colors group
                                {$page.url.pathname === item.path
                ? 'text-red-600'
                : 'text-slate-500 hover:text-slate-900'}"
            >
              {item.label}
              <!-- Animated Bottom Line Indicator -->
              <span
                class="absolute bottom-2 left-0 w-full h-[2.5px] rounded-full transform origin-left transition-transform duration-300 ease-out
                {$page.url.pathname === item.path
                  ? 'bg-red-500 scale-x-100'
                  : 'bg-slate-300 scale-x-0 group-hover:scale-x-100'}"
              ></span>
            </a>
          {/each}
        </div>
      </div>
    </div>

    <!-- Mobile Menu Panel -->
    {#if isMobileMenuOpen}
      <div 
        class="sm:hidden border-t border-slate-200 bg-white/95 backdrop-blur-lg absolute w-full z-40 shadow-lg"
        transition:fly={{ y: -10, duration: 200 }}
      >
        <div class="px-4 pt-2 pb-4 space-y-1">
          {#each navItems as item}
            <a
              href={item.path}
              class="block px-3 py-3 rounded-md text-base font-medium transition-colors
                {$page.url.pathname === item.path
                ? 'bg-red-50 text-red-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}"
              onclick={() => isMobileMenuOpen = false}
            >
              {item.label}
            </a>
          {/each}
        </div>
      </div>
    {/if}
  </nav>

  <!-- Main Content -->
  <main class="flex-grow">
    {@render children()}
  </main>

  <!-- Footer -->
  <footer class="bg-slate-50 border-t border-slate-200 mt-16 py-12">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <div
        class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6"
      >
        <div>
          <span
            class="font-slab font-bold text-2xl tracking-tight text-slate-800"
            >Pulso</span
          >
          <p
            class="text-sm text-slate-500 mt-2 max-w-md leading-relaxed font-light"
          >
            Sistema satelital de Alerta Temprana ante El Niño Costero. Monitoreo
            acoplado del precursor térmico oceánico y confirmación territorial.
          </p>
        </div>

        <div class="flex flex-col md:items-end text-sm text-slate-500 gap-1">
          <p
            class="text-xs text-slate-500 md:text-right max-w-xs leading-relaxed"
          >
            Datos: NOAA OISST v2.1 · USGS Landsat 8 · Mapa Regional de
            Ecosistemas de Piura (GORE Piura, O.R. 492-2023) · INDECI (SINPAD)
          </p>
          <p
            class="text-xs text-slate-400 md:text-right max-w-xs leading-relaxed"
          >
            Categorías del ICEN según ENFEN (2024), Nota Técnica 01-2024.
          </p>
          <p class="mt-2 text-slate-400">Desarrollado para el Perú.</p>
        </div>
      </div>
    </div>
  </footer>
</div>
