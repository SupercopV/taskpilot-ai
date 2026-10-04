import React from 'react';
import { Send, Sparkles, RefreshCw, AlertCircle } from 'lucide-react';

export default function TaskInput({ 
  goal, 
  setGoal, 
  simulateFailure, 
  setSimulateFailure, 
  onSubmit, 
  isRunning,
  error 
}) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!goal.trim() || isRunning) return;
    onSubmit();
  };

  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span>Assign Business Objective to Autonomous Worker</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Describe the goal in natural language. TaskPilot AI will plan, execute tools, observe, and verify results.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <textarea
            rows={3}
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            disabled={isRunning}
            placeholder="What would you like me to do? (e.g. Find the latest invoice from Acme Corp, extract the invoice amount and due date, enter it into the finance system, and verify that it was successfully recorded.)"
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl p-3.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 disabled:opacity-50 transition duration-150 resize-none font-sans"
          />
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
          {/* Failure Simulation Demo Toggle */}
          <label className="flex items-center space-x-2.5 text-xs text-slate-300 select-none cursor-pointer group">
            <input
              type="checkbox"
              checked={simulateFailure}
              onChange={(e) => setSimulateFailure(e.target.checked)}
              disabled={isRunning}
              className="w-4 h-4 rounded text-emerald-500 focus:ring-emerald-500 bg-slate-950 border-slate-700 cursor-pointer"
            />
            <span className="text-slate-400 group-hover:text-slate-200 transition">
              Simulate 1st-attempt validation error <strong className="text-amber-400 font-semibold">(Failure Recovery Demo)</strong>
            </span>
          </label>

          {/* Submit Run Button */}
          <button
            type="submit"
            disabled={isRunning || !goal.trim()}
            className="px-6 py-2.5 rounded-xl font-semibold text-xs text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 active:from-emerald-700 active:to-teal-700 shadow-lg shadow-emerald-950/40 transition duration-150 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Agent Executing...</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Run Autonomous Task</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
