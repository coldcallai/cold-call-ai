import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Zap, X, TrendingUp, AlertTriangle } from "lucide-react";
import { Button } from "./ui/button";

const TrialBanner = ({ user }) => {
  const [dismissed, setDismissed] = useState(false);
  const [showUrgent, setShowUrgent] = useState(false);

  const leadCredits = user?.lead_credits_remaining || 0;
  const callCredits = user?.call_credits_remaining || 0;
  const subscriptionTier = user?.subscription_tier || "free";
  
  // Check if user is on free tier
  const isFreeTier = subscriptionTier === "free" || subscriptionTier === "Free";
  
  // Check if credits are low (relative thresholds)
  const lowLeadCredits = leadCredits <= 10;
  const lowCallCredits = callCredits <= 10;
  const isLowCredits = lowLeadCredits || lowCallCredits;
  const isCriticalCredits = leadCredits <= 5 || callCredits <= 5;

  // Check if unlimited/paid tier with lots of credits
  const isUnlimited = subscriptionTier === "unlimited" || subscriptionTier === "enterprise";
  const hasPlentyCredits = leadCredits > 100 && callCredits > 100;

  useEffect(() => {
    // Show urgent banner when credits are critically low
    if (isCriticalCredits) {
      setShowUrgent(true);
    }
  }, [isCriticalCredits]);

  // Don't show banner if dismissed (for this session)
  if (dismissed && !isCriticalCredits) return null;
  
  // Don't show for unlimited users with plenty of credits
  if (isUnlimited && hasPlentyCredits) return null;

  // Urgent/Critical credits banner (red)
  if (showUrgent || isCriticalCredits) {
    return (
      <div className="bg-gradient-to-r from-red-600 to-orange-600 text-white px-4 py-3" data-testid="trial-banner-urgent">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div>
              <p className="font-semibold text-sm">Credits Running Low!</p>
              <p className="text-xs text-white/80">
                {leadCredits} leads & {callCredits} calls remaining. Upgrade to keep calling.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/app/packs">
              <Button 
                size="sm" 
                className="bg-white text-red-600 hover:bg-gray-100 font-semibold"
                data-testid="upgrade-btn-urgent"
              >
                <Zap className="w-4 h-4 mr-1" />
                Upgrade Now
              </Button>
            </Link>
            <button 
              onClick={() => { setDismissed(true); setShowUrgent(false); }}
              className="text-white/70 hover:text-white p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Low credits warning banner (amber)
  if (isLowCredits) {
    return (
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-4 py-2.5" data-testid="trial-banner-warning">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <TrendingUp className="w-5 h-5" />
            <p className="text-sm">
              <span className="font-semibold">Credits running low:</span> {leadCredits} leads & {callCredits} calls left
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/app/packs">
              <Button 
                size="sm" 
                variant="outline"
                className="border-white/50 text-white hover:bg-white/20 bg-transparent text-xs"
                data-testid="upgrade-btn-warning"
              >
                Get More Credits
              </Button>
            </Link>
            <button 
              onClick={() => setDismissed(true)}
              className="text-white/70 hover:text-white p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Free trial info banner (cyan/teal)
  if (isFreeTier) {
    return (
      <div className="bg-gradient-to-r from-cyan-600 to-teal-600 text-white px-4 py-2.5" data-testid="trial-banner-info">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center">
              <Zap className="w-3 h-3" />
            </div>
            <p className="text-sm">
              <span className="font-semibold">Free Trial:</span> {leadCredits} leads & {callCredits} calls remaining
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/app/packs">
              <Button 
                size="sm" 
                className="bg-white text-cyan-700 hover:bg-gray-100 text-xs font-medium"
                data-testid="upgrade-btn-trial"
              >
                <TrendingUp className="w-3 h-3 mr-1" />
                Upgrade Plan
              </Button>
            </Link>
            <button 
              onClick={() => setDismissed(true)}
              className="text-white/70 hover:text-white p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default TrialBanner;
