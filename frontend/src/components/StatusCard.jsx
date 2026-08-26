/**
 * StatusCard — reusable health-status card for the AI Operations Center.
 *
 * Every operational subsystem (Outbound Dialer, ElevenLabs, OpenAI, Twilio,
 * Prospecting Engine, UniversalBrain, etc.) plugs into the same dashboard by
 * supplying one async `fetchStatus()` function. This keeps the dashboard
 * uniform and lets new engines onboard in ~30 lines.
 *
 * fetchStatus contract — return an object shaped like:
 *   {
 *     status: 'safe' | 'warn' | 'down' | 'unknown',
 *     label:  'SAFE' | 'DEGRADED' | 'DISABLED' | 'UNKNOWN' | string,
 *     reason: string,
 *     metrics: [{ label: string, value: string | number }, ...]
 *   }
 *
 * Polling: defaults to every 30 seconds. Pauses while the tab is hidden.
 */
import { useEffect, useRef, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, RefreshCw, CircleAlert, CircleCheck, CircleHelp, CircleOff } from "lucide-react";

const STATUS_STYLES = {
  safe:    { dot: "bg-emerald-500",   ring: "ring-emerald-500/20", badge: "bg-emerald-50 text-emerald-700 border-emerald-200",  Icon: CircleCheck, defaultLabel: "SAFE" },
  warn:    { dot: "bg-amber-500",     ring: "ring-amber-500/20",   badge: "bg-amber-50 text-amber-700 border-amber-200",        Icon: CircleAlert, defaultLabel: "DEGRADED" },
  down:    { dot: "bg-rose-500",      ring: "ring-rose-500/20",    badge: "bg-rose-50 text-rose-700 border-rose-200",           Icon: CircleOff,   defaultLabel: "DISABLED" },
  unknown: { dot: "bg-slate-400",     ring: "ring-slate-400/20",   badge: "bg-slate-50 text-slate-700 border-slate-200",        Icon: CircleHelp,  defaultLabel: "UNKNOWN" },
};

const _fmtRelative = (iso) => {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return iso;
  const diff = Date.now() - t;
  if (diff < 0) return new Date(iso).toLocaleTimeString();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return new Date(iso).toLocaleDateString();
};

export const formatRelativeTime = _fmtRelative;

const StatusCard = ({
  title,
  icon: TitleIcon,
  fetchStatus,
  intervalMs = 30000,
  testId,
  helpHref,
}) => {
  const [state, setState] = useState({ status: "unknown", label: "LOADING…", reason: "", metrics: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);
  const timerRef = useRef(null);
  const mountedRef = useRef(true);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const result = await fetchStatus();
      if (!mountedRef.current) return;
      const status = ["safe", "warn", "down", "unknown"].includes(result?.status) ? result.status : "unknown";
      setState({
        status,
        label: result?.label || STATUS_STYLES[status].defaultLabel,
        reason: result?.reason || "",
        metrics: Array.isArray(result?.metrics) ? result.metrics : [],
      });
      setLastChecked(new Date().toISOString());
    } catch (e) {
      if (!mountedRef.current) return;
      setError(e?.message || "Failed to fetch status");
      setState((s) => ({ ...s, status: "unknown", label: "UNREACHABLE" }));
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [fetchStatus]);

  // Initial fetch + poll loop
  useEffect(() => {
    mountedRef.current = true;
    refresh();
    const tick = () => {
      if (!document.hidden) refresh();
    };
    timerRef.current = setInterval(tick, intervalMs);
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [refresh, intervalMs]);

  // Refresh on tab refocus so the user always sees fresh state when they look
  useEffect(() => {
    const onVis = () => { if (!document.hidden) refresh(); };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, [refresh]);

  const style = STATUS_STYLES[state.status] || STATUS_STYLES.unknown;
  const StatusIcon = style.Icon;

  return (
    <Card
      data-testid={testId}
      data-status={state.status}
      className={`relative overflow-hidden border-2 ring-1 ${style.ring} hover:shadow-md transition-shadow`}
    >
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${style.dot}`} aria-hidden="true" />
      <CardHeader className="pb-3 pl-5">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            {TitleIcon ? <TitleIcon className="w-5 h-5 text-slate-600 shrink-0" /> : null}
            <CardTitle
              className="text-base font-semibold tracking-tight text-slate-900 truncate"
              data-testid={testId ? `${testId}-title` : undefined}
            >
              {title}
            </CardTitle>
          </div>
          <Badge
            variant="outline"
            className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 ${style.badge}`}
            data-testid={testId ? `${testId}-badge` : undefined}
          >
            <StatusIcon className="w-3.5 h-3.5" />
            {state.label}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pl-5 pb-4">
        {error ? (
          <p className="text-sm text-rose-600" data-testid={testId ? `${testId}-error` : undefined}>
            {error}
          </p>
        ) : (
          <>
            <p
              className="text-sm text-slate-600 leading-relaxed min-h-[2.5rem]"
              data-testid={testId ? `${testId}-reason` : undefined}
            >
              {state.reason || (loading ? "Checking…" : "—")}
            </p>

            {state.metrics?.length ? (
              <dl
                className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2"
                data-testid={testId ? `${testId}-metrics` : undefined}
              >
                {state.metrics.map((m, i) => (
                  <div key={i} className="min-w-0">
                    <dt className="text-[11px] uppercase tracking-wide text-slate-400 font-medium truncate">
                      {m.label}
                    </dt>
                    <dd
                      className="text-sm font-medium text-slate-800 truncate"
                      data-testid={testId ? `${testId}-metric-${m.label?.toLowerCase().replace(/\s+/g, "-")}` : undefined}
                    >
                      {m.value ?? "—"}
                    </dd>
                  </div>
                ))}
              </dl>
            ) : null}
          </>
        )}

        <div className="mt-4 flex items-center justify-between text-[11px] text-slate-400">
          <span data-testid={testId ? `${testId}-last-checked` : undefined}>
            Checked {_fmtRelative(lastChecked)}
          </span>
          <button
            type="button"
            onClick={refresh}
            className="inline-flex items-center gap-1 text-slate-500 hover:text-slate-800 transition-colors"
            data-testid={testId ? `${testId}-refresh` : undefined}
            aria-label="Refresh status"
          >
            {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
            Refresh
          </button>
        </div>

        {helpHref ? (
          <a
            href={helpHref}
            className="absolute right-2 top-2 text-[11px] text-slate-400 hover:text-slate-600"
            target="_blank"
            rel="noreferrer"
            data-testid={testId ? `${testId}-help` : undefined}
          >
            docs
          </a>
        ) : null}
      </CardContent>
    </Card>
  );
};

export default StatusCard;
