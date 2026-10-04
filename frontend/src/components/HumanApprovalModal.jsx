import React, { useState } from 'react';
import { AlertCircle, ShieldAlert, Check, X, FileText, DollarSign, Calendar } from 'lucide-react';

export default function HumanApprovalModal({ approvalData, onApprove, onReject, isSubmitting }) {
  const [feedback, setFeedback] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [isRejecting, setIsRejecting] = useState(false);

  if (!approvalData) return null;

  return (
    <div className="rounded-2xl border-2 border-amber-500/40 bg-gradient-to-b from-amber-950/30 to-slate-900/90 p-6 shadow-2xl backdrop-blur">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div className="flex items-start space-x-3.5">
          <div className="p-2.5 rounded-xl bg-amber-500/20 border border-amber-500/30 text-amber-400 flex-shrink-0">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-bold uppercase tracking-wider bg-amber-500/20 text-amber-300 px-2.5 py-0.5 rounded border border-amber-500/30">
                Governance Checkpoint
              </span>
              <span className="text-xs text-amber-400/80 font-medium">Autonomous Execution Paused</span>
            </div>
            <h3 className="text-base font-bold text-white mt-1.5">
              Human Authorization Required for High-Value Invoice
            </h3>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              TaskPilot AI detected an invoice exceeding the standard autonomous limit (₹100,000). 
              In compliance with enterprise financial governance policy, agent execution has halted pending human verification.
            </p>
          </div>
        </div>
      </div>

      {/* Invoice Details Card */}
      <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/70 p-4 rounded-xl border border-slate-800">
        <div>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">Vendor / Company</span>
          <span className="text-sm font-semibold text-white mt-0.5 block truncate">
            {approvalData.company || 'Enterprise Global'}
          </span>
        </div>
        <div>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">Invoice Number</span>
          <span className="text-sm font-mono font-bold text-emerald-400 mt-0.5 block">
            {approvalData.invoice_number || 'ENT-902'}
          </span>
        </div>
        <div>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">Total Due Amount</span>
          <span className="text-sm font-mono font-bold text-amber-300 mt-0.5 block">
            {approvalData.currency || 'INR'} {Number(approvalData.amount || 125000).toLocaleString()}
          </span>
        </div>
        <div>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">Payment Due Date</span>
          <span className="text-sm font-mono text-slate-200 mt-0.5 block">
            {approvalData.due_date || '2026-11-02'}
          </span>
        </div>
      </div>

      {/* Action Controls */}
      <div className="mt-5 pt-4 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="w-full sm:w-auto text-xs text-slate-400">
          Select an action to resume or terminate the workflow safely.
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto justify-end">
          {!isRejecting ? (
            <>
              <button
                type="button"
                disabled={isSubmitting}
                onClick={() => setIsRejecting(true)}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 transition duration-150 flex items-center space-x-1.5 disabled:opacity-50"
              >
                <X className="w-3.5 h-3.5" />
                <span>Reject Action</span>
              </button>

              <button
                type="button"
                disabled={isSubmitting}
                onClick={() => onApprove(feedback)}
                className="px-5 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 shadow-lg shadow-emerald-950/40 transition duration-150 flex items-center space-x-1.5 disabled:opacity-50"
              >
                <Check className="w-4 h-4" />
                <span>Authorize & Submit</span>
              </button>
            </>
          ) : (
            <div className="flex items-center space-x-2 w-full">
              <input
                type="text"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Reason for rejection (e.g. Unapproved Q4 budget)"
                className="bg-slate-900 border border-rose-500/40 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-400 w-64"
              />
              <button
                disabled={isSubmitting}
                onClick={() => onReject(rejectReason)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500"
              >
                Confirm Reject
              </button>
              <button
                onClick={() => setIsRejecting(false)}
                className="px-2 py-1.5 text-xs text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
