"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  API_BASE_URL,
  api,
  type ArtifactDetail,
  type ImportResponse,
  type JourneyItem,
  type JourneyStep,
  type LogItem,
  type SessionDetail,
  type SessionItem,
  type TestCaseDetail,
  type TestCaseItem,
  type TestRun,
} from "./lib/api";

const TABS = ["Logs", "Sessions", "Journeys", "Test Cases", "Runs", "Report"] as const;

type Tab = (typeof TABS)[number];
type Notice = { type: "ok" | "error"; text: string } | null;

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "n/a";
  }
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatJson(value: unknown) {
  return JSON.stringify(value ?? {}, null, 2);
}

function statusClass(status: string | number | null | undefined) {
  const normalized = String(status ?? "").toLowerCase();
  if (normalized.includes("pass") || normalized === "200" || normalized === "201") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  if (normalized.includes("fail") || normalized.includes("error") || normalized.startsWith("5")) {
    return "border-rose-200 bg-rose-50 text-rose-700";
  }
  return "border-slate-200 bg-slate-50 text-slate-700";
}

function getArtifact(testCase: TestCaseDetail | null): ArtifactDetail | null {
  return testCase?.artifacts.find((artifact) => artifact.framework === "jest_supertest") ?? null;
}

function chainingRows(steps: JourneyStep[]) {
  return steps.flatMap((step, index) => {
    const extract = Object.entries(step.extract ?? {}).map(([field, path]) => ({
      kind: "extract",
      step: index + 1,
      field,
      path: String(path),
      endpoint: step.endpoint ?? "/",
    }));
    const uses = Object.entries(step.uses ?? {}).map(([field, source]) => ({
      kind: "use",
      step: index + 1,
      field,
      path: typeof source === "string" ? source : formatJson(source),
      endpoint: step.endpoint ?? "/",
    }));
    return [...extract, ...uses];
  });
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("Logs");
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [journeys, setJourneys] = useState<JourneyItem[]>([]);
  const [testCases, setTestCases] = useState<TestCaseItem[]>([]);
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>("");
  const [selectedJourneyId, setSelectedJourneyId] = useState<string>("");
  const [selectedTestCaseId, setSelectedTestCaseId] = useState<string>("");
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [sessionDetail, setSessionDetail] = useState<SessionDetail | null>(null);
  const [testCaseDetail, setTestCaseDetail] = useState<TestCaseDetail | null>(null);
  const [runDetail, setRunDetail] = useState<TestRun | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const [busy, setBusy] = useState<string>("");

  const selectedJourney = useMemo(
    () => journeys.find((journey) => journey.id === selectedJourneyId) ?? null,
    [journeys, selectedJourneyId],
  );
  const selectedRun = runDetail ?? runs.find((run) => run.id === selectedRunId) ?? null;
  const latestRun = runs[0] ?? null;
  const artifact = getArtifact(testCaseDetail);

  const setResult = (label: string, result: ImportResponse | { [key: string]: unknown }) => {
    setNotice({ type: "ok", text: `${label}: ${formatJson(result)}` });
  };

  const loadLists = useCallback(async () => {
    const [logList, sessionList, journeyList, testCaseList, runList] = await Promise.all([
      api.listLogs(),
      api.listSessions(),
      api.listJourneys(),
      api.listTestCases(),
      api.listRuns(),
    ]);
    setLogs(logList.items);
    setSessions(sessionList.items);
    setJourneys(journeyList.items);
    setTestCases(testCaseList.items);
    setRuns(runList.items);
    setSelectedSessionId((current) => current || sessionList.items[0]?.external_session_id || "");
    setSelectedJourneyId((current) => current || journeyList.items[0]?.id || "");
    setSelectedTestCaseId((current) => current || testCaseList.items[0]?.id || "");
    setSelectedRunId((current) => current || runList.items[0]?.id || "");
  }, []);

  const runAction = useCallback(async (label: string, action: () => Promise<unknown>) => {
    setBusy(label);
    setNotice(null);
    try {
      const result = await action();
      if (result && typeof result === "object") {
        setResult(label, result as { [key: string]: unknown });
      } else {
        setNotice({ type: "ok", text: `${label} completed.` });
      }
      await loadLists();
    } catch (error) {
      setNotice({
        type: "error",
        text: `${label} failed: ${error instanceof Error ? error.message : String(error)}`,
      });
    } finally {
      setBusy("");
    }
  }, [loadLists]);

  useEffect(() => {
    let ignore = false;
    Promise.all([
      api.listLogs(),
      api.listSessions(),
      api.listJourneys(),
      api.listTestCases(),
      api.listRuns(),
    ])
      .then(([logList, sessionList, journeyList, testCaseList, runList]) => {
        if (ignore) {
          return;
        }
        setLogs(logList.items);
        setSessions(sessionList.items);
        setJourneys(journeyList.items);
        setTestCases(testCaseList.items);
        setRuns(runList.items);
        setSelectedSessionId(sessionList.items[0]?.external_session_id || "");
        setSelectedJourneyId(journeyList.items[0]?.id || "");
        setSelectedTestCaseId(testCaseList.items[0]?.id || "");
        setSelectedRunId(runList.items[0]?.id || "");
      })
      .catch((error) => {
        if (ignore) {
          return;
        }
        setNotice({
          type: "error",
          text: `Load dashboard data failed: ${error instanceof Error ? error.message : String(error)}`,
        });
      });
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (selectedSessionId) {
      api.getSession(selectedSessionId).then(setSessionDetail).catch(() => setSessionDetail(null));
    }
  }, [selectedSessionId]);

  useEffect(() => {
    if (selectedTestCaseId) {
      api.getTestCase(selectedTestCaseId).then(setTestCaseDetail).catch(() => setTestCaseDetail(null));
    }
  }, [selectedTestCaseId]);

  useEffect(() => {
    if (selectedRunId) {
      api.getRun(selectedRunId).then(setRunDetail).catch(() => setRunDetail(null));
    }
  }, [selectedRunId]);

  return (
    <main className="min-h-screen bg-[#f6f7f9] text-slate-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
        <Header logs={logs.length} journeys={journeys.length} tests={testCases.length} runs={runs.length} />

        <section className="grid gap-4 border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[1.6fr_1fr]">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <ActionButton
                disabled={Boolean(busy)}
                label="Import Mock"
                onClick={() => runAction("Import mock logs", api.importMockLogs)}
              />
              <ActionButton
                disabled={Boolean(busy)}
                label="Import ES"
                onClick={() => runAction("Import Elasticsearch logs", api.importElasticsearchLogs)}
              />
              <ActionButton
                disabled={Boolean(busy)}
                label="Analyze"
                onClick={() => runAction("Analyze journeys", api.analyzeJourneys)}
              />
              <ActionButton
                disabled={Boolean(busy) || !selectedJourneyId}
                label="Generate Jest"
                onClick={() =>
                  runAction("Generate Jest/Supertest test", () => api.generateTest(selectedJourneyId))
                }
              />
              <ActionButton
                disabled={Boolean(busy) || !selectedTestCaseId}
                label="Run Test"
                onClick={() =>
                  runAction("Run selected test", () => api.runTestCase(selectedTestCaseId))
                }
              />
              <ActionButton disabled={Boolean(busy)} label="Refresh" onClick={() => runAction("Refresh", loadLists)} />
            </div>
            <p className="mt-3 text-sm text-slate-600">
              API: <span className="font-mono text-slate-900">{API_BASE_URL}</span> · Target:{" "}
              <span className="font-mono text-slate-900">configured by API</span>
            </p>
          </div>
          <div className="min-h-20 border border-slate-200 bg-slate-50 p-3 text-sm">
            <p className="font-medium text-slate-900">{busy ? `${busy}...` : "Pipeline status"}</p>
            <p className={notice?.type === "error" ? "mt-2 text-rose-700" : "mt-2 text-slate-600"}>
              {notice?.text ?? "Ready. Start with demo script or import mock logs, then analyze."}
            </p>
          </div>
        </section>

        <nav className="flex gap-1 overflow-x-auto border-b border-slate-300">
          {TABS.map((tab) => (
            <button
              className={`h-10 whitespace-nowrap border border-b-0 px-3 text-sm font-medium ${
                activeTab === tab
                  ? "border-slate-300 bg-white text-slate-950"
                  : "border-transparent text-slate-600 hover:bg-white"
              }`}
              key={tab}
              onClick={() => setActiveTab(tab)}
              type="button"
            >
              {tab}
            </button>
          ))}
        </nav>

        {activeTab === "Logs" ? <LogsPanel logs={logs} /> : null}
        {activeTab === "Sessions" ? (
          <SessionsPanel
            detail={sessionDetail}
            selectedId={selectedSessionId}
            sessions={sessions}
            onSelect={setSelectedSessionId}
          />
        ) : null}
        {activeTab === "Journeys" ? (
          <JourneysPanel
            journey={selectedJourney}
            journeys={journeys}
            selectedId={selectedJourneyId}
            onSelect={setSelectedJourneyId}
          />
        ) : null}
        {activeTab === "Test Cases" ? (
          <TestCasesPanel
            artifact={artifact}
            detail={testCaseDetail}
            selectedId={selectedTestCaseId}
            testCases={testCases}
            onSelect={setSelectedTestCaseId}
          />
        ) : null}
        {activeTab === "Runs" ? (
          <RunsPanel runs={runs} selectedId={selectedRunId} selectedRun={selectedRun} onSelect={setSelectedRunId} />
        ) : null}
        {activeTab === "Report" ? <ReportPanel latestRun={latestRun} selectedRun={selectedRun} /> : null}
      </div>
    </main>
  );
}

function Header({
  logs,
  journeys,
  tests,
  runs,
}: {
  logs: number;
  journeys: number;
  tests: number;
  runs: number;
}) {
  return (
    <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div>
        <p className="text-sm font-semibold uppercase text-slate-500">LogiTest AI MVP</p>
        <h1 className="text-3xl font-semibold text-slate-950">Behavior regression dashboard</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Import API logs, mine journeys, generate Jest/Supertest tests, execute against the demo backend, and inspect
          regression diffs from one operational screen.
        </p>
        <Link
          className="mt-3 inline-flex h-9 items-center justify-center border border-slate-900 bg-slate-950 px-3 text-sm font-medium text-white hover:bg-slate-800"
          href="/demo"
        >
          Run Web Demo
        </Link>
      </div>
      <div className="grid grid-cols-4 gap-2 text-center">
        <Metric label="Logs" value={logs} />
        <Metric label="Journeys" value={journeys} />
        <Metric label="Tests" value={tests} />
        <Metric label="Runs" value={runs} />
      </div>
    </header>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="min-w-20 border border-slate-200 bg-white px-3 py-2">
      <div className="text-xl font-semibold">{value}</div>
      <div className="text-xs uppercase text-slate-500">{label}</div>
    </div>
  );
}

function ActionButton({
  disabled,
  label,
  onClick,
}: {
  disabled: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      className="h-9 border border-slate-900 bg-slate-950 px-3 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:border-slate-300 disabled:bg-slate-200 disabled:text-slate-500"
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      {label}
    </button>
  );
}

function EmptyState({ label }: { label: string }) {
  return <div className="border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">{label}</div>;
}

function LogsPanel({ logs }: { logs: LogItem[] }) {
  if (logs.length === 0) {
    return <EmptyState label="No logs yet. Run the demo flow and import Elasticsearch, or import mock logs." />;
  }
  return (
    <Panel title="Raw API Logs" subtitle="Latest normalized requests stored by the platform.">
      <Table
        headers={["Time", "Session", "Method", "Endpoint", "Status", "Latency"]}
        rows={logs.map((log) => [
          formatDate(log.occurred_at),
          log.session_external_id ?? "n/a",
          log.method ?? "n/a",
          log.endpoint ?? "n/a",
          <Badge key={log.id} value={log.status_code ?? "n/a"} />,
          log.response_time_ms === null ? "n/a" : `${log.response_time_ms} ms`,
        ])}
      />
    </Panel>
  );
}

function SessionsPanel({
  detail,
  onSelect,
  selectedId,
  sessions,
}: {
  detail: SessionDetail | null;
  onSelect: (id: string) => void;
  selectedId: string;
  sessions: SessionItem[];
}) {
  if (sessions.length === 0) {
    return <EmptyState label="No sessions yet. Import logs first." />;
  }
  return (
    <SplitPanel
      left={
        <Table
          headers={["Session", "User", "Requests", "Source", "Start"]}
          rows={sessions.map((session) => [
            <button
              className={`text-left font-mono text-xs ${selectedId === session.external_session_id ? "font-semibold text-slate-950" : "text-slate-700"}`}
              key={session.id}
              onClick={() => onSelect(session.external_session_id)}
              type="button"
            >
              {session.external_session_id}
            </button>,
            session.user_id ?? "n/a",
            session.log_count,
            session.source,
            formatDate(session.started_at),
          ])}
        />
      }
      right={
        <Detail title="Session detail">
          {detail ? (
            <>
              <KeyValue label="External ID" value={detail.session.external_session_id} />
              <KeyValue label="Services" value={detail.session.services.join(", ") || "n/a"} />
              <KeyValue label="Log count" value={String(detail.logs.length)} />
              <h3 className="mt-4 text-sm font-semibold">Replay order</h3>
              <ol className="mt-2 space-y-2">
                {detail.logs.map((log) => (
                  <li className="border border-slate-200 bg-slate-50 p-2 text-sm" key={log.id}>
                    <span className="font-mono">{log.method}</span> {log.endpoint}{" "}
                    <span className="text-slate-500">{log.response_time_ms} ms</span>
                  </li>
                ))}
              </ol>
            </>
          ) : (
            <p className="text-sm text-slate-500">Select a session.</p>
          )}
        </Detail>
      }
    />
  );
}

function JourneysPanel({
  journey,
  journeys,
  onSelect,
  selectedId,
}: {
  journey: JourneyItem | null;
  journeys: JourneyItem[];
  onSelect: (id: string) => void;
  selectedId: string;
}) {
  if (journeys.length === 0) {
    return <EmptyState label="No journeys yet. Import logs, then run behavior analysis." />;
  }
  const proofRows = journey ? chainingRows(journey.steps) : [];
  return (
    <SplitPanel
      left={
        <Table
          headers={["Journey", "Persona", "Sessions", "Risk"]}
          rows={journeys.map((item) => [
            <button
              className={`text-left ${selectedId === item.id ? "font-semibold text-slate-950" : "text-slate-700"}`}
              key={item.id}
              onClick={() => onSelect(item.id)}
              type="button"
            >
              {item.name}
            </button>,
            item.persona_name ?? "n/a",
            item.source_session_count,
            item.risk_score ?? "n/a",
          ])}
        />
      }
      right={
        <Detail title="Journey detail">
          {journey ? (
            <>
              <KeyValue label="Example session" value={journey.example_session_id ?? "n/a"} />
              <KeyValue label="Frequency" value={String(journey.frequency_score ?? "n/a")} />
              <h3 className="mt-4 text-sm font-semibold">Steps</h3>
              <ol className="mt-2 space-y-2">
                {journey.steps.map((step, index) => (
                  <li className="border border-slate-200 bg-slate-50 p-2 text-sm" key={`${step.endpoint}-${index}`}>
                    <span className="font-mono">{step.method ?? "GET"}</span> {step.endpoint ?? "/"}{" "}
                    <span className="text-slate-500">{step.action_type ?? ""}</span>
                  </li>
                ))}
              </ol>
              <h3 className="mt-4 text-sm font-semibold">Chaining proof</h3>
              {proofRows.length ? (
                <div className="mt-2 space-y-2">
                  {proofRows.map((row) => (
                    <div className="border border-slate-200 bg-white p-2 text-sm" key={`${row.kind}-${row.step}-${row.field}`}>
                      <Badge value={row.kind} /> step {row.step} · {row.field} ·{" "}
                      <span className="font-mono">{row.path}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-sm text-slate-500">No extracted variables detected on this journey.</p>
              )}
            </>
          ) : (
            <p className="text-sm text-slate-500">Select a journey.</p>
          )}
        </Detail>
      }
    />
  );
}

function TestCasesPanel({
  artifact,
  detail,
  onSelect,
  selectedId,
  testCases,
}: {
  artifact: ArtifactDetail | null;
  detail: TestCaseDetail | null;
  onSelect: (id: string) => void;
  selectedId: string;
  testCases: TestCaseItem[];
}) {
  if (testCases.length === 0) {
    return <EmptyState label="No generated tests yet. Select a journey and generate Jest/Supertest." />;
  }
  return (
    <SplitPanel
      left={
        <Table
          headers={["Test Case", "Journey", "Steps", "Status"]}
          rows={testCases.map((testCase) => [
            <button
              className={`text-left ${selectedId === testCase.id ? "font-semibold text-slate-950" : "text-slate-700"}`}
              key={testCase.id}
              onClick={() => onSelect(testCase.id)}
              type="button"
            >
              {testCase.name}
            </button>,
            testCase.journey_name ?? "n/a",
            testCase.step_count,
            <Badge key={testCase.id} value={testCase.status} />,
          ])}
        />
      }
      right={
        <Detail title="Generated Jest/Supertest">
          {detail ? (
            <>
              <KeyValue label="Generated by" value={detail.generated_by} />
              <KeyValue label="Artifact" value={artifact?.file_path ?? "database artifact"} />
              <pre className="mt-3 max-h-[520px] overflow-auto border border-slate-200 bg-slate-950 p-3 text-xs leading-5 text-slate-100">
                {artifact?.code ?? detail.generated_code ?? "No generated code stored for this test case."}
              </pre>
            </>
          ) : (
            <p className="text-sm text-slate-500">Select a test case.</p>
          )}
        </Detail>
      }
    />
  );
}

function RunsPanel({
  onSelect,
  runs,
  selectedId,
  selectedRun,
}: {
  onSelect: (id: string) => void;
  runs: TestRun[];
  selectedId: string;
  selectedRun: TestRun | null;
}) {
  if (runs.length === 0) {
    return <EmptyState label="No runs yet. Generate a test case, then run it against the demo backend." />;
  }
  return (
    <SplitPanel
      left={
        <Table
          headers={["Run", "Status", "Duration", "Started"]}
          rows={runs.map((run) => [
            <button
              className={`text-left font-mono text-xs ${selectedId === run.id ? "font-semibold text-slate-950" : "text-slate-700"}`}
              key={run.id}
              onClick={() => onSelect(run.id)}
              type="button"
            >
              {run.id.slice(0, 8)}
            </button>,
            <Badge key={run.id} value={run.status} />,
            run.duration_ms === null ? "n/a" : `${run.duration_ms} ms`,
            formatDate(run.started_at),
          ])}
        />
      }
      right={
        <Detail title="Run result">
          {selectedRun ? (
            <>
              <KeyValue label="Test case" value={selectedRun.test_case_id} />
              <KeyValue label="Environment" value={selectedRun.target_environment} />
              <KeyValue label="Error" value={selectedRun.error_message ?? "none"} />
              <JsonBlock title="Actual response" value={selectedRun.actual_response} />
              <JsonBlock title="Diff result" value={selectedRun.diff_result} />
            </>
          ) : (
            <p className="text-sm text-slate-500">Select a run.</p>
          )}
        </Detail>
      }
    />
  );
}

function ReportPanel({ latestRun, selectedRun }: { latestRun: TestRun | null; selectedRun: TestRun | null }) {
  const run = selectedRun ?? latestRun;
  if (!run) {
    return <EmptyState label="No report yet. Run a generated test to persist a regression report." />;
  }
  return (
    <Panel title="Regression Report" subtitle="Latest selected execution output from the reports API.">
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs uppercase text-slate-500">Status</p>
          <Badge value={run.status} />
        </div>
        <div className="border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs uppercase text-slate-500">Duration</p>
          <p className="mt-1 text-lg font-semibold">{run.duration_ms ?? "n/a"} ms</p>
        </div>
        <div className="border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs uppercase text-slate-500">Finished</p>
          <p className="mt-1 text-lg font-semibold">{formatDate(run.finished_at)}</p>
        </div>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <JsonBlock title="Actual response" value={run.actual_response} />
        <JsonBlock title="Regression diff" value={run.diff_result} />
      </div>
    </Panel>
  );
}

function Panel({ children, subtitle, title }: { children: React.ReactNode; subtitle: string; title: string }) {
  return (
    <section className="border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-sm text-slate-500">{subtitle}</p>
      </div>
      {children}
    </section>
  );
}

function SplitPanel({ left, right }: { left: React.ReactNode; right: React.ReactNode }) {
  return (
    <section className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
      <div className="border border-slate-200 bg-white p-4 shadow-sm">{left}</div>
      {right}
    </section>
  );
}

function Detail({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <aside className="border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold">{title}</h2>
      {children}
    </aside>
  );
}

function Table({ headers, rows }: { headers: string[]; rows: React.ReactNode[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase text-slate-500">
            {headers.map((header) => (
              <th className="px-3 py-2 font-semibold" key={header}>
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr className="border-b border-slate-100 align-top last:border-0" key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td className="max-w-[280px] px-3 py-2" key={cellIndex}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Badge({ value }: { value: string | number }) {
  return (
    <span className={`inline-flex border px-2 py-1 text-xs font-medium ${statusClass(value)}`}>
      {String(value)}
    </span>
  );
}

function KeyValue({ label, value }: { label: string; value: string }) {
  return (
    <div className="mb-2 grid gap-1 text-sm sm:grid-cols-[120px_1fr]">
      <span className="text-slate-500">{label}</span>
      <span className="break-all font-medium text-slate-900">{value}</span>
    </div>
  );
}

function JsonBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="mt-3">
      <h3 className="mb-2 text-sm font-semibold">{title}</h3>
      <pre className="max-h-80 overflow-auto border border-slate-200 bg-slate-50 p-3 text-xs leading-5 text-slate-800">
        {formatJson(value)}
      </pre>
    </div>
  );
}
