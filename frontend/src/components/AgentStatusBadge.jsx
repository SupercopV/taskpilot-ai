import React from 'react';
import { 
  Sparkles, 
  Play, 
  PauseCircle, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  Search, 
  Clock 
} from 'lucide-react';

export default function AgentStatusBadge({ status }) {
  const getBadgeConfig = () => {
    switch (status?.toUpperCase()) {
      case 'PLANNING':
        return {
          label: 'Planning Workflow',
          color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
          dot: 'bg-indigo-400',
          icon: Sparkles
        };
      case 'EXECUTING':
        return {
          label: 'Executing Tools',
          color: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
          dot: 'bg-blue-400 animate-pulse',
          icon: Play
        };
      case 'WAITING_FOR_APPROVAL':
        return {
          label: 'Waiting for Human Approval',
          color: 'bg-amber-500/15 text-amber-300 border-amber-500/40 animate-pulse',
          dot: 'bg-amber-400',
          icon: PauseCircle
        };
      case 'RECOVERING':
        return {
          label: 'Self-Healing & Retrying',
          color: 'bg-orange-500/15 text-orange-300 border-orange-500/40',
          dot: 'bg-orange-400 animate-spin',
          icon: RefreshCw
        };
      case 'VERIFYING':
        return {
          label: 'Auditing & Verifying Ledger',
          color: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
          dot: 'bg-purple-400 animate-pulse',
          icon: Search
        };
      case 'COMPLETED':
        return {
          label: 'Task Completed & Verified',
          color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          dot: 'bg-emerald-400',
          icon: CheckCircle2
        };
      case 'REJECTED':
        return {
          label: 'Rejected by User',
          color: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          dot: 'bg-rose-400',
          icon: XCircle
        };
      case 'FAILED':
        return {
          label: 'Execution Terminated (Failed)',
          color: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          dot: 'bg-rose-400',
          icon: XCircle
        };
      default:
        return {
          label: status || 'Idle / Ready',
          color: 'bg-slate-800 text-slate-300 border-slate-700',
          dot: 'bg-slate-400',
          icon: Clock
        };
    }
  };

  const { label, color, dot, icon: Icon } = getBadgeConfig();

  return (
    <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold border ${color}`}>
      <span className={`w-2 h-2 rounded-full ${dot}`}></span>
      <Icon className="w-3.5 h-3.5" />
      <span>{label}</span>
    </div>
  );
}
