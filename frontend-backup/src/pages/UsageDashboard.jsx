import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  TrendingUp, TrendingDown, AlertTriangle, Zap, Phone, Search,
  ArrowUpRight, Calendar, BarChart3, RefreshCw
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Simple bar chart component
const MiniBarChart = ({ data, maxValue, color }) => {
  if (!data || data.length === 0) return null;
  
  const chartHeight = 80;
  const barWidth = Math.max(4, Math.floor(280 / data.length) - 2);
  
  return (
    <div className="flex items-end gap-1 h-20 w-full">
      {data.map((item, idx) => {
        const height = maxValue > 0 ? (item.value / maxValue) * chartHeight : 0;
        return (
          <div
            key={idx}
            className="group relative flex-1"
            style={{ minWidth: barWidth }}
          >
            <div
              className={`w-full rounded-t transition-all duration-200 ${color}`}
              style={{ height: `${Math.max(2, height)}px` }}
            />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
              {item.label}: {item.value}
            </div>
          </div>
        );
      })}
    </div>
  );
};

const UsageDashboard = () => {
  const { user, sessionToken } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics/usage`, {
        headers: { Authorization: `Bearer ${sessionToken}` }
      });
      setAnalytics(response.data);
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
      toast.error("Failed to load usage data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (sessionToken) {
      fetchAnalytics();
    }
  }, [sessionToken]);

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-40 bg-gray-200 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const leadCredits = analytics?.current_balance?.lead_credits || 0;
  const callCredits = analytics?.current_balance?.call_credits || 0;
  const leadsUsed = analytics?.period_totals?.leads_used || 0;
  const callsMade = analytics?.period_totals?.calls_made || 0;
  const avgLeads = analytics?.daily_averages?.leads || 0;
  const avgCalls = analytics?.daily_averages?.calls || 0;

  // Prepare chart data
  const usageTrend = analytics?.usage_trend || [];
  const last14Days = usageTrend.slice(-14);
  
  const leadChartData = last14Days.map(d => ({
    label: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: d.leads
  }));
  
  const callChartData = last14Days.map(d => ({
    label: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: d.calls
  }));

  const maxLeads = Math.max(...leadChartData.map(d => d.value), 1);
  const maxCalls = Math.max(...callChartData.map(d => d.value), 1);

  // Calculate usage percentages (assuming 250 as default monthly allocation)
  const monthlyLeadAllocation = user?.monthly_lead_allowance || 250;
  const monthlyCallAllocation = user?.monthly_call_allowance || 250;
  const leadUsagePercent = Math.min(100, Math.round((leadsUsed / monthlyLeadAllocation) * 100));
  const callUsagePercent = Math.min(100, Math.round((callsMade / monthlyCallAllocation) * 100));

  return (
    <div className="p-8 space-y-6" data-testid="usage-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Usage Dashboard
          </h1>
          <p className="text-gray-500 mt-1">Track your credit consumption and discover insights</p>
        </div>
        <Button 
          variant="outline" 
          onClick={fetchAnalytics}
          className="gap-2"
          data-testid="refresh-analytics-btn"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      {/* Suggestions/Alerts */}
      {analytics?.suggestions?.length > 0 && (
        <div className="space-y-3">
          {analytics.suggestions.map((suggestion, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-4 p-4 rounded-xl border ${
                suggestion.type === 'warning' 
                  ? 'bg-amber-50 border-amber-200' 
                  : 'bg-gradient-to-r from-cyan-50 to-teal-50 border-cyan-200'
              }`}
              data-testid={`suggestion-${suggestion.type}`}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                suggestion.type === 'warning' ? 'bg-amber-100' : 'bg-cyan-100'
              }`}>
                {suggestion.type === 'warning' ? (
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                ) : (
                  <TrendingUp className="w-5 h-5 text-cyan-600" />
                )}
              </div>
              <div className="flex-1">
                <h3 className={`font-semibold ${
                  suggestion.type === 'warning' ? 'text-amber-800' : 'text-cyan-800'
                }`}>
                  {suggestion.title}
                </h3>
                <p className={`text-sm mt-1 ${
                  suggestion.type === 'warning' ? 'text-amber-700' : 'text-cyan-700'
                }`}>
                  {suggestion.description}
                </p>
              </div>
              <Button
                size="sm"
                className={suggestion.type === 'warning' 
                  ? 'bg-amber-600 hover:bg-amber-700' 
                  : 'bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600'
                }
              >
                {suggestion.type === 'warning' ? 'Add Credits' : 'Upgrade'}
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Credit Balances */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-cyan-500 to-cyan-600 text-white border-0">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-cyan-100 text-sm">Lead Credits</p>
                <p className="text-4xl font-bold mt-1">{leadCredits}</p>
                <p className="text-cyan-200 text-xs mt-2">remaining</p>
              </div>
              <div className="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center">
                <Search className="w-7 h-7" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-violet-500 to-violet-600 text-white border-0">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-violet-100 text-sm">Call Credits</p>
                <p className="text-4xl font-bold mt-1">{callCredits}</p>
                <p className="text-violet-200 text-xs mt-2">remaining</p>
              </div>
              <div className="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center">
                <Phone className="w-7 h-7" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Leads Used (30d)</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{leadsUsed}</p>
                <div className="flex items-center gap-1 mt-2">
                  <TrendingUp className="w-3 h-3 text-emerald-500" />
                  <span className="text-xs text-emerald-600">{avgLeads}/day avg</span>
                </div>
              </div>
              <div className="w-12 h-12 bg-cyan-100 rounded-full flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-cyan-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Calls Made (30d)</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{callsMade}</p>
                <div className="flex items-center gap-1 mt-2">
                  <TrendingUp className="w-3 h-3 text-emerald-500" />
                  <span className="text-xs text-emerald-600">{avgCalls}/day avg</span>
                </div>
              </div>
              <div className="w-12 h-12 bg-violet-100 rounded-full flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-violet-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Usage Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border border-gray-200">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Search className="w-5 h-5 text-cyan-500" />
              Lead Discovery Trend
            </CardTitle>
            <CardDescription>Last 14 days of lead generation activity</CardDescription>
          </CardHeader>
          <CardContent>
            {leadChartData.length > 0 ? (
              <MiniBarChart data={leadChartData} maxValue={maxLeads} color="bg-cyan-500" />
            ) : (
              <div className="h-20 flex items-center justify-center text-gray-400 text-sm">
                No data yet. Start discovering leads!
              </div>
            )}
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
              <div>
                <p className="text-xs text-gray-500">Monthly Usage</p>
                <p className="text-sm font-medium text-gray-900">{leadsUsed} / {monthlyLeadAllocation}</p>
              </div>
              <Progress value={leadUsagePercent} className="w-32 h-2" />
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Phone className="w-5 h-5 text-violet-500" />
              AI Calls Trend
            </CardTitle>
            <CardDescription>Last 14 days of calling activity</CardDescription>
          </CardHeader>
          <CardContent>
            {callChartData.length > 0 ? (
              <MiniBarChart data={callChartData} maxValue={maxCalls} color="bg-violet-500" />
            ) : (
              <div className="h-20 flex items-center justify-center text-gray-400 text-sm">
                No calls yet. Start your first campaign!
              </div>
            )}
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
              <div>
                <p className="text-xs text-gray-500">Monthly Usage</p>
                <p className="text-sm font-medium text-gray-900">{callsMade} / {monthlyCallAllocation}</p>
              </div>
              <Progress value={callUsagePercent} className="w-32 h-2" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="border border-gray-200">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            Recent Activity
          </CardTitle>
          <CardDescription>Your latest credit usage events</CardDescription>
        </CardHeader>
        <CardContent>
          {analytics?.recent_activity?.length > 0 ? (
            <div className="space-y-3">
              {analytics.recent_activity.map((event, idx) => (
                <div 
                  key={idx}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      event.event_type.includes('lead') ? 'bg-cyan-100' : 'bg-violet-100'
                    }`}>
                      {event.event_type.includes('lead') ? (
                        <Search className={`w-4 h-4 ${event.event_type.includes('purchased') ? 'text-emerald-600' : 'text-cyan-600'}`} />
                      ) : (
                        <Phone className={`w-4 h-4 ${event.event_type.includes('purchased') ? 'text-emerald-600' : 'text-violet-600'}`} />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {event.event_type === 'lead_discovery' && `Discovered ${event.amount} leads`}
                        {event.event_type === 'call_made' && `Made ${event.amount} AI call${event.amount > 1 ? 's' : ''}`}
                        {event.event_type === 'lead_purchased' && `Purchased ${event.amount} lead credits`}
                        {event.event_type === 'call_purchased' && `Purchased ${event.amount} call credits`}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(event.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <Badge variant={event.event_type.includes('purchased') ? 'default' : 'secondary'}>
                    {event.event_type.includes('purchased') ? `+${event.amount}` : `-${event.amount}`}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No recent activity</p>
              <p className="text-sm mt-1">Start using the platform to see your activity here</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Button variant="outline" className="h-auto py-4 justify-start gap-3" asChild>
          <a href="/app/leads">
            <div className="w-10 h-10 bg-cyan-100 rounded-lg flex items-center justify-center">
              <Search className="w-5 h-5 text-cyan-600" />
            </div>
            <div className="text-left">
              <p className="font-medium">Discover Leads</p>
              <p className="text-xs text-gray-500">Find high-intent businesses</p>
            </div>
            <ArrowUpRight className="w-4 h-4 ml-auto text-gray-400" />
          </a>
        </Button>
        
        <Button variant="outline" className="h-auto py-4 justify-start gap-3" asChild>
          <a href="/app/campaigns">
            <div className="w-10 h-10 bg-violet-100 rounded-lg flex items-center justify-center">
              <Phone className="w-5 h-5 text-violet-600" />
            </div>
            <div className="text-left">
              <p className="font-medium">Start Calling</p>
              <p className="text-xs text-gray-500">Launch an AI call campaign</p>
            </div>
            <ArrowUpRight className="w-4 h-4 ml-auto text-gray-400" />
          </a>
        </Button>
        
        <Button variant="outline" className="h-auto py-4 justify-start gap-3" asChild>
          <a href="/app/packs">
            <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-emerald-600" />
            </div>
            <div className="text-left">
              <p className="font-medium">Buy Credits</p>
              <p className="text-xs text-gray-500">Top up your balance</p>
            </div>
            <ArrowUpRight className="w-4 h-4 ml-auto text-gray-400" />
          </a>
        </Button>
      </div>
    </div>
  );
};

export default UsageDashboard;
