/**
 * Ops Center — the platform's operational heads-up display.
 *
 * Each subsystem renders as a single StatusCard. The grid auto-flows so
 * adding a new card requires zero layout work — just drop it into `cards`.
 *
 * Future cards (NOT enabled yet, per scope):
 *   - ElevenLabs       (API reachable, voice latency, last successful synth)
 *   - OpenAI           (API reachable, current model, last completion)
 *   - Twilio           (Voice connected, SMS connected, webhook health)
 *   - Prospecting      (Last run, prospects loaded, dedup complete)
 *   - Campaign Engine  (Active campaign, calls today, transfers, DNC count)
 *   - UniversalBrain   (Active brain, version, loaded successfully)
 *   - System Health    (Backend online, DB connected, queue healthy)
 *
 * Each one plugs in by exporting a component that renders <StatusCard ... />.
 */
import OutboundDialerStatusCard from "@/components/cards/OutboundDialerStatusCard";
import { Activity } from "lucide-react";

const OpsCenterPage = () => {
  const cards = [
    { key: "outbound", el: <OutboundDialerStatusCard /> },
    // Future cards land here — no other layout changes required.
  ];

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8" data-testid="ops-center-page">
      <header className="mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-slate-900 text-white">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h1
              className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900"
              style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
              data-testid="ops-center-title"
            >
              AI Operations Center
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Live health of every engine that powers IntentBrain. Cards auto-refresh every 30 seconds.
            </p>
          </div>
        </div>
      </header>

      <div
        className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 lg:gap-5"
        data-testid="ops-center-grid"
      >
        {cards.map((c) => (
          <div key={c.key}>{c.el}</div>
        ))}
      </div>
    </div>
  );
};

export default OpsCenterPage;
