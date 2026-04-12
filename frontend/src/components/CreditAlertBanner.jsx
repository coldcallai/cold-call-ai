import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { AlertTriangle, X, ExternalLink } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;
const CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutes

const CreditAlertBanner = ({ user }) => {
  const [alerts, setAlerts] = useState([]);
  const [dismissed, setDismissed] = useState({});

  const checkBalances = useCallback(async () => {
    if (!user) return;
    try {
      const token = localStorage.getItem("session_token");
      if (!token) return;
      const { data } = await axios.get(`${API}/api/settings/integrations/balances`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const newAlerts = [];
      if (data.twilio?.low) {
        newAlerts.push({
          id: "twilio",
          message: `Twilio balance is low: $${data.twilio.balance.toFixed(2)}`,
          link: "https://console.twilio.com/us1/billing/manage-billing/billing",
          linkText: "Add funds"
        });
      }
      if (data.elevenlabs?.low) {
        newAlerts.push({
          id: "elevenlabs",
          message: `ElevenLabs credits running low: ${data.elevenlabs.remaining_percent}% remaining`,
          link: "https://elevenlabs.io/subscription",
          linkText: "Upgrade plan"
        });
      }
      setAlerts(newAlerts);
    } catch {
      // silently fail
    }
  }, [user]);

  useEffect(() => {
    checkBalances();
    const interval = setInterval(checkBalances, CHECK_INTERVAL);
    return () => clearInterval(interval);
  }, [checkBalances]);

  const visibleAlerts = alerts.filter((a) => !dismissed[a.id]);
  if (visibleAlerts.length === 0) return null;

  return (
    <div className="w-full" data-testid="credit-alert-banner">
      {visibleAlerts.map((alert) => (
        <div
          key={alert.id}
          data-testid={`credit-alert-${alert.id}`}
          className="bg-amber-50 border-b border-amber-200 px-4 py-2 flex items-center justify-between text-sm"
        >
          <div className="flex items-center gap-2 text-amber-800">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{alert.message}</span>
            <a
              href={alert.link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 font-medium text-amber-900 hover:underline ml-1"
            >
              {alert.linkText} <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          <button
            onClick={() => setDismissed((d) => ({ ...d, [alert.id]: true }))}
            className="text-amber-600 hover:text-amber-800 ml-4"
            data-testid={`dismiss-alert-${alert.id}`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
};

export default CreditAlertBanner;
