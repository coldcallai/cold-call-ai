/**
 * ElevenLabsStatusCard — voice synthesis health.
 *
 * Polls GET /api/admin/elevenlabs-status. The backend uses cached metadata
 * from real production synth calls + a rate-limited reachability ping — it
 * NEVER synthesizes audio on poll. No API keys / voice IDs in response.
 */
import { Volume2 } from "lucide-react";
import StatusCard, { formatRelativeTime } from "@/components/StatusCard";

const API_BASE = process.env.REACT_APP_BACKEND_URL || "";

const fetchElevenLabsStatus = async () => {
  const resp = await fetch(`${API_BASE}/api/admin/elevenlabs-status`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}`);
  }
  const data = await resp.json();

  // Pass-through status — backend already classifies as safe/warn/down/unknown.
  const status = ["safe", "warn", "down", "unknown"].includes(data.status) ? data.status : "unknown";
  const label =
    status === "safe" ? "SAFE" :
    status === "warn" ? "DEGRADED" :
    status === "down" ? "DOWN" : "UNKNOWN";

  const latency = Number.isFinite(data.last_synth_latency_ms) ? data.last_synth_latency_ms : null;
  // Treat 0 as "no data" — backend reports 0 when no synth event has been recorded yet.
  const latencyDisplay = latency != null && latency > 0 ? `${latency} ms` : "—";

  return {
    status,
    label,
    reason: data.reason || "",
    metrics: [
      { label: "API reachable", value: data.api_reachable ? "yes" : "no" },
      { label: "Last synth",    value: formatRelativeTime(data.last_synth_at) },
      { label: "Last latency",  value: latencyDisplay },
      { label: "Last success",  value: formatRelativeTime(data.last_successful_synth_at) },
    ],
  };
};

const ElevenLabsStatusCard = () => (
  <StatusCard
    title="ElevenLabs"
    icon={Volume2}
    fetchStatus={fetchElevenLabsStatus}
    intervalMs={30000}
    testId="status-card-elevenlabs"
  />
);

export default ElevenLabsStatusCard;
