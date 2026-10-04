import React, { useState } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  Clock, 
  ChevronDown, 
  ChevronRight, 
  Terminal, 
  ShieldCheck, 
  Search, 
  FileText, 
  Send 
} from 'lucide-react';

export default function ExecutionTimeline({ events = [], currentStepIndex, plan = [] }) {
  const [expandedEvents, setExpandedEvents] = useState({});

  const toggleExpand = (id) => {
    setExpandedEvents((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const getEventIcon = (event) => {
    const status = event.status?.toLowerCase();
    const action = event.action?.toLowerCase() || '';

    if (status === 'error' || action.includes('fail')) {
      return <AlertTriangle className="w-4 h-4 text-rose-400" />;
    }
    if (status === 'warning' || action.includes('recover')) {
      return <RefreshCw className="w-4 h-4 text-amber-400 animate-spin" />;
    }
    if (status === 'success') {
      return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
    }
    if (action.includes('search')) {
      return <Search className="w-4 h-4 text-blue-400" />;
    }
    if (action.includes('extract')) {
      return <FileText className="w-4 h-4 text-teal-400" />;
    }
    if (action.includes('submit')) {
      return <Send className="w-4 h-4 text-indigo-400" />;
    }
    return <Clock className="w-4 h-4 text-slate-400" />;
  };

  return (
    <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 shadow-xl flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-white tracking-wide">Live Execution Timeline</h3>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          {events.length} event{events.length !== 1 ? 's' : ''} recorded
        </span>
      </div>

      {events.length === 0 ? (
        <div className="py-12 text-center text-slate-500 text-xs flex flex-col items-center justify-center space-y-2">
          <Clock className="w-6 h-6 text-slate-600 animate-pulse" />
          <p>Agent idle. Run a task or select a demo scenario to initiate timeline.</p>
        </div>
      ) : (
        <div className="mt-4 space-y-3 overflow-y-auto pr-1 flex-1 max-h-[520px]">
          {events.map((event, idx) => {
            const isExpanded = !!expandedEvents[event.id || idx];
            const hasDetails = event.details && Object.keys(event.details).length > 0;
            const timeStr = event.timestamp ? event.timestamp.slice(11, 19) : '';

            const isRecovery = event.status === 'warning' || event.action === 'recover';
            const isError = event.status === 'error';

            return (
              <div
                key={event.id || idx}
                className={`p-3 rounded-xl border transition duration-150 ${
                  isError
                    ? 'bg-rose-950/20 border-rose-500/30'
                    : isRecovery
                    ? 'bg-amber-950/20 border-amber-500/30'
                    : 'bg-slate-950/50 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div
                  className="flex items-start justify-between cursor-pointer select-none"
                  onClick={() => hasDetails && toggleExpand(event.id || idx)}
                >
                  <div className="flex items-start space-x-3">
                    <div className="mt-0.5 flex-shrink-0">{getEventIcon(event)}</div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold text-slate-200">
                          {event.message}
                        </span>
                        {event.tool && (
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400 border border-slate-700">
                            {event.tool}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-[10px] font-mono text-slate-500">[{timeStr}]</span>
                        <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                          {event.state}
                        </span>
                      </div>
                    </div>
                  </div>

                  {hasDetails && (
                    <button className="text-slate-500 hover:text-slate-300 p-1">
                      {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                    </button>
                  )}
                </div>

                {/* Structured JSON Inspector */}
                {isExpanded && hasDetails && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800">
                    <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Event Metadata / Tool Payload:
                    </div>
                    <pre className="text-[11px] font-mono text-slate-300 bg-slate-900/90 p-2.5 rounded-lg overflow-x-auto max-h-48 border border-slate-800">
                      {JSON.stringify(event.details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
