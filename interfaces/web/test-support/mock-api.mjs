import http from "node:http";

const hostname = "127.0.0.1";
const port = 8010;

let scenario = "ready";

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

function buildRunDetail(datasetPath, prompt) {
  return {
    run_id: "run-ui-success",
    session_id: "session-ui-001",
    agent_id: "data_analyst",
    status: "succeeded",
    created_at: "2026-04-15T12:00:00Z",
    updated_at: "2026-04-15T12:00:04Z",
    dataset_profile: {
      source_path: datasetPath,
      format: datasetPath.split(".").pop().toLowerCase(),
      table_name: "dataset_run_ui_001",
      schema: [
        { name: "store", type: "INTEGER" },
        { name: "sales", type: "DOUBLE" },
      ],
      row_count: 2,
    },
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
        run_id: "run-ui-success",
        response_path: "artifacts/runs/run-ui-success/response.md",
        table_paths: ["artifacts/runs/run-ui-success/tables/preview.json"],
        chart_paths: [],
      },
      recommendations: ["Revisar la distribucion de ventas por tienda."],
    },
    artifact_manifest: {
      run_id: "run-ui-success",
      response_path: "artifacts/runs/run-ui-success/response.md",
      table_paths: ["artifacts/runs/run-ui-success/tables/preview.json"],
      chart_paths: [],
    },
  };
}

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url ?? "/", `http://${hostname}:${port}`);

  if (request.method === "POST" && url.pathname === "/__scenario") {
    const payload = await parseJsonBody(request);
    scenario = typeof payload.scenario === "string" ? payload.scenario : "ready";
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
          stage: "request_validation",
        },
        trace_id: "mock-trace-request-validation",
      });
      return;
    }

    if (scenario === "provider_down") {
      sendJson(response, 503, {
        code: "llm_provider_unavailable",
        message: "Ollama is unavailable for local generation",
        status: 503,
        details: {
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
      sendJson(response, 400, {
        code: "dataset_path_not_found",
        message: "Dataset path does not exist",
        status: 400,
        details: {
          stage: "dataset_preparation",
          context: {
            dataset_path: datasetPath,
          },
        },
        trace_id: "mock-trace-dataset",
      });
      return;
    }

    sendJson(response, 200, buildRunDetail(datasetPath, prompt));
    return;
  }

  if (request.method === "GET" && url.pathname === "/runs/run-ui-success/artifacts") {
    sendJson(response, 200, [
      {
        name: "response.md",
        type: "response",
        path: "artifacts/runs/run-ui-success/response.md",
        run_id: "run-ui-success",
        size_bytes: 256,
      },
      {
        name: "preview.json",
        type: "table",
        path: "artifacts/runs/run-ui-success/tables/preview.json",
        run_id: "run-ui-success",
        size_bytes: 128,
      },
    ]);
    return;
  }

  sendJson(response, 404, {
    code: "not_found",
    message: "Unknown route",
    status: 404,
    details: {
      path: url.pathname,
    },
    trace_id: "mock-trace-not-found",
  });
});

server.listen(port, hostname, () => {
  console.log(`Mock API listening on http://${hostname}:${port}`);
});