import http from "node:http";

const hostname = "127.0.0.1";
const port = 8010;

let scenario = "ready";
let createdRunCount = 0;
let runs = [];

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
  });
  response.end(JSON.stringify(payload));
}

function parseJsonBody(request) {
  return new Promise((resolve, reject) => {
    let body = "";
    request.on("data", (chunk) => {
      body += chunk;
    });
    request.on("end", () => {
      if (!body) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(body));
      } catch (error) {
        reject(error);
      }
    });
    request.on("error", reject);
  });
}

function buildDatasetProfile(datasetPath, tableName) {
  return {
    source_path: datasetPath,
    format: datasetPath.split(".").pop().toLowerCase(),
    table_name: tableName,
    schema: [
      { name: "store", type: "INTEGER" },
      { name: "sales", type: "DOUBLE" },
    ],
    row_count: 2,
  };
}

function createSucceededRun({ runId, sessionId, datasetPath, prompt, createdAt, updatedAt }) {
  const detail = {
    run_id: runId,
    session_id: sessionId,
    agent_id: "data_analyst",
    status: "succeeded",
    created_at: createdAt,
    updated_at: updatedAt,
    dataset_profile: buildDatasetProfile(datasetPath, `dataset_${runId}`),
    result: {
      narrative: `Narrativa UI para: ${prompt}`,
      findings: [
        "Las ventas tienen un pico claro en el primer bloque analizado.",
        "La metrica sales domina el resumen inicial.",
      ],
      sql_trace: [],
      tables: [
        {
          name: "preview",
          rows: [
            { store: 1, sales: 240.5 },
            { store: 2, sales: 310.0 },
          ],
        },
      ],
      charts: [],
      artifact_manifest: {
        run_id: runId,
        response_path: `artifacts/runs/${runId}/response.md`,
        table_paths: [`artifacts/runs/${runId}/tables/preview.json`],
        chart_paths: [],
      },
      recommendations: ["Revisar la distribucion de ventas por tienda."],
    },
    artifact_manifest: {
      run_id: runId,
      response_path: `artifacts/runs/${runId}/response.md`,
      table_paths: [`artifacts/runs/${runId}/tables/preview.json`],
      chart_paths: [],
    },
  };

  return {
    summary: {
      run_id: runId,
      session_id: sessionId,
      agent_id: "data_analyst",
      dataset_path: datasetPath,
      status: "succeeded",
      created_at: createdAt,
      updated_at: updatedAt,
    },
    detail,
    artifacts: [
      {
        name: "response.md",
        type: "response",
        path: `artifacts/runs/${runId}/response.md`,
        run_id: runId,
        size_bytes: 256,
      },
      {
        name: "preview.json",
        type: "table",
        path: `artifacts/runs/${runId}/tables/preview.json`,
        run_id: runId,
        size_bytes: 128,
      },
    ],
  };
}

function createFailedRun({
  runId,
  sessionId,
  datasetPath,
  code,
  message,
  stage,
  createdAt,
  updatedAt,
  includeDatasetProfile = false,
}) {
  const detail = {
    run_id: runId,
    session_id: sessionId,
    agent_id: "data_analyst",
    status: "failed",
    created_at: createdAt,
    updated_at: updatedAt,
    dataset_profile: includeDatasetProfile ? buildDatasetProfile(datasetPath, `dataset_${runId}`) : null,
    result: null,
    error: {
      code,
      message,
      stage,
      details:
        stage === "dataset_preparation"
          ? { dataset_path: datasetPath, category: "dataset" }
          : { provider: "ollama", category: "provider" },
    },
    artifact_manifest: null,
  };

  return {
    summary: {
      run_id: runId,
      session_id: sessionId,
      agent_id: "data_analyst",
      dataset_path: datasetPath,
      status: "failed",
      created_at: createdAt,
      updated_at: updatedAt,
    },
    detail,
    artifacts: [],
  };
}

function buildSeedRuns() {
  return [
    createSucceededRun({
      runId: "run-ui-latest",
      sessionId: "session-ui-001",
      datasetPath: "DatasetV1/Walmart_Sales.csv",
      prompt: "Revisa el run persistido mas reciente",
      createdAt: "2026-04-15T12:00:00Z",
      updatedAt: "2026-04-15T12:00:04Z",
    }),
    createFailedRun({
      runId: "run-ui-failed-history",
      sessionId: "session-ui-000",
      datasetPath: "DatasetV1/missing.csv",
      code: "dataset_path_not_found",
      message: "Dataset path does not exist",
      stage: "dataset_preparation",
      createdAt: "2026-04-15T11:15:00Z",
      updatedAt: "2026-04-15T11:15:02Z",
    }),
  ];
}

function resetState(nextScenario = "ready") {
  scenario = nextScenario;
  createdRunCount = 0;
  runs = buildSeedRuns();
}

function nextRunId(prefix) {
  createdRunCount += 1;
  return `${prefix}-${String(createdRunCount).padStart(3, "0")}`;
}

function listSummaries() {
  return runs.map((run) => run.summary);
}

function findRun(runId) {
  return runs.find((run) => run.summary.run_id === runId) ?? null;
}

function prependRun(run) {
  runs = [run, ...runs];
  return run;
}

resetState();

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url ?? "/", `http://${hostname}:${port}`);
  const pathSegments = url.pathname.split("/").filter(Boolean);

  if (request.method === "POST" && url.pathname === "/__scenario") {
    const payload = await parseJsonBody(request);
    resetState(typeof payload.scenario === "string" ? payload.scenario : "ready");
    sendJson(response, 200, { ok: true, scenario });
    return;
  }

  if (request.method === "GET" && url.pathname === "/health") {
    sendJson(response, 200, {
      status: "ok",
      ready: true,
      default_agent_id: "data_analyst",
      artifacts_root: "artifacts/runs",
      checks: {
        agent_registry: true,
        artifacts_root_writable: true,
        config_available: true,
      },
      details: [],
    });
    return;
  }

  if (request.method === "GET" && url.pathname === "/health/proveedor") {
    if (scenario === "provider_down") {
      sendJson(response, 200, {
        status: "error",
        ready: false,
        proveedor: "ollama",
        endpoint: "http://127.0.0.1:11434",
        binary_available: true,
        binary_path: "C:/Users/manue/AppData/Local/Programs/Ollama/ollama.EXE",
        reachable: false,
        version: null,
        model: "deepseek-r1:8b",
        model_available: false,
        details: ["Ollama no responde en 127.0.0.1:11434."],
      });
      return;
    }

    sendJson(response, 200, {
      status: "ok",
      ready: true,
      proveedor: "ollama",
      endpoint: "http://127.0.0.1:11434",
      binary_available: true,
      binary_path: "C:/Users/manue/AppData/Local/Programs/Ollama/ollama.EXE",
      reachable: true,
      version: "0.18.0",
      model: "deepseek-r1:8b",
      model_available: true,
      details: [],
    });
    return;
  }

  if (request.method === "POST" && url.pathname === "/runs") {
    const payload = await parseJsonBody(request);
    const datasetPath = String(payload.dataset_path ?? "");
    const prompt = String(payload.user_prompt ?? "");
    const agentId = String(payload.agent_id ?? "");

    if (!agentId || !datasetPath || !prompt) {
      sendJson(response, 400, {
        code: "invalid_request",
        message: "Missing required fields",
        status: 400,
        details: {
          category: "request",
          stage: "request_validation",
        },
        trace_id: "mock-trace-validation",
      });
      return;
    }

    if (/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(datasetPath) || !/\.(csv|xlsx|parquet)$/i.test(datasetPath)) {
      sendJson(response, 400, {
        code: "invalid_request",
        message: "dataset_path must use a supported format: csv, xlsx, parquet",
        status: 400,
        details: {
          category: "request",
          stage: "request_validation",
        },
        trace_id: "mock-trace-request-validation",
      });
      return;
    }

    if (scenario === "provider_down") {
      prependRun(
        createFailedRun({
          runId: nextRunId("run-ui-failed"),
          sessionId: "session-ui-provider-down",
          datasetPath,
          code: "llm_provider_unavailable",
          message: "Ollama is unavailable for local generation",
          stage: "agent_execution",
          createdAt: "2026-04-15T12:20:00Z",
          updatedAt: "2026-04-15T12:20:01Z",
          includeDatasetProfile: true,
        }),
      );
      sendJson(response, 503, {
        code: "llm_provider_unavailable",
        message: "Ollama is unavailable for local generation",
        status: 503,
        details: {
          category: "provider",
          stage: "agent_execution",
          context: {
            provider: "ollama",
          },
        },
        trace_id: "mock-trace-provider",
      });
      return;
    }

    if (scenario === "dataset_error" || datasetPath.toLowerCase().includes("missing")) {
      prependRun(
        createFailedRun({
          runId: nextRunId("run-ui-failed"),
          sessionId: "session-ui-dataset-error",
          datasetPath,
          code: "dataset_path_not_found",
          message: "Dataset path does not exist",
          stage: "dataset_preparation",
          createdAt: "2026-04-15T12:25:00Z",
          updatedAt: "2026-04-15T12:25:01Z",
        }),
      );
      sendJson(response, 400, {
        code: "dataset_path_not_found",
        message: "Dataset path does not exist",
        status: 400,
        details: {
          category: "dataset",
          stage: "dataset_preparation",
          context: {
            dataset_path: datasetPath,
          },
        },
        trace_id: "mock-trace-dataset",
      });
      return;
    }

    const createdRun = prependRun(
      createSucceededRun({
        runId: nextRunId("run-ui-created"),
        sessionId: "session-ui-created",
        datasetPath,
        prompt,
        createdAt: "2026-04-15T12:30:00Z",
        updatedAt: "2026-04-15T12:30:03Z",
      }),
    );
    sendJson(response, 200, createdRun.detail);
    return;
  }

  if (request.method === "GET" && pathSegments.length === 1 && pathSegments[0] === "runs") {
    sendJson(response, 200, listSummaries());
    return;
  }

  if (request.method === "GET" && pathSegments.length >= 2 && pathSegments[0] === "runs") {
    const run = findRun(pathSegments[1]);
    if (!run) {
      sendJson(response, 404, {
        code: "run_not_found",
        message: `Run not found: ${pathSegments[1]}`,
        status: 404,
        details: {
          category: "request",
          run_id: pathSegments[1],
        },
        trace_id: "mock-trace-run-not-found",
      });
      return;
    }

    if (pathSegments.length === 2) {
      sendJson(response, 200, run.detail);
      return;
    }

    if (pathSegments.length === 3 && pathSegments[2] === "artifacts") {
      sendJson(response, 200, run.artifacts);
      return;
    }
  }

  sendJson(response, 404, {
    code: "not_found",
    message: "Unknown route",
    status: 404,
    details: {
      category: "core",
      path: url.pathname,
    },
    trace_id: "mock-trace-not-found",
  });
});

server.listen(port, hostname, () => {
  console.log(`Mock API listening on http://${hostname}:${port}`);
});
