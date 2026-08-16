<script lang="ts">
  import "./layout.css";
  import { page } from "$app/stores";
  import type { Snippet } from "svelte";

  let { children } = $props<{ children: Snippet }>();

  // Navigation routes
  const navItems = [
    { path: "/", label: "Resumen" },
    { path: "/monitoreo", label: "Monitoreo Satelital" },
    { path: "/backtest", label: "Backtest" },
    { path: "/impacto", label: "Matriz de Impacto" },
  ];
</script>

<div
  class="min-h-screen flex flex-col bg-[#F8FAFC] font-sans selection:bg-amber-100 selection:text-amber-900"
>
  <!-- Navbar -->
  <nav class="bg-white/80 backdrop-blur-lg border-b border-slate-200/60 sticky top-0 z-50 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <!-- Logo -->
        <div class="flex-shrink-0 flex items-center gap-2">
          <span
            class="font-slab font-bold text-5xl tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-slate-900 via-slate-800 to-slate-600"
            >Pulso.</span
          >
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
              <span class="absolute bottom-2 left-0 w-full h-[2.5px] rounded-full transform origin-left transition-transform duration-300 ease-out
                {$page.url.pathname === item.path ? 'bg-red-500 scale-x-100' : 'bg-slate-300 scale-x-0 group-hover:scale-x-100'}"></span>
            </a>
          {/each}
        </div>
      </div>
    </div>
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
          <div
            class="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full border border-slate-200 shadow-sm mb-1"
          >
            <span class="relative flex h-2 w-2">
              <span
                class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"
              ></span>
              <span
                class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"
              ></span>
            </span>
            <span class="text-xs font-semibold tracking-wide"
              >Motores Activos</span
            >
          </div>
          <p class="mt-1 text-slate-400">Desarrollado para el Perú.</p>
        </div>
      </div>
    </div>
  </footer>
</div>
