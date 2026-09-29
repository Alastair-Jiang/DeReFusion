"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, Clock3, Cpu, Database, Gpu, RefreshCw, ShieldCheck, WifiOff } from "lucide-react";

type Hardware = { id: string; label: string; kind: string; state: string; observedAt?: string | null; utilizationPercent?: number | null; memoryUsedMiB?: number | null; memoryTotalMiB?: number | null; detail?: string };
type Task = { id: string; label: string; hardwareId: string; status: string; currentRun?: string | null; currentStep?: string | null; completed?: number; total?: number; updatedAt?: string | null; source?: string; detail?: string; freshness?: string };
type Snapshot = { schemaVersion: string; observedAt: string; readOnly: boolean; hardware: Hardware[]; tasks: Task[]; edges: { from: string; to: string; label: string; kind: string }[]; alerts: (string | { message?: string; detail?: string })[] };
const labels: Record<string, string> = { running: "运行中", reported_running: "远端报告运行", "reported-running": "远端报告运行", completed: "已完成", queue_completed: "队列完成", waiting: "等待资源", waiting_resource: "等待 GPU", queued: "待处理", blocked: "已阻塞", idle: "空闲", released: "已释放", archived: "历史产物", historical: "历史产物", failed: "异常", interrupted: "已中断", artifact_invalid: "产物异常", stale: "观测过期", unknown: "尚未观测", budget_exhausted: "预算停止", unassigned: "未分配", active: "执行中", fresh: "观测有效" };
function statusLabel(status: string) { return labels[status] ?? status.replaceAll("_", " "); }
function tone(status: string) { return /failed|invalid|error|blocked/.test(status) ? "danger" : /stale|unknown|wait|interrupt|budget/.test(status) ? "warning" : /complete|archiv|histor/.test(status) ? "success" : /run|active/.test(status) ? "info" : "neutral"; }
function timestamp(value?: string | null) { return value && Number.isFinite(Date.parse(value)) ? new Date(value).toLocaleTimeString("zh-CN", { hour12: false }) : "未观测"; }

function TaskNode({ task, hardware, nodeRef, onSelect }: { task: Task; hardware?: Hardware; nodeRef: (node: HTMLButtonElement | null) => void; onSelect: () => void }) {
  const count = Number.isFinite(task.completed) ? task.completed! : 0;
  const total = Number.isFinite(task.total) ? task.total! : 0;
  const Icon = task.hardwareId.includes("cpu") ? Cpu : task.id.includes("archive") ? Database : Gpu;
  return <button type="button" ref={nodeRef} onClick={onSelect} className={`flow-node flow-node-${task.id} flow-tone-${tone(task.status)}`} aria-label={`${task.label}，${statusLabel(task.status)}，完成 ${count}${total ? ` / ${total}` : ""}`}>
    <div className="flow-node-top"><span><Icon size={15} /> {hardware?.label ?? task.hardwareId}</span><span className={`badge badge-${tone(task.status)}`}>{statusLabel(task.status)}</span></div>
    <h3>{task.label}</h3>
    <div className="flow-node-value">{count}<span>{total ? ` / ${total}` : " 份"}</span></div>
    {total > 0 && <div className="flow-progress" role="progressbar" aria-label={`${task.label}完成进度`} aria-valuenow={count} aria-valuemin={0} aria-valuemax={total}><span style={{ width: `${Math.min(100, count / total * 100)}%` }} /></div>}
    <div className="flow-current">{task.currentStep && <strong>{task.currentStep} · </strong>}{task.currentRun ?? task.detail ?? "等待新的完整产物"}</div>
    <div className="flow-node-foot"><Clock3 size={12} /> 记录 {timestamp(task.updatedAt)}{task.freshness === "stale" && <span> · 已过期</span>}</div>
  </button>;
}

export default function LiveComputeFlow() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [paths, setPaths] = useState<{ key: string; d: string; label: string; x: number; y: number; waiting: boolean }[]>([]);
  const graphRef = useRef<HTMLDivElement>(null);
  const nodes = useRef<Record<string, HTMLButtonElement | null>>({});
  const refresh = useCallback(async (signal?: AbortSignal) => {
    try {
      const response = await fetch("/ops-api/status", { cache: "no-store", signal });
      if (!response.ok) throw new Error(`状态服务响应 ${response.status}`);
      const data = (await response.json()) as Partial<Snapshot>;
      if (!data.readOnly || !Array.isArray(data.tasks) || !Array.isArray(data.hardware)) throw new Error("状态数据格式无效");
      setSnapshot(data as Snapshot); setError(null);
    } catch (failure) {
      if (!signal?.aborted) setError(failure instanceof Error ? failure.message : "无法连接状态服务");
    }
  }, []);
  useEffect(() => {
    let alive = true; let timer: ReturnType<typeof setTimeout>; let controller: AbortController;
    const poll = async () => {
      controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 8000);
      await refresh(controller.signal); clearTimeout(timeout);
      if (alive) timer = setTimeout(poll, 5000);
    };
    void poll(); return () => { alive = false; clearTimeout(timer); controller?.abort(); };
  }, [refresh]);
  const taskById = Object.fromEntries((snapshot?.tasks ?? []).map(task => [task.id, task]));
  const hardwareById = Object.fromEntries((snapshot?.hardware ?? []).map(hardware => [hardware.id, hardware]));
  const graphOrder = ["stage-c", "remote-stage-b", "p4-archive", "intake-c", "transfer", "bridge-replay", "gpu-replay-queue", "intake-8000"];
  useEffect(() => {
    const root = graphRef.current; if (!root || !snapshot) return;
    const draw = () => {
      const box = root.getBoundingClientRect();
      setPaths(snapshot.edges.flatMap(edge => {
        const from = nodes.current[edge.from]?.getBoundingClientRect(), to = nodes.current[edge.to]?.getBoundingClientRect();
        if (!from || !to) return [];
        const vertical = to.top >= from.bottom - 2;
        const x1 = (vertical ? from.left + from.width / 2 : from.right) - box.left;
        const y1 = (vertical ? from.bottom : from.top + from.height / 2) - box.top;
        const x2 = (vertical ? to.left + to.width / 2 : to.left) - box.left;
        const y2 = (vertical ? to.top : to.top + to.height / 2) - box.top;
        const mid = vertical ? (y1 + y2) / 2 : (x1 + x2) / 2;
        return [{ key: edge.from + edge.to, d: vertical ? `M${x1},${y1} C${x1},${mid} ${x2},${mid} ${x2},${y2}` : `M${x1},${y1} C${mid},${y1} ${mid},${y2} ${x2},${y2}`, label: edge.label, x: (x1 + x2) / 2, y: (y1 + y2) / 2, waiting: /wait|queue/.test(edge.kind) }];
      }));
    };
    const observer = new ResizeObserver(draw); observer.observe(root); draw();
    return () => observer.disconnect();
  }, [snapshot]);
  const detail = selected && taskById[selected];
  return <section className="live-compute" aria-label="实时硬件任务流程">
    <div className="live-heading"><div><span className="eyebrow">LIVE EXECUTION MAP</span><h2>计算与产物流转</h2><p>训练、回传、审计并行推进；观测状态不代表研究结论。</p></div><div className="live-refresh"><span className={error ? "live-disconnected" : "live-connected"}>{error ? <WifiOff size={15} /> : <Activity size={15} />}{error ? "连接中断" : snapshot ? `更新 ${timestamp(snapshot.observedAt)}` : "连接状态源"}</span><button type="button" className="outline-button" onClick={() => void refresh()} aria-label="刷新硬件任务状态"><RefreshCw size={14} /> 刷新</button></div></div>
    {error && <div className="flow-alert" role="alert"><AlertTriangle size={17} /><span>{error}。{snapshot ? "下方保留最后一次观测，不代表任务仍在运行。" : "不展示猜测的运行状态。"}</span></div>}
    {!snapshot && !error && <div className="flow-loading" role="status">正在读取进程、日志与完整产物…</div>}
    {snapshot && <>
      <div className={`flow-graph ${error ? "flow-old" : ""}`} ref={graphRef}>
        <svg className="flow-connectors" aria-hidden="true"><defs><marker id="flow-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0 L7 3.5 L0 7 Z" fill="currentColor" /></marker></defs>{paths.map(path => <g key={path.key}><path className={path.waiting ? "flow-edge waiting" : "flow-edge"} d={path.d} markerEnd="url(#flow-arrow)" /><text x={path.x} y={path.y - 6} textAnchor="middle">{path.label}</text></g>)}</svg>
        {graphOrder.filter(id => taskById[id]).map(id => <TaskNode key={id} task={taskById[id]} hardware={hardwareById[taskById[id].hardwareId]} nodeRef={node => { nodes.current[id] = node; }} onSelect={() => setSelected(selected === id ? null : id)} />)}
      </div>
      {detail && <div className="flow-detail" aria-live="polite"><strong>{detail.label}</strong><p>{detail.detail ?? statusLabel(detail.status)}</p><span>来源：{detail.source ?? "没有可验证来源"} · 记录：{timestamp(detail.updatedAt)}</span>{detail.currentRun && <code>{detail.currentRun}</code>}</div>}
      <div className="hardware-strip">{snapshot.hardware.map(hardware => <article key={hardware.id}><div><strong>{hardware.label}</strong><span className={`badge badge-${tone(hardware.state)}`}>{statusLabel(hardware.state)}</span></div><p>{hardware.utilizationPercent != null ? `GPU ${hardware.utilizationPercent}%` : hardware.kind === "gpu" ? "利用率未观测" : hardware.detail ?? "只读状态"}{hardware.memoryUsedMiB != null && ` · ${(hardware.memoryUsedMiB / 1024).toFixed(1)}${hardware.memoryTotalMiB ? ` / ${(hardware.memoryTotalMiB / 1024).toFixed(0)}` : ""} GiB`}</p><small>{hardware.detail}</small></article>)}</div>
      {snapshot.alerts.length > 0 && <div className="flow-alerts">{snapshot.alerts.map((alert, index) => <div className="flow-alert" key={index}><AlertTriangle size={16} /><span>{typeof alert === "string" ? alert : alert.message ?? alert.detail}</span></div>)}</div>}
      <div className="flow-legend"><span><Activity size={14} /> 实线：产物依赖</span><span><Clock3 size={14} /> 虚线：等待资源／前置条件</span><span><ShieldCheck size={14} /> 只读，不启动或改动实验</span><span><CheckCircle2 size={14} /> 已完成与已审计分别计数</span></div>
    </>}
  </section>;
}
