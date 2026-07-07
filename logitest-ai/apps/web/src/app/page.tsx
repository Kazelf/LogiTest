"use client";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  API_BASE_URL,
  api,
  type ArtifactDetail,
  type GenerateResponse,
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
const LOG_PAGE_SIZE = 100;
const LIST_PAGE_SIZE = 100;
const PIPELINE_BATCH_SIZE = 500;

type Tab = (typeof TABS)[number];
type Notice = { type: "ok" | "error"; text: string } | null;
type PipelineStageStatus = "pending" | "running" | "done" | "failed";
type PipelineStage = { key: string; label: string; status: PipelineStageStatus; detail?: string };
type PipelineSummary = {
  logsProcessed: number;
  journeysDetected: number;
  testCasesGenerated: number;
  testsExecuted: number;
  passedTests: number;
  failedTests: number;
  reportRunId: string | null;
  errorMessage: string | null;
};
type PaginationState = { limit: number; offset: number };
type PaginationProps = PaginationState & {
  total: number;
  onPageChange: (offset: number) => void;
};

const PIPELINE_STAGES: PipelineStage[] = [
  { key: "import", label: "Importing logs", status: "pending" },
  { key: "analyze", label: "Detecting journeys", status: "pending" },
  { key: "generate", label: "Generating test cases", status: "pending" },
  { key: "scripts", label: "Generating test scripts", status: "pending" },
  { key: "run", label: "Running tests", status: "pending" },
  { key: "report", label: "Building regression report", status: "pending" },
];

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

function pageRange({ limit, offset, total }: PaginationState & { total: number }) {
  if (total === 0) {
    return "0 of 0";
  }
  const start = offset + 1;
  const end = Math.min(offset + limit, total);
  return `${start}-${end} of ${total}`;
}

function keepSelection<T>(current: string, items: T[], getId: (item: T) => string) {
  if (items.some((item) => getId(item) === current)) {
    return current;
  }
  return items[0] ? getId(items[0]) : "";
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

function reportDiffs(run: TestRun | null) {
  const diffs = run?.diff_result?.diffs ?? run?.diff_result?.differences;
  return Array.isArray(diffs) ? diffs : [];
}

function ignoredFields(run: TestRun | null) {
  const fields = run?.diff_result?.ignoredFields;
  return Array.isArray(fields) ? fields.map(String) : [];
}

function freshPipelineStages() {
  return PIPELINE_STAGES.map((stage) => ({ ...stage }));
}

function pipelineSummaryText(summary: PipelineSummary) {
  return [
    "Full pipeline completed.",
    `Logs processed: ${summary.logsProcessed}`,
    `Journeys detected: ${summary.journeysDetected}`,
    `Test cases generated: ${summary.testCasesGenerated}`,
    `Tests executed: ${summary.testsExecuted}`,
    `Passed: ${summary.passedTests}`,
    `Failed/Error: ${summary.failedTests}`,
    `Report run: ${summary.reportRunId ?? "n/a"}`,
  ].join("\n");
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("Logs");
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [journeys, setJourneys] = useState<JourneyItem[]>([]);
  const [testCases, setTestCases] = useState<TestCaseItem[]>([]);
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [logPage, setLogPage] = useState<PaginationState>({ limit: LOG_PAGE_SIZE, offset: 0 });
  const [sessionPage, setSessionPage] = useState<PaginationState>({ limit: LIST_PAGE_SIZE, offset: 0 });
  const [journeyPage, setJourneyPage] = useState<PaginationState>({ limit: LIST_PAGE_SIZE, offset: 0 });
  const [testCasePage, setTestCasePage] = useState<PaginationState>({ limit: LIST_PAGE_SIZE, offset: 0 });
  const [runPage, setRunPage] = useState<PaginationState>({ limit: LIST_PAGE_SIZE, offset: 0 });
  const [logTotal, setLogTotal] = useState(0);
  const [sessionTotal, setSessionTotal] = useState(0);
  const [journeyTotal, setJourneyTotal] = useState(0);
  const [testCaseTotal, setTestCaseTotal] = useState(0);
  const [runTotal, setRunTotal] = useState(0);
  const [selectedSessionId, setSelectedSessionId] = useState<string>("");
  const [selectedJourneyId, setSelectedJourneyId] = useState<string>("");
  const [selectedTestCaseId, setSelectedTestCaseId] = useState<string>("");
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [sessionDetail, setSessionDetail] = useState<SessionDetail | null>(null);
  const [testCaseDetail, setTestCaseDetail] = useState<TestCaseDetail | null>(null);
  const [runDetail, setRunDetail] = useState<TestRun | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const [busy, setBusy] = useState<string>("");
  const [statusCopied, setStatusCopied] = useState(false);
  const [pipelineStages, setPipelineStages] = useState<PipelineStage[]>(freshPipelineStages);
  const [pipelineSummary, setPipelineSummary] = useState<PipelineSummary | null>(null);

  const selectedJourney = useMemo(
    () => journeys.find((journey) => journey.id === selectedJourneyId) ?? null,
    [journeys, selectedJourneyId],
  );
  const selectedRun = runDetail ?? runs.find((run) => run.id === selectedRunId) ?? null;
  const latestRun = runs[0] ?? null;
  const artifact = getArtifact(testCaseDetail);
  const pipelineText =
    notice?.text ??
    (pipelineSummary ? pipelineSummaryText(pipelineSummary) : "Ready. Run the full pipeline or use the manual buttons.");

  const setResult = (label: string, result: ImportResponse | { [key: string]: unknown }) => {
    setNotice({ type: "ok", text: `${label}: ${formatJson(result)}` });
  };

  const loadLists = useCallback(async () => {
    const [logList, sessionList, journeyList, testCaseList, runList] = await Promise.all([
      api.listLogs(logPage),
      api.listSessions(sessionPage),
      api.listJourneys(journeyPage),
      api.listTestCases(testCasePage),
      api.listRuns(runPage),
    ]);
    setLogs(logList.items);
    setSessions(sessionList.items);
    setJourneys(journeyList.items);
    setTestCases(testCaseList.items);
    setRuns(runList.items);
    setLogTotal(logList.total);
    setSessionTotal(sessionList.total);
    setJourneyTotal(journeyList.total);
    setTestCaseTotal(testCaseList.total);
    setRunTotal(runList.total);
    setSelectedSessionId((current) =>
      keepSelection(current, sessionList.items, (session) => session.external_session_id),
    );
    setSelectedJourneyId((current) => keepSelection(current, journeyList.items, (journey) => journey.id));
    setSelectedTestCaseId((current) => keepSelection(current, testCaseList.items, (testCase) => testCase.id));
    setSelectedRunId((current) => keepSelection(current, runList.items, (run) => run.id));
  }, [journeyPage, logPage, runPage, sessionPage, testCasePage]);

  const runAction = useCallback(async (label: string, action: () => Promise<unknown>) => {
    setBusy(label);
    setNotice(null);
    setPipelineSummary(null);
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

  const clearDatabase = useCallback(() => {
    if (!window.confirm("Delete all LogiTest database data? This cannot be undone.")) {
      return;
    }
    setSelectedSessionId("");
    setSelectedJourneyId("");
    setSelectedTestCaseId("");
    setSelectedRunId("");
    setSessionDetail(null);
    setTestCaseDetail(null);
    setRunDetail(null);
    void runAction("Clear database", api.clearDatabase);
  }, [runAction]);

  const setPipelineStage = useCallback(
    (key: string, status: PipelineStageStatus, detail?: string) => {
      setPipelineStages((current) =>
        current.map((stage) => (stage.key === key ? { ...stage, status, detail } : stage)),
      );
    },
    [],
  );

  const runFullPipeline = useCallback(async () => {
    setBusy("Run full pipeline");
    setNotice(null);
    setPipelineSummary(null);
    setPipelineStages(freshPipelineStages());
    try {
      setPipelineStage("import", "running");
      const importResult = await api.importElasticsearchLogs({ newOnly: true });
      const logsProcessed = importResult.imported_logs ?? importResult.loaded_records;
      setPipelineStage("import", "done", `${logsProcessed} log(s) from ${importResult.source}`);

      setPipelineStage("analyze", "running");
      const analysis = await api.analyzeJourneys();
      const journeyList = await api.listJourneys({ limit: PIPELINE_BATCH_SIZE, offset: 0 });
      setPipelineStage("analyze", "done", `${journeyList.total} journey(s) detected`);

      if (journeyList.items.length === 0) {
        throw new Error("No journeys were detected from the imported logs.");
      }

      setPipelineStage("generate", "running");
      const generated: GenerateResponse[] = [];
      for (const journey of journeyList.items) {
        generated.push(await api.generateTest(journey.id));
      }
      setPipelineStage("generate", "done", `${generated.length} test case(s) generated`);
      setPipelineStage("scripts", "done", "Jest/Supertest artifacts stored");

      setPipelineStage("run", "running");
      const executed: TestRun[] = [];
      for (const testCase of generated) {
        executed.push(await api.runTestCase(testCase.test_case_id));
      }
      const passedTests = executed.filter((run) => run.status === "passed").length;
      const failedTests = executed.length - passedTests;
      setPipelineStage("run", "done", `${executed.length} test(s) executed`);

      setPipelineStage("report", "running");
      const reportRunId = executed[executed.length - 1]?.id ?? null;
      const summary: PipelineSummary = {
        logsProcessed,
        journeysDetected: analysis.journeys_upserted || journeyList.total,
        testCasesGenerated: generated.length,
        testsExecuted: executed.length,
        passedTests,
        failedTests,
        reportRunId,
        errorMessage: null,
      };
      setPipelineSummary(summary);
      setNotice({ type: failedTests ? "error" : "ok", text: pipelineSummaryText(summary) });
      if (reportRunId) {
        setSelectedRunId(reportRunId);
        setActiveTab("Report");
      }
      setPipelineStage("report", "done", reportRunId ? `Report ${reportRunId.slice(0, 8)}` : "No run report");
      await loadLists();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setNotice({ type: "error", text: `Full pipeline failed: ${message}` });
      setPipelineSummary((current) => ({
        logsProcessed: current?.logsProcessed ?? 0,
        journeysDetected: current?.journeysDetected ?? 0,
        testCasesGenerated: current?.testCasesGenerated ?? 0,
        testsExecuted: current?.testsExecuted ?? 0,
        passedTests: current?.passedTests ?? 0,
        failedTests: current?.failedTests ?? 0,
        reportRunId: current?.reportRunId ?? null,
        errorMessage: message,
      }));
      setPipelineStages((current) =>
        current.map((stage) => (stage.status === "running" ? { ...stage, status: "failed", detail: message } : stage)),
      );
    } finally {
      setBusy("");
    }
  }, [loadLists, setPipelineStage]);

  const copyPipelineStatus = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(pipelineText);
    } catch {
      try {
        const textarea = document.createElement("textarea");
        textarea.value = pipelineText;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        textarea.remove();
      } catch {
        // Clipboard can be blocked in headless browsers.
      }
    } finally {
      setStatusCopied(true);
      window.setTimeout(() => setStatusCopied(false), 1200);
    }
  }, [pipelineText]);

  useEffect(() => {
    let ignore = false;
    Promise.all([
      api.listLogs(logPage),
      api.listSessions(sessionPage),
      api.listJourneys(journeyPage),
      api.listTestCases(testCasePage),
      api.listRuns(runPage),
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
        setLogTotal(logList.total);
        setSessionTotal(sessionList.total);
        setJourneyTotal(journeyList.total);
        setTestCaseTotal(testCaseList.total);
        setRunTotal(runList.total);
        setSelectedSessionId((current) =>
          keepSelection(current, sessionList.items, (session) => session.external_session_id),
        );
        setSelectedJourneyId((current) => keepSelection(current, journeyList.items, (journey) => journey.id));
        setSelectedTestCaseId((current) => keepSelection(current, testCaseList.items, (testCase) => testCase.id));
        setSelectedRunId((current) => keepSelection(current, runList.items, (run) => run.id));
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
  }, [journeyPage, logPage, runPage, sessionPage, testCasePage]);

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
        <Header logs={logTotal} journeys={journeyTotal} tests={testCaseTotal} runs={runTotal} />

        <section className="grid gap-4 border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[1.6fr_1fr]">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <ActionButton disabled={Boolean(busy)} label="Run Full Pipeline" onClick={runFullPipeline} />
              <ActionButton
                disabled={Boolean(busy)}
                label="Import from ES"
                onClick={() =>
                  runAction("Import Elasticsearch logs", () => api.importElasticsearchLogs({ newOnly: true }))
                }
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
              <ActionButton disabled={Boolean(busy)} label="Clear Database" onClick={clearDatabase} variant="danger" />
            </div>
            <p className="mt-3 text-sm text-slate-600">
              API: <span className="font-mono text-slate-900">{API_BASE_URL}</span> · Target:{" "}
              <span className="font-mono text-slate-900">configured by API</span>
            </p>
          </div>
          <div className="border border-slate-200 bg-slate-50 text-sm">
            <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-3 py-2">
              <p className="font-medium text-slate-900">{busy ? `${busy}...` : "Pipeline status"}</p>
              <button
                className="h-8 border border-slate-300 bg-white px-2 text-xs font-medium text-slate-700 hover:bg-slate-100"
                onClick={copyPipelineStatus}
                type="button"
              >
                {statusCopied ? "Copied" : "Copy"}
              </button>
            </div>
            <pre
              className={`max-h-40 overflow-auto whitespace-pre-wrap break-words p-3 text-xs leading-5 ${
                notice?.type === "error" ? "text-rose-700" : "text-slate-600"
              }`}
            >
              {pipelineText}
            </pre>
            <PipelineStages stages={pipelineStages} />
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

        {activeTab === "Logs" ? (
          <LogsPanel
            logs={logs}
            pagination={{
              ...logPage,
              total: logTotal,
              onPageChange: (offset) => setLogPage((current) => ({ ...current, offset })),
            }}
          />
        ) : null}
        {activeTab === "Sessions" ? (
          <SessionsPanel
            detail={sessionDetail}
            pagination={{
              ...sessionPage,
              total: sessionTotal,
              onPageChange: (offset) => setSessionPage((current) => ({ ...current, offset })),
            }}
            selectedId={selectedSessionId}
            sessions={sessions}
            onSelect={setSelectedSessionId}
          />
        ) : null}
        {activeTab === "Journeys" ? (
          <JourneysPanel
            journey={selectedJourney}
            journeys={journeys}
            pagination={{
              ...journeyPage,
              total: journeyTotal,
              onPageChange: (offset) => setJourneyPage((current) => ({ ...current, offset })),
            }}
            selectedId={selectedJourneyId}
            onSelect={setSelectedJourneyId}
          />
        ) : null}
        {activeTab === "Test Cases" ? (
          <TestCasesPanel
            artifact={artifact}
            detail={testCaseDetail}
            pagination={{
              ...testCasePage,
              total: testCaseTotal,
              onPageChange: (offset) => setTestCasePage((current) => ({ ...current, offset })),
            }}
            selectedId={selectedTestCaseId}
            testCases={testCases}
            onSelect={setSelectedTestCaseId}
          />
        ) : null}
        {activeTab === "Runs" ? (
          <RunsPanel
            runs={runs}
            pagination={{
              ...runPage,
              total: runTotal,
              onPageChange: (offset) => setRunPage((current) => ({ ...current, offset })),
            }}
            selectedId={selectedRunId}
            selectedRun={selectedRun}
            onSelect={setSelectedRunId}
          />
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
          Import Elasticsearch logs, mine journeys, generate Jest/Supertest tests, execute against ShopLite, and inspect
          regression diffs from one operational screen.
        </p>
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
  variant = "primary",
}: {
  disabled: boolean;
  label: string;
  onClick: () => void;
  variant?: "primary" | "danger";
}) {
  return (
    <button
      className={`h-9 border px-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:border-slate-300 disabled:bg-slate-200 disabled:text-slate-500 ${
        variant === "danger"
          ? "border-rose-700 bg-rose-700 hover:bg-rose-800"
          : "border-slate-900 bg-slate-950 hover:bg-slate-800"
      }`}
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

function LogsPanel({ logs, pagination }: { logs: LogItem[]; pagination: PaginationProps }) {
  const [selectedLog, setSelectedLog] = useState<LogItem | null>(null);

  if (pagination.total === 0) {
    return <EmptyState label="No logs yet. Run ShopLite journeys, then import logs from Elasticsearch." />;
  }

  const table = (
    <Panel
      title="Raw API Logs"
      subtitle={`Latest normalized requests stored by the platform. Showing ${pageRange(pagination)}.`}
    >
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase text-slate-500">
              {["Time", "Session", "Action", "Method", "Endpoint", "Status", "Latency"].map((header) => (
                <th className="px-3 py-2 font-semibold" key={header}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr
                className={`cursor-pointer border-b border-slate-100 align-top last:border-0 hover:bg-slate-50 ${
                  selectedLog?.id === log.id ? "bg-slate-100" : ""
                }`}
                key={log.id}
                onClick={() => setSelectedLog(log)}
              >
                <td className="max-w-[180px] px-3 py-2">{formatDate(log.occurred_at)}</td>
                <td className="max-w-[220px] break-all px-3 py-2 font-mono text-xs">
                  {log.session_external_id ?? "n/a"}
                </td>
                <td className="max-w-[180px] px-3 py-2">
                  <Badge value={log.action_type || "unknown"} />
                </td>
                <td className="max-w-[90px] px-3 py-2 font-mono">{log.method ?? "n/a"}</td>
                <td className="max-w-[280px] break-all px-3 py-2">{log.endpoint ?? "n/a"}</td>
                <td className="max-w-[90px] px-3 py-2">
                  <Badge value={log.status_code ?? "n/a"} />
                </td>
                <td className="max-w-[110px] px-3 py-2">
                  {log.response_time_ms === null ? "n/a" : `${log.response_time_ms} ms`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <PaginationControls pagination={pagination} />
    </Panel>
  );

  if (!selectedLog) {
    return table;
  }

  return (
    <section className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
      {table}
      <Detail title="Log detail">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="break-all font-mono text-xs text-slate-500">{selectedLog.id}</p>
            <p className="mt-1 break-all text-sm font-semibold text-slate-950">
              {selectedLog.method ?? "n/a"} {selectedLog.endpoint ?? "n/a"}
            </p>
          </div>
          <button
            aria-label="Close log detail"
            className="h-8 w-8 border border-slate-300 text-sm font-semibold text-slate-600 hover:bg-slate-100"
            onClick={() => setSelectedLog(null)}
            type="button"
          >
            X
          </button>
        </div>
        <KeyValue label="Session" value={selectedLog.session_external_id ?? "n/a"} />
        <KeyValue label="Trace" value={selectedLog.trace_id ?? "n/a"} />
        <KeyValue label="User" value={selectedLog.user_id ?? "n/a"} />
        <KeyValue label="Service" value={selectedLog.service_name} />
        <KeyValue label="Action" value={selectedLog.action_type || "unknown"} />
        <KeyValue label="Status" value={String(selectedLog.status_code ?? "n/a")} />
        <JsonBlock title="Request payload" value={selectedLog.request_payload} />
        <JsonBlock title="Response body" value={selectedLog.response_body} />
        <JsonBlock title="Raw log" value={selectedLog.raw_log} />
      </Detail>
    </section>
  );
}

function SessionsPanel({
  detail,
  onSelect,
  pagination,
  selectedId,
  sessions,
}: {
  detail: SessionDetail | null;
  onSelect: (id: string) => void;
  pagination: PaginationProps;
  selectedId: string;
  sessions: SessionItem[];
}) {
  if (pagination.total === 0) {
    return <EmptyState label="No sessions yet. Import logs first." />;
  }
  return (
    <SplitPanel
      left={
        <>
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
          <PaginationControls pagination={pagination} />
        </>
      }
      right={
        <Detail title="Session detail">
          {detail ? (
            <>
              <KeyValue label="External ID" value={detail.session.external_session_id} />
              <KeyValue label="Services" value={detail.session.services?.join(", ") || "n/a"} />
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
  pagination,
  selectedId,
}: {
  journey: JourneyItem | null;
  journeys: JourneyItem[];
  onSelect: (id: string) => void;
  pagination: PaginationProps;
  selectedId: string;
}) {
  if (pagination.total === 0) {
    return <EmptyState label="No journeys yet. Import logs, then run behavior analysis." />;
  }
  const proofRows = journey ? chainingRows(journey.steps) : [];
  return (
    <SplitPanel
      left={
        <>
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
          <PaginationControls pagination={pagination} />
        </>
      }
      right={
        <Detail title="Journey detail">
          {journey ? (
            <>
              <KeyValue label="Example session" value={journey.example_session_id ?? "n/a"} />
              <KeyValue label="Frequency" value={String(journey.frequency_score ?? "n/a")} />
              <h3 className="mt-4 text-sm font-semibold">Behavior explanation</h3>
              <div className="mt-2 border border-slate-200 bg-slate-50 p-3 text-sm">
                <KeyValue label="Behavior" value={journey.behavior_analysis.behaviorName ?? journey.name} />
                <KeyValue label="Type" value={journey.behavior_analysis.behaviorType ?? "normal"} />
                <KeyValue label="Goal" value={journey.behavior_analysis.userGoal ?? journey.description ?? "n/a"} />
                <KeyValue
                  label="AI"
                  value={`${journey.behavior_analysis.ai_provider ?? "rule_based"}${
                    journey.behavior_analysis.ai_model ? ` / ${journey.behavior_analysis.ai_model}` : ""
                  }${journey.behavior_analysis.fallback_used ? " / fallback" : ""}`}
                />
                <KeyValue label="Prompt" value={journey.behavior_analysis.prompt_version ?? "n/a"} />
                <ol className="mt-2 space-y-2">
                  {(journey.behavior_analysis.stepSummary ?? []).map((step) => (
                    <li className="border border-slate-200 bg-white p-2" key={`${step.step}-${step.api}`}>
                      <p className="font-mono text-xs">{step.api}</p>
                      <p className="mt-1">{step.meaning}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        Payload: {(step.importantPayload ?? []).join(", ") || "none"} · Response:{" "}
                        {(step.importantResponse ?? []).join(", ") || "n/a"}
                      </p>
                      {step.inputFromPreviousStep ? (
                        <p className="mt-1 text-xs text-slate-600">Uses: {step.inputFromPreviousStep}</p>
                      ) : null}
                    </li>
                  ))}
                </ol>
              </div>
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
  pagination,
  selectedId,
  testCases,
}: {
  artifact: ArtifactDetail | null;
  detail: TestCaseDetail | null;
  onSelect: (id: string) => void;
  pagination: PaginationProps;
  selectedId: string;
  testCases: TestCaseItem[];
}) {
  if (pagination.total === 0) {
    return <EmptyState label="No generated tests yet. Select a journey and generate Jest/Supertest." />;
  }
  return (
    <SplitPanel
      left={
        <>
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
          <PaginationControls pagination={pagination} />
        </>
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
  pagination,
  runs,
  selectedId,
  selectedRun,
}: {
  onSelect: (id: string) => void;
  pagination: PaginationProps;
  runs: TestRun[];
  selectedId: string;
  selectedRun: TestRun | null;
}) {
  if (pagination.total === 0) {
    return <EmptyState label="No runs yet. Generate a test case, then run it against ShopLite." />;
  }
  return (
    <SplitPanel
      left={
        <>
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
          <PaginationControls pagination={pagination} />
        </>
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
  const diffs = reportDiffs(run);
  const ignored = ignoredFields(run);
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
      <div className="mt-4 border border-slate-200 bg-white">
        <div className="border-b border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold">Deterministic diffs</div>
        {diffs.length ? (
          <Table
            headers={["Type", "Path", "Expected", "Actual", "Severity"]}
            rows={diffs.map((diff, index) => {
              const item = diff as Record<string, unknown>;
              return [
                String(item.type ?? "diff"),
                <span className="font-mono text-xs" key={`path-${index}`}>{String(item.path ?? "n/a")}</span>,
                <span className="font-mono text-xs" key={`expected-${index}`}>{formatJson(item.expected)}</span>,
                <span className="font-mono text-xs" key={`actual-${index}`}>{formatJson(item.actual)}</span>,
                <Badge key={`severity-${index}`} value={String(item.severity ?? "medium")} />,
              ];
            })}
          />
        ) : (
          <p className="p-3 text-sm text-slate-500">No diffs for this run.</p>
        )}
      </div>
      <div className="mt-4 border border-slate-200 bg-slate-50 p-3 text-sm">
        <p className="font-semibold">Ignored dynamic fields</p>
        <p className="mt-1 font-mono text-xs text-slate-700">{ignored.length ? ignored.join(", ") : "none"}</p>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <JsonBlock title="Actual response" value={run.actual_response} />
        <JsonBlock title="Regression diff" value={run.diff_result} />
      </div>
    </Panel>
  );
}

function PaginationControls({ pagination }: { pagination: PaginationProps }) {
  const previousOffset = Math.max(0, pagination.offset - pagination.limit);
  const nextOffset = pagination.offset + pagination.limit;
  const hasPrevious = pagination.offset > 0;
  const hasNext = nextOffset < pagination.total;

  return (
    <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3 text-sm text-slate-600">
      <span>{pageRange(pagination)}</span>
      <div className="flex gap-2">
        <button
          className="h-8 border border-slate-300 px-3 font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
          disabled={!hasPrevious}
          onClick={() => pagination.onPageChange(previousOffset)}
          type="button"
        >
          Previous
        </button>
        <button
          className="h-8 border border-slate-300 px-3 font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
          disabled={!hasNext}
          onClick={() => pagination.onPageChange(nextOffset)}
          type="button"
        >
          Next
        </button>
      </div>
    </div>
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

function PipelineStages({ stages }: { stages: PipelineStage[] }) {
  return (
    <ol className="grid gap-1 border-t border-slate-200 p-3">
      {stages.map((stage) => (
        <li className="flex items-center justify-between gap-3 text-xs" key={stage.key}>
          <span className="text-slate-700">{stage.label}</span>
          <span className="flex items-center gap-2 text-right">
            {stage.detail ? <span className="hidden max-w-48 truncate text-slate-500 sm:inline">{stage.detail}</span> : null}
            <Badge value={stage.status} />
          </span>
        </li>
      ))}
    </ol>
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
