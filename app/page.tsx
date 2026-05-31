"use client";
import React from 'react';
import { Terminal, Cpu, Layers, Play, CircleCheck, CircleAlert, ChevronRight, Activity, ShieldAlert, GitBranch } from 'lucide-react';

// Importing the actual Shadcn components you installed
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";

// 1. Pulled log text out of JSX to avoid template indentation & parsing bugs
const LOG_DATA = `[Node-01] [Storage Layer] Write isolation level verified. 
[Node-02] [Network Layer] Simulated latency drop injected: +45ms.
[Node-03] [Guest Logic] Replicating deterministic network frame...

> Status: 100% Chaos Proof`;

export default function EngineDashboard() {
  return (
    <div className="flex h-screen w-screen bg-background text-foreground antialiased overflow-hidden text-sm">
      
      {/* 1. LEFT PANEL: Framework View */}
      <aside className="w-64 border-r border-border bg-card flex flex-col justify-between">
        <div>
          <div className="h-14 flex items-center px-4 border-b border-border gap-2">
            <Cpu className="w-4 h-4 text-emerald-500 animate-pulse" />
            <span className="font-mono text-xs font-bold tracking-widest">AGENT_NATIVE</span>
          </div>
          
          <div className="p-4 space-y-6">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold mb-3">Simulation Targets</div>
              <div className="space-y-2">
                <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-muted/50 border border-border/50 text-xs">
                  <span className="font-bold text-emerald-500">GO</span>
                  <span className="text-muted-foreground">orchestrator-go</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-muted/50 border border-border/50 text-xs">
                  <span className="font-bold text-blue-500">C++</span>
                  <span className="text-muted-foreground">engine-cpp (Core)</span>
                </div>
              </div>
            </div>

            <div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold mb-3">Systems Management</div>
              <nav className="space-y-1 font-mono text-xs">
                <Button variant="secondary" className="w-full justify-start gap-2 h-8 px-2 text-xs">
                  <Layers className="w-3.5 h-3.5 text-emerald-500" />
                  Discrete Canvas
                </Button>
                <Button variant="ghost" className="w-full justify-start gap-2 h-8 px-2 text-xs text-muted-foreground">
                  <GitBranch className="w-3.5 h-3.5" />
                  gRPC API Layer
                </Button>
              </nav>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-border bg-muted/20 font-mono text-xs">
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span>Seed:</span>
            <span className="text-foreground">0x7F4A9B</span>
          </div>
          <div className="flex items-center gap-1.5 text-emerald-500 text-[11px] font-medium">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Verification Active
          </div>
        </div>
      </aside>

      {/* 2. CENTER CANVAS: State Tree Visualizer */}
      <main className="flex-1 flex flex-col overflow-hidden bg-background">
        <header className="h-14 border-b border-border flex items-center justify-between px-6 bg-card/50">
          <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
            <span>Simulation Run</span>
            <ChevronRight className="w-3 h-3 text-border" />
            <span className="text-foreground">guest_node_cluster_01</span>
          </div>
          <Button size="sm" className="h-8 gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white shadow-none">
            <Play className="w-3 h-3 fill-current" /> Inject Chaos
          </Button>
        </header>

        <ScrollArea className="flex-1 p-6">
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 border border-border bg-card rounded-lg shadow-sm">
                <div className="text-muted-foreground text-xs mb-1 font-mono">Virtualized CPU State</div>
                <div className="text-xl font-mono tracking-tight">0.024ms / Event Tick</div>
              </div>
              <div className="p-4 border border-border bg-card rounded-lg shadow-sm">
                <div className="text-muted-foreground text-xs mb-1 font-mono">Invariant Errors</div>
                <div className="text-xl font-mono text-amber-500 tracking-tight">0 Detected</div>
              </div>
            </div>

            <div className="rounded-lg border border-border bg-card shadow-sm overflow-hidden">
              <div className="flex items-center justify-between p-3 border-b border-border bg-muted/30">
                <span className="flex items-center gap-2 text-xs font-mono font-medium">
                  <Activity className="w-3.5 h-3.5 text-blue-500" /> 
                  Distributed Node Invariant Matrix
                </span>
                <span className="text-[10px] text-muted-foreground font-mono">Protocol v1</span>
              </div>
              <div className="p-4 bg-zinc-950">
                {/* 2. Rendered clean layout data without break-spacing */}
                <pre className="font-mono text-xs text-zinc-400 leading-relaxed overflow-x-auto whitespace-pre-wrap">
                  {LOG_DATA}
                </pre>
              </div>
            </div>
          </div>
        </ScrollArea>
      </main>

      {/* 3. RIGHT PANEL: Live Trajectory Log */}
      <section className="w-80 border-l border-border bg-card flex flex-col justify-between overflow-hidden">
        <div className="h-14 flex items-center px-4 border-b border-border bg-card/50">
          <h3 className="text-xs font-mono font-bold text-muted-foreground tracking-wider">EVENT STREAM</h3>
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-3 font-mono text-[11px]">
            <div className="p-3 rounded-md bg-muted/50 border border-border flex gap-2.5">
              <CircleCheck className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <span className="text-foreground block font-semibold">driver::init_discrete_event()</span>
                <span className="text-muted-foreground block leading-tight">Timeline synchronized to seed baseline.</span>
              </div>
            </div>

            <div className="p-3 rounded-md bg-amber-500/10 border border-amber-500/20 flex gap-2.5">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <span className="text-amber-500 block font-semibold">chaos::network_partition()</span>
                <span className="text-amber-500/80 block leading-tight">Evaluating message drop tolerance...</span>
              </div>
            </div>
          </div>
        </ScrollArea>

        <div className="p-4 border-t border-border bg-card">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground font-mono text-xs">$</span>
            <Input 
              type="text" 
              placeholder="inject_fault --node 2" 
              className="pl-7 h-9 font-mono text-xs bg-muted/50 border-border focus-visible:ring-1 focus-visible:ring-emerald-500 shadow-none"
            />
          </div>
        </div>
      </section>

    </div>
  );
}