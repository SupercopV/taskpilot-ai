import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import DemoScenarios from './components/DemoScenarios';
import TaskInput from './components/TaskInput';
import AgentStatusBadge from './components/AgentStatusBadge';
import ExecutionTimeline from './components/ExecutionTimeline';
import EvidenceViewer from './components/EvidenceViewer';
import HumanApprovalModal from './components/HumanApprovalModal';
import FinancePortalView from './components/FinancePortalView';
import { 
  checkHealth, 
  createTask, 
  getTaskStatus, 
  getTaskEvents, 
  getTaskResult, 
  approveTask, 
  rejectTask 
} from './services/api';
import { 
  Bot, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Layers, 
  Sparkles, 
  ShieldCheck, 
  FileText 
} from 'lucide-react';

export default function App() {
  const [health, setHealth] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Task State
  const [goal, setGoal] = useState('');
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [events, setEvents] = useState([]);
  const [result, setResult] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmittingApproval, setIsSubmittingApproval] = useState(false);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const pollingRef = useRef(null);

  // Initial Health Check
  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch((err) => console.warn('Health check issue:', err));
  }, []);

  // Poll for events & status updates while running
  const refreshTaskData = async (currentTaskId) => {
    if (!currentTaskId) return;
    try {
      const [statusData, eventsData] = await Promise.all([
        getTaskStatus(currentTaskId),
        getTaskEvents(currentTaskId)
      ]);

      setTaskStatus(statusData);
      setEvents(eventsData || []);

      const currentStatus = statusData.status?.toUpperCase();

      if (currentStatus === 'COMPLETED') {
        setIsRunning(false);
        const resultData = await getTaskResult(currentTaskId);
        setResult(resultData);
      } else if (currentStatus === 'FAILED' || currentStatus === 'REJECTED') {
        setIsRunning(false);
      } else if (currentStatus === 'WAITING_FOR_APPROVAL') {
        setIsRunning(false); // Paused for human approval
      }
    } catch (err) {
      console.error('Error refreshing task data:', err);
    }
  };

  // Setup WebSocket & Polling
  useEffect(() => {
    if (!taskId) return;

    // WebSocket connection
    let wsUrl;
    const apiUrl = import.meta.env.VITE_API_URL;
    if (apiUrl) {
      const cleanUrl = apiUrl.replace(/^http/, 'ws');
      wsUrl = `${cleanUrl}/ws/tasks/${taskId}`;
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      wsUrl = `${protocol}//${host}/ws/tasks/${taskId}`;
    }

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          refreshTaskData(taskId);
        } catch (e) {
          // non-json
        }
      };

      ws.onerror = () => {
        // Fallback to HTTP polling handled below
      };
    } catch (err) {
      console.warn("WebSocket init warning:", err);
    }

    // Polling interval fallback for seamless live feedback
    pollingRef.current = setInterval(() => {
      refreshTaskData(taskId);
    }, 1000);

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [taskId]);

  // Handle Run Task
  const handleRunTask = async () => {
    if (!goal.trim()) return;
    setError(null);
    setIsRunning(true);
    setResult(null);
    setEvents([]);

    try {
      const res = await createTask(goal, simulateFailure);
      setTaskId(res.task_id);
      setTaskStatus({ status: 'PLANNING', goal: goal, plan: [] });
      await refreshTaskData(res.task_id);
    } catch (err) {
      setError(err.message || 'Failed to initiate task');
      setIsRunning(false);
    }
  };

  // Handle Demo Scenario Click
  const handleSelectScenario = (scenarioPrompt, shouldSimulateFailure) => {
    setGoal(scenarioPrompt);
    setSimulateFailure(shouldSimulateFailure);
  };

  // Handle Human Approval
  const handleApprove = async (feedback) => {
    if (!taskId) return;
    setIsSubmittingApproval(true);
    try {
      await approveTask(taskId, feedback);
      setIsRunning(true);
      await refreshTaskData(taskId);
    } catch (err) {
      setError(err.message || 'Approval submission failed');
    } finally {
      setIsSubmittingApproval(false);
    }
  };

  // Handle Human Rejection
  const handleReject = async (reason) => {
    if (!taskId) return;
    setIsSubmittingApproval(true);
    try {
      await rejectTask(taskId, reason);
      setIsRunning(false);
      await refreshTaskData(taskId);
    } catch (err) {
      setError(err.message || 'Rejection failed');
    } finally {
      setIsSubmittingApproval(false);
    }
  };

  const isApprovalRequired = taskStatus?.status === 'WAITING_FOR_APPROVAL';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header health={health} activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'finance' ? (
          <FinancePortalView />
        ) : (
          <div className="space-y-8">
            {/* Top Demo Scenarios Bar */}
            <DemoScenarios onSelectScenario={handleSelectScenario} isRunning={isRunning} />

            {/* Main Task Input */}
            <TaskInput
              goal={goal}
              setGoal={setGoal}
              simulateFailure={simulateFailure}
              setSimulateFailure={setSimulateFailure}
              onSubmit={handleRunTask}
              isRunning={isRunning}
              error={error}
            />

            {/* Human Approval Governance Banner */}
            {isApprovalRequired && (
              <HumanApprovalModal
                approvalData={taskStatus?.approval_request}
                onApprove={handleApprove}
                onReject={handleReject}
                isSubmitting={isSubmittingApproval}
              />
            )}

            {/* Main Dashboard Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              {/* Left Column: Plan, Extracted Data, and Evidence Result */}
              <div className="lg:col-span-7 space-y-6">
                {/* Active Plan Card */}
                {taskStatus?.plan && taskStatus.plan.length > 0 && (
                  <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6 shadow-xl space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                      <div className="flex items-center space-x-2">
                        <Layers className="w-4 h-4 text-emerald-400" />
                        <h3 className="text-sm font-bold text-white">Autonomous Execution Plan</h3>
                      </div>
                      <AgentStatusBadge status={taskStatus?.status} />
                    </div>

                    <div className="space-y-2.5">
                      {taskStatus.plan.map((step, idx) => {
                        const isCurrent = idx === taskStatus.current_step_index && isRunning;
                        const isDone = idx < taskStatus.current_step_index || taskStatus.status === 'COMPLETED';

                        return (
                          <div
                            key={step.step_id || idx}
                            className={`p-3 rounded-xl border flex items-start space-x-3 transition duration-150 ${
                              isCurrent
                                ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
                                : isDone
                                ? 'bg-slate-950/60 border-slate-800 text-slate-300'
                                : 'bg-slate-950/30 border-slate-800/60 text-slate-500'
                            }`}
                          >
                            <div className="mt-0.5 flex-shrink-0">
                              {isDone ? (
                                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                              ) : isCurrent ? (
                                <span className="relative flex h-3.5 w-3.5 mt-0.5">
                                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                  <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-emerald-500"></span>
                                </span>
                              ) : (
                                <div className="w-4 h-4 rounded-full border border-slate-700 flex items-center justify-center text-[10px] text-slate-500">
                                  {idx + 1}
                                </div>
                              )}
                            </div>

                            <div className="flex-1">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-white">{step.title}</span>
                                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400 border border-slate-700">
                                  {step.tool}
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-400 mt-0.5">{step.description}</p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Final Evidence & Reconciled Result */}
                {result && <EvidenceViewer taskResult={result} />}
              </div>

              {/* Right Column: Live Timeline of Events */}
              <div className="lg:col-span-5">
                <ExecutionTimeline 
                  events={events} 
                  currentStepIndex={taskStatus?.current_step_index} 
                  plan={taskStatus?.plan} 
                />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>TaskPilot AI — Autonomous AI Worker for Enterprise Task Automation</span>
          <span className="font-mono text-[11px]">LangGraph • FastAPI • Playwright • Chromium</span>
        </div>
      </footer>
    </div>
  );
}
