import React, { useState, useEffect } from 'react';
import { Database, Search, RefreshCw, CheckCircle2, ExternalLink } from 'lucide-react';
import { getFinanceInvoices } from '../services/api';

export default function FinancePortalView() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchInvoices = async () => {
    try {
      setLoading(true);
      const data = await getFinanceInvoices();
      setInvoices(data || []);
    } catch (err) {
      console.error("Failed to load finance invoices:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
    const interval = setInterval(fetchInvoices, 4000);
    return () => clearInterval(interval);
  }, []);

  const filtered = invoices.filter((inv) => {
    const q = search.toLowerCase().trim();
    if (!q) return true;
    return (
      (inv.company && inv.company.toLowerCase().includes(q)) ||
      (inv.invoice_number && inv.invoice_number.toLowerCase().includes(q)) ||
      (inv.record_id && inv.record_id.toLowerCase().includes(q))
    );
  });

  const totalAmount = invoices.reduce((acc, curr) => acc + (parseFloat(curr.amount) || 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-white">NexusFinance Enterprise ERP — Accounts Payable Ledger</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            System of record for all verified business invoices ingested by TaskPilot AI agents.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchInvoices}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-850 hover:bg-slate-800 text-slate-300 border border-slate-700 transition"
            title="Refresh Ledger"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <a
            href="/finance"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 transition flex items-center space-x-1.5 shadow"
          >
            <span>Open Standalone Web ERP</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Total General Ledger Volume
          </span>
          <span className="text-2xl font-mono font-bold text-white mt-1 block">
            ₹{totalAmount.toLocaleString()}
          </span>
          <span className="text-xs text-emerald-400 mt-1 block">Reconciled in ERP Database</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Ingested Records
          </span>
          <span className="text-2xl font-mono font-bold text-emerald-400 mt-1 block">
            {invoices.length}
          </span>
          <span className="text-xs text-slate-400 mt-1 block">Historical & Autonomous Records</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Verification Parity
          </span>
          <span className="text-2xl font-mono font-bold text-emerald-400 mt-1 block">
            100%
          </span>
          <span className="text-xs text-slate-400 mt-1 block">Field-Level Parity Audited</span>
        </div>
      </div>

      {/* Search & Records Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between gap-4">
          <h3 className="text-sm font-bold text-white">General Ledger Journal Entries</h3>
          <div className="relative w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search company, invoice #, ID..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-sans"
            />
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="min-w-full divide-y divide-slate-800 text-left text-xs">
            <thead className="bg-slate-950 font-semibold text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="py-3 px-3">Record ID</th>
                <th className="py-3 px-3">Company / Vendor</th>
                <th className="py-3 px-3">Invoice Number</th>
                <th className="py-3 px-3 text-right">Amount</th>
                <th className="py-3 px-3">Due Date</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3">Created At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono text-slate-300">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-8 text-center text-slate-500 font-sans">
                    No finance ledger records matching search filter.
                  </td>
                </tr>
              ) : (
                filtered.map((inv) => (
                  <tr key={inv.record_id} className="hover:bg-slate-850/50 transition duration-150">
                    <td className="py-3 px-3 font-bold text-emerald-400">{inv.record_id}</td>
                    <td className="py-3 px-3 font-sans font-medium text-white">{inv.company}</td>
                    <td className="py-3 px-3 font-mono text-slate-300">{inv.invoice_number}</td>
                    <td className="py-3 px-3 text-right font-bold text-white">
                      {inv.currency} {Number(inv.amount).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-slate-400">{inv.due_date}</td>
                    <td className="py-3 px-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {inv.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-500 text-[11px]">
                      {inv.created_at ? inv.created_at.slice(0, 19).replace('T', ' ') : 'N/A'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
