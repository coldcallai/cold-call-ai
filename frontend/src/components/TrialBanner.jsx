import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Zap, X, TrendingUp, AlertTriangle, Clock, Timer } from "lucide-react";
import { Button } from "./ui/button";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TrialBanner = ({ user }) => {
  const [dismissed, setDismissed] = useState(false);
  const [trialStatus, setTrialStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const subscriptionTier = user?.subscription_tier;
  
  // Fetch trial status on mount
  useEffect(() => {
    const fetchTrialStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/api/user/trial-status`, {
          credentials: "include"
        });
        if (response.ok) {
          const data = await response.json();
          setTrialStatus(data);
        }
      } catch (error) {
        console.error("Failed to fetch trial status:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrialStatus();
  }, []);

  // Format time remaining
  const formatTimeRemaining = (minutes) => {
    if (minutes >= 60) {
      const hours = Math.floor(minutes / 60);
      const mins = Math.round(minutes % 60);
      return `${hours}h ${mins}m`;
    }
    if (minutes >= 1) {
      return `${Math.round(minutes)} min`;
    }
    const seconds = Math.round(minutes * 60);
    return `${seconds} sec`;
  };

  // Check if user is on a paid tier
  const isPaidTier = subscriptionTier && !["free", "free_trial", null].includes(subscriptionTier);

  // Don't show banner if dismissed (for this session) or still loading
  if (loading) return null;
  if (dismissed && !trialStatus?.trial_expired) return null;
  
  // Don't show for paid users
  if (isPaidTier) return null;

  // Trial expired banner (red) - shows upgrade prompt
  if (trialStatus?.trial_expired) {
    return (
      <div className="bg-gradient-to-r from-red-600 to-orange-600 text-white px-4 py-3" data-testid="trial-banner-expired">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div>
              <p className="font-semibold text-sm">Free Trial Expired</p>
              <p className="text-xs text-white/80">
                You've used all {trialStatus.minutes_total} minutes of your free trial. Upgrade to continue making AI calls.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/app/packs">
              <Button 
                size="sm" 
                className="bg-white text-red-600 hover:bg-gray-100 font-semibold"
                data-testid="upgrade-btn-expired"
              >
                <Zap className="w-4 h-4 mr-1" />
                Upgrade Now
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Trial user with time remaining
  if (trialStatus?.is_trial && !trialStatus?.trial_expired) {
    const minutesRemaining = trialStatus.minutes_remaining || 0;
    const usagePercent = trialStatus.usage_percent || 0;
    const isCritical = minutesRemaining <= 3; // Less than 3 minutes
    const isLow = minutesRemaining <= 7 && minutesRemaining > 3; // 3-7 minutes

    // Critical warning (less than 3 minutes)
    if (isCritical) {
      return (
        <div className="bg-gradient-to-r from-red-600 to-orange-600 text-white px-4 py-3" data-testid="trial-banner-critical">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center animate-pulse">
                <Timer className="w-4 h-4" />
              </div>
              <div>
                <p className="font-semibold text-sm">Trial Almost Over!</p>
                <p className="text-xs text-white/80">
                  Only {formatTimeRemaining(minutesRemaining)} remaining. Upgrade before your trial ends.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Link to="/app/packs">
                <Button 
                  size="sm" 
                  className="bg-white text-red-600 hover:bg-gray-100 font-semibold"
                  data-testid="upgrade-btn-critical"
                >
                  <Zap className="w-4 h-4 mr-1" />
                  Upgrade Now
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

    // Low time warning (3-7 minutes)
    if (isLow) {
      return (
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-4 py-2.5" data-testid="trial-banner-warning">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5" />
              <p className="text-sm">
                <span className="font-semibold">Trial running low:</span> {formatTimeRemaining(minutesRemaining)} of call time left
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

    // Normal trial info banner (cyan/teal)
    return (
      <div className="bg-gradient-to-r from-cyan-600 to-teal-600 text-white px-4 py-2.5" data-testid="trial-banner-info">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center">
              <Clock className="w-3 h-3" />
            </div>
            <div className="flex items-center gap-2">
              <p className="text-sm">
                <span className="font-semibold">Free Trial:</span> {formatTimeRemaining(minutesRemaining)} of call time remaining
              </p>
              {/* Progress bar */}
              <div className="hidden sm:block w-24 h-1.5 bg-white/30 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-white rounded-full transition-all duration-300"
                  style={{ width: `${100 - usagePercent}%` }}
                />
              </div>
            </div>
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
