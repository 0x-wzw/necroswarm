"use client";

import { useCallback, useEffect, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PipelineStage {
  name: string;
  status: "pending" | "running" | "success" | "failed" | "skipped";
  duration?: string;
  detail?: string;
}

interface PipelineRun {
  id: string;
  branch: string;
  commit: string;
  trigger: "push" | "pull_request" | "manual";
  status: "pending" | "running" | "success" | "failed";
  stages: PipelineStage[];
  started_at: string;
  completed_at?: string;
}

interface DeployRecord {
  deploy_id: string;
  environment: string;
  status: "success" | "failed" | "rolled_back";
  triggered_at: string;
  completed_at?: string;
}

interface NECROSWARMHealth {
  reachable: boolean;
  tools_count?: number;
  error?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_COLORS: Record<string, string> = {
  pending: "#6b7280",
  running: "#2563eb",
  success: "#16a34a",
  failed: "#dc2626",
  skipped: "#9ca3af",
  rolled_back: "#f59e0b",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 12,
        fontSize: 12,
        fontWeight: 600,
        color: "#fff",
        backgroundColor: STATUS_COLORS[status] ?? "#6b7280",
      }}
    >
      {status}
    </span>
  );
}

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        padding: 20,
        marginBottom: 24,
        background: "#fff",
      }}
    >
      <h2 style={{ margin: "0 0 16px", fontSize: 18, fontWeight: 600 }}>
        {title}
      </h2>
      {children}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Demo seed data (replaced by real API calls in production)
// ---------------------------------------------------------------------------

function seedPipelineRuns(): PipelineRun[] {
  return [
    {
      id: "ci-100",
      branch: "main",
      commit: "a3223a6",
      trigger: "push",
      status: "success",
      started_at: new Date(Date.now() - 3600_000).toISOString(),
      completed_at: new Date(Date.now() - 3480_000).toISOString(),
      stages: [
        { name: "Lint & Typecheck", status: "success", duration: "32s" },
        { name: "Build", status: "success", duration: "58s" },
        { name: "Deploy Staging", status: "success", duration: "24s" },
        {
          name: "Deploy Production",
          status: "skipped",
          detail: "Manual gate",
        },
      ],
    },
    {
      id: "ci-99",
      branch: "feature/necroswarm",
      commit: "4717fd4",
      trigger: "pull_request",
      status: "running",
      started_at: new Date(Date.now() - 120_000).toISOString(),
      stages: [
        { name: "Lint & Typecheck", status: "success", duration: "29s" },
        { name: "Build", status: "running" },
        { name: "Deploy Staging", status: "pending" },
        { name: "Deploy Production", status: "pending" },
      ],
    },
  ];
}

function seedDeployments(): DeployRecord[] {
  return [
    {
      deploy_id: "ci-100",
      environment: "staging",
      status: "success",
      triggered_at: new Date(Date.now() - 3500_000).toISOString(),
      completed_at: new Date(Date.now() - 3480_000).toISOString(),
    },
    {
      deploy_id: "ci-98",
      environment: "production",
      status: "success",
      triggered_at: new Date(Date.now() - 86400_000).toISOString(),
      completed_at: new Date(Date.now() - 86380_000).toISOString(),
    },
  ];
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function CICDPage() {
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [deploys, setDeploys] = useState<DeployRecord[]>([]);
  const [necroswarm, setNECROSWARM] = useState<NECROSWARMHealth | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const refresh = useCallback(async () => {
    setRefreshing(true);

    // Pipeline runs – seed data (swap with real GitHub Actions API call)
    setRuns(seedPipelineRuns());
    setDeploys(seedDeployments());

    // NECROSWARM health check
    try {
      const res = await fetch("/api/necroswarm");
      if (res.ok) {
        const data = await res.json();
        setNECROSWARM({
          reachable: true,
          tools_count: data.tools?.length ?? 0,
        });
      } else {
        setNECROSWARM({ reachable: false, error: `HTTP ${res.status}` });
      }
    } catch (e) {
      setNECROSWARM({
        reachable: false,
        error: (e as Error).message,
      });
    }

    setRefreshing(false);
  }, []);

  useEffect(() => {
    refresh();
    const iv = setInterval(refresh, 30_000);
    return () => clearInterval(iv);
  }, [refresh]);

  return (
    <main
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: "32px 16px",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        color: "#1f2937",
      }}
    >
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 32,
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: 24 }}>CI/CD Dashboard</h1>
          <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: 14 }}>
            Light Agentic Agent &mdash; Pipeline &amp; Deployments
          </p>
        </div>
        <button
          onClick={refresh}
          disabled={refreshing}
          style={{
            padding: "8px 16px",
            borderRadius: 6,
            border: "1px solid #d1d5db",
            background: refreshing ? "#f3f4f6" : "#fff",
            cursor: refreshing ? "default" : "pointer",
            fontSize: 14,
          }}
        >
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      {/* ── Service health ───────────────────────────────────── */}
      <Card title="Service Health">
        <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
          <HealthTile
            name="Agent API"
            ok={true}
            detail="localhost:3000"
          />
          <HealthTile
            name="NECROSWARM"
            ok={necroswarm?.reachable ?? false}
            detail={
              necroswarm?.reachable
                ? `${necroswarm.tools_count} tools available`
                : necroswarm?.error ?? "Checking..."
            }
          />
        </div>
      </Card>

      {/* ── Pipeline runs ────────────────────────────────────── */}
      <Card title="Pipeline Runs">
        {runs.length === 0 ? (
          <p style={{ color: "#9ca3af" }}>No pipeline runs yet.</p>
        ) : (
          <table
            style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}
          >
            <thead>
              <tr
                style={{
                  textAlign: "left",
                  borderBottom: "2px solid #e5e7eb",
                }}
              >
                <th style={{ padding: "8px 4px" }}>Run</th>
                <th style={{ padding: "8px 4px" }}>Branch</th>
                <th style={{ padding: "8px 4px" }}>Commit</th>
                <th style={{ padding: "8px 4px" }}>Trigger</th>
                <th style={{ padding: "8px 4px" }}>Status</th>
                <th style={{ padding: "8px 4px" }}>Stages</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr
                  key={run.id}
                  style={{ borderBottom: "1px solid #f3f4f6" }}
                >
                  <td style={{ padding: "10px 4px", fontFamily: "monospace" }}>
                    {run.id}
                  </td>
                  <td style={{ padding: "10px 4px" }}>{run.branch}</td>
                  <td
                    style={{ padding: "10px 4px", fontFamily: "monospace" }}
                  >
                    {run.commit.slice(0, 7)}
                  </td>
                  <td style={{ padding: "10px 4px" }}>{run.trigger}</td>
                  <td style={{ padding: "10px 4px" }}>
                    <StatusBadge status={run.status} />
                  </td>
                  <td style={{ padding: "10px 4px" }}>
                    <StagePills stages={run.stages} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* ── Deployments ──────────────────────────────────────── */}
      <Card title="Recent Deployments">
        {deploys.length === 0 ? (
          <p style={{ color: "#9ca3af" }}>No deployments recorded.</p>
        ) : (
          <table
            style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}
          >
            <thead>
              <tr
                style={{
                  textAlign: "left",
                  borderBottom: "2px solid #e5e7eb",
                }}
              >
                <th style={{ padding: "8px 4px" }}>ID</th>
                <th style={{ padding: "8px 4px" }}>Environment</th>
                <th style={{ padding: "8px 4px" }}>Status</th>
                <th style={{ padding: "8px 4px" }}>Triggered</th>
              </tr>
            </thead>
            <tbody>
              {deploys.map((d) => (
                <tr
                  key={d.deploy_id + d.environment}
                  style={{ borderBottom: "1px solid #f3f4f6" }}
                >
                  <td style={{ padding: "10px 4px", fontFamily: "monospace" }}>
                    {d.deploy_id}
                  </td>
                  <td style={{ padding: "10px 4px" }}>{d.environment}</td>
                  <td style={{ padding: "10px 4px" }}>
                    <StatusBadge status={d.status} />
                  </td>
                  <td style={{ padding: "10px 4px" }}>
                    {new Date(d.triggered_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* ── Pipeline workflow ────────────────────────────────── */}
      <Card title="Pipeline Workflow">
        <PipelineVisual />
      </Card>
    </main>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function HealthTile({
  name,
  ok,
  detail,
}: {
  name: string;
  ok: boolean;
  detail: string;
}) {
  return (
    <div
      style={{
        padding: "12px 20px",
        border: `1px solid ${ok ? "#bbf7d0" : "#fecaca"}`,
        borderRadius: 8,
        background: ok ? "#f0fdf4" : "#fef2f2",
        minWidth: 180,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{name}</div>
      <div style={{ fontSize: 13, color: ok ? "#15803d" : "#b91c1c" }}>
        {ok ? "Healthy" : "Unreachable"} &mdash; {detail}
      </div>
    </div>
  );
}

function StagePills({ stages }: { stages: PipelineStage[] }) {
  return (
    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
      {stages.map((s) => (
        <span
          key={s.name}
          title={`${s.name}${s.duration ? ` (${s.duration})` : ""}${s.detail ? ` – ${s.detail}` : ""}`}
          style={{
            display: "inline-block",
            width: 14,
            height: 14,
            borderRadius: "50%",
            backgroundColor: STATUS_COLORS[s.status] ?? "#6b7280",
          }}
        />
      ))}
    </div>
  );
}

function PipelineVisual() {
  const stages = [
    {
      name: "Lint & Typecheck",
      desc: "ESLint + tsc --noEmit",
    },
    {
      name: "Build",
      desc: "next build",
    },
    {
      name: "Deploy Staging",
      desc: "Auto on main push",
    },
    {
      name: "Deploy Production",
      desc: "Manual approval gate",
    },
  ];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 0,
        overflowX: "auto",
        padding: "8px 0",
      }}
    >
      {stages.map((s, i) => (
        <div key={s.name} style={{ display: "flex", alignItems: "center" }}>
          <div
            style={{
              padding: "12px 18px",
              border: "1px solid #d1d5db",
              borderRadius: 8,
              background: "#f9fafb",
              textAlign: "center",
              minWidth: 140,
            }}
          >
            <div style={{ fontWeight: 600, fontSize: 13 }}>{s.name}</div>
            <div style={{ fontSize: 11, color: "#6b7280", marginTop: 4 }}>
              {s.desc}
            </div>
          </div>
          {i < stages.length - 1 && (
            <div
              style={{
                width: 32,
                height: 2,
                background: "#d1d5db",
                flexShrink: 0,
              }}
            />
          )}
        </div>
      ))}
    </div>
  );
}
