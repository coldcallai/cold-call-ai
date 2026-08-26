/**
 * OutboundDialerStatusCard — first concrete card for the AI Operations Center.
 *
 * Polls GET /api/admin/outbound-status (no secrets exposed) and renders the
 * dialer's safety state. Other engine cards follow this exact pattern.
 */
import { Phone } from "lucide-react";
import StatusCard, { formatRelativeTime } from "@/components/StatusCard";

const API_BASE = process.env.REACT_APP_BACKEND_URL || "";

const fetchOutboundStatus = async () => {
  const resp = await fetch(`${API_BASE}/api/admin/outbound-status`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}`);
  }
  const data = await resp.json();

  // Translate the backend's 4 decision states into StatusCard's 4 visual states.
  let status = "unknown";
  let label = "UNKNOWN";
  if (data.can_live_dial === true) {
    status = "safe";
    label = "SAFE";
  } else if (data.kill_switch_present === true) {
    status = "down";
    label = "DISABLED";
  } else if (data.last_selftest_passed === false) {
    status = "down";
    label = "DISABLED";
  } else {
    status = "warn";
    label = "UNVERIFIED";
  }

  return {
    status,
    label,
    reason: data.reason || "",
    metrics: [
      { label: "Kill switch",     value: data.kill_switch_present ? "PRESENT" : "absent" },
      { label: "Last self-test",  value: formatRelativeTime(data.last_selftest_at) },
      { label: "Self-test result", value:
          data.last_selftest_passed === true  ? "passed" :
          data.last_selftest_passed === false ? "failed" : "—" },
      { label: "Can live dial",   value: data.can_live_dial ? "yes" : "no" },
    ],
  };
};

const OutboundDialerStatusCard = () => (
  <StatusCard
    title="Outbound Dialer"
    icon={Phone}
    fetchStatus={fetchOutboundStatus}
    intervalMs={30000}
    testId="status-card-outbound"
  />
);

export default OutboundDialerStatusCard;
