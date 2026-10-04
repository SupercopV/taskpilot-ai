import React from 'react';
import { Play, RefreshCw, AlertTriangle, ShieldAlert } from 'lucide-react';

export default function DemoScenarios({ onSelectScenario, isRunning }) {
  const scenarios = [
    {
      id: 1,
      title: "Scenario 1: Autonomous Ingestion",
      tag: "Standard Flow",
      tagColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      description: "Find latest Acme Corp invoice, extract amount/date, enter into ERP, and verify ledger record.",
      prompt: "Find the latest invoice from Acme Corp, extract the invoice amount and due date, enter it into the finance system, and verify that it was successfully recorded.",
      simulateFailure: false,
      icon: Play
    },
    {
      id: 2,
      title: "Scenario 2: Failure & Recovery Demo",
      tag: "Self-Healing Loop",
      tagColor: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      description: "Intentional 1st submission validation error. Agent observes failure, logs diagnosis, retries, and verifies.",
      prompt: "Process the latest invoice from Acme Corp and verify completion.",
      simulateFailure: true,
      icon: RefreshCw
    },
    {
      id: 3,
      title: "Scenario 3: Human-in-the-Loop Governance",
      tag: "High Value (> ₹100k)",
      tagColor: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
      description: "Enterprise invoice is ₹125,000. Agent pauses, requests human authorization, and waits for user approval.",
      prompt: "Process the latest invoice from Enterprise Corp and verify ledger recording.",
      simulateFailure: false,
      icon: ShieldAlert
    }
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Evaluator Demo Scenarios
        </h3>
        <span className="text-[11px] text-slate-500">Click to load & run technical scenario</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {scenarios.map((sc) => {
          const Icon = sc.icon;
          return (
            <button
              key={sc.id}
              disabled={isRunning}
              onClick={() => onSelectScenario(sc.prompt, sc.simulateFailure)}
              className="text-left p-3.5 rounded-xl bg-slate-900/60 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 transition duration-150 group disabled:opacity-50 disabled:cursor-not-allowed flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${sc.tagColor}`}>
                    {sc.tag}
                  </span>
                  <Icon className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 transition" />
                </div>
                <h4 className="text-xs font-bold text-white group-hover:text-emerald-300 transition">
                  {sc.title}
                </h4>
                <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                  {sc.description}
                </p>
              </div>
              <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-medium text-emerald-400 group-hover:text-emerald-300">
                <span>Load Scenario {sc.id}</span>
                <span className="text-slate-500 group-hover:translate-x-0.5 transition">→</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
