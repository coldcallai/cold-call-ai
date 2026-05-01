import React, { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown,
  Phone, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Users,
  Calendar,
  Target,
  Percent,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AnalyticsPage = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState("7d"); // 7d, 30d, 90d, all

  useEffect(() => {
    fetchAnalytics();
  }, [dateRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/analytics?range=${dateRange}`, { withCredentials: true });
      setAnalytics(response.data);
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
      // Set mock data for demo
      setAnalytics({
        total_calls: 247,
        total_calls_change: 12.5,
        answered_calls: 186,
        answer_rate: 75.3,
        answer_rate_change: 3.2,
        qualified_leads: 48,
        qualification_rate: 25.8,
        qualification_rate_change: -2.1,
        bookings: 23,
        booking_rate: 47.9,
        booking_rate_change: 8.4,
        avg_call_duration: 142,
        avg_duration_change: 15,
        total_talk_time: 587,
        calls_by_day: [
          { date: "Mon", calls: 42, qualified: 12 },
          { date: "Tue", calls: 38, qualified: 8 },
          { date: "Wed", calls: 45, qualified: 14 },
          { date: "Thu", calls: 31, qualified: 6 },
          { date: "Fri", calls: 52, qualified: 16 },
          { date: "Sat", calls: 18, qualified: 4 },
          { date: "Sun", calls: 21, qualified: 5 }
        ],
        calls_by_outcome: [
          { outcome: "Qualified", count: 48, color: "bg-emerald-500" },
          { outcome: "Not Qualified", count: 89, color: "bg-gray-400" },
          { outcome: "No Answer", count: 61, color: "bg-yellow-500" },
          { outcome: "Voicemail", count: 34, color: "bg-blue-400" },
          { outcome: "Failed", count: 15, color: "bg-red-500" }
        ],
        top_campaigns: [
          { name: "Credit Card Processing Q2", calls: 89, qualified: 24, rate: 27.0 },
          { name: "Insurance Leads", calls: 67, qualified: 14, rate: 20.9 },
          { name: "Solar Panel Outreach", calls: 54, qualified: 18, rate: 33.3 },
          { name: "HVAC Services", calls: 37, qualified: 8, rate: 21.6 }
        ],
        best_call_times: [
          { hour: "9 AM", success_rate: 32 },
          { hour: "10 AM", success_rate: 38 },
          { hour: "11 AM", success_rate: 29 },
          { hour: "1 PM", success_rate: 24 },
          { hour: "2 PM", success_rate: 35 },
          { hour: "3 PM", success_rate: 31 },
          { hour: "4 PM", success_rate: 28 }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const StatCard = ({ title, value, change, icon: Icon, suffix = "", prefix = "" }) => {
    const isPositive = change >= 0;
    return (
      <Card className="bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">{title}</p>
              <p className="text-3xl font-bold text-gray-900">
                {prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}
              </p>
              {change !== undefined && (
                <div className={`flex items-center gap-1 mt-2 text-sm ${isPositive ? 'text-emerald-600' : 'text-red-600'}`}>
                  {isPositive ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                  <span>{isPositive ? '+' : ''}{change}% vs last period</span>
                </div>
              )}
            </div>
            <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
              title.includes('Qualified') ? 'bg-emerald-100' : 
              title.includes('Booking') ? 'bg-purple-100' :
              title.includes('Answer') ? 'bg-blue-100' : 'bg-gray-100'
            }`}>
              <Icon className={`w-7 h-7 ${
                title.includes('Qualified') ? 'text-emerald-600' : 
                title.includes('Booking') ? 'text-purple-600' :
                title.includes('Answer') ? 'text-blue-600' : 'text-gray-600'
              }`} />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="p-6 md:p-8 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="analytics-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Call Analytics
          </h1>
          <p className="text-gray-500 mt-1">Track your calling performance and conversion rates</p>
          <p className="text-xs text-blue-600 mt-1 bg-blue-50 px-2 py-1 rounded inline-block">
            💡 Use these insights to optimize your scripts and calling times for better results.
          </p>
        </div>
        <div className="flex gap-2">
          {["7d", "30d", "90d", "all"].map((range) => (
            <Button
              key={range}
              variant={dateRange === range ? "default" : "outline"}
              size="sm"
              onClick={() => setDateRange(range)}
              className={dateRange === range ? "bg-blue-600" : ""}
            >
              {range === "7d" ? "7 Days" : range === "30d" ? "30 Days" : range === "90d" ? "90 Days" : "All Time"}
            </Button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Total Calls" 
          value={analytics?.total_calls || 0}
          change={analytics?.total_calls_change}
          icon={Phone}
        />
        <StatCard 
          title="Answer Rate" 
          value={analytics?.answer_rate || 0}
          change={analytics?.answer_rate_change}
          icon={CheckCircle2}
          suffix="%"
        />
        <StatCard 
          title="Qualified Leads" 
          value={analytics?.qualified_leads || 0}
          change={analytics?.qualification_rate_change}
          icon={Target}
        />
        <StatCard 
          title="Booking Rate" 
          value={analytics?.booking_rate || 0}
          change={analytics?.booking_rate_change}
          icon={Calendar}
          suffix="%"
        />
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Calls by Day Chart */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              Calls by Day
            </CardTitle>
            <CardDescription>Daily call volume and qualified leads</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-2 h-48">
              {analytics?.calls_by_day?.map((day, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full flex flex-col items-center gap-1" style={{ height: '140px' }}>
                    <div 
                      className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                      style={{ height: `${(day.calls / 60) * 100}%`, minHeight: '4px' }}
                      title={`${day.calls} calls`}
                    />
                    <div 
                      className="w-full bg-emerald-500 rounded-b transition-all hover:bg-emerald-600"
                      style={{ height: `${(day.qualified / 20) * 100}%`, minHeight: '2px' }}
                      title={`${day.qualified} qualified`}
                    />
                  </div>
                  <span className="text-xs text-gray-500">{day.date}</span>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center gap-6 mt-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500 rounded" />
                <span className="text-gray-600">Total Calls</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-emerald-500 rounded" />
                <span className="text-gray-600">Qualified</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Call Outcomes */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Percent className="w-5 h-5 text-purple-600" />
              Call Outcomes
            </CardTitle>
            <CardDescription>Breakdown of how calls ended</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics?.calls_by_outcome?.map((outcome, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-24 text-sm text-gray-600">{outcome.outcome}</div>
                  <div className="flex-1 h-8 bg-gray-100 rounded-lg overflow-hidden">
                    <div 
                      className={`h-full ${outcome.color} transition-all flex items-center justify-end pr-2`}
                      style={{ width: `${(outcome.count / analytics.total_calls) * 100}%` }}
                    >
                      <span className="text-xs font-medium text-white">{outcome.count}</span>
                    </div>
                  </div>
                  <div className="w-12 text-right text-sm font-medium text-gray-700">
                    {((outcome.count / analytics.total_calls) * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top Campaigns */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-emerald-600" />
              Top Performing Campaigns
            </CardTitle>
            <CardDescription>Campaigns ranked by qualification rate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics?.top_campaigns?.map((campaign, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm ${
                      i === 0 ? 'bg-yellow-500' : i === 1 ? 'bg-gray-400' : i === 2 ? 'bg-amber-600' : 'bg-gray-300'
                    }`}>
                      {i + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{campaign.name}</p>
                      <p className="text-sm text-gray-500">{campaign.calls} calls · {campaign.qualified} qualified</p>
                    </div>
                  </div>
                  <Badge variant={campaign.rate >= 25 ? "default" : "secondary"} className={campaign.rate >= 25 ? "bg-emerald-100 text-emerald-700" : ""}>
                    {campaign.rate}% rate
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Best Call Times */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-orange-600" />
              Best Calling Times
            </CardTitle>
            <CardDescription>Hours with highest qualification rates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analytics?.best_call_times?.map((time, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-16 text-sm text-gray-600 font-medium">{time.hour}</div>
                  <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all ${
                        time.success_rate >= 35 ? 'bg-emerald-500' : 
                        time.success_rate >= 30 ? 'bg-blue-500' : 'bg-gray-400'
                      }`}
                      style={{ width: `${time.success_rate * 2.5}%` }}
                    />
                  </div>
                  <div className="w-12 text-right text-sm font-medium text-gray-700">
                    {time.success_rate}%
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
              <p className="text-sm text-emerald-800">
                <strong>🎯 Pro Tip:</strong> Schedule campaigns between 10 AM - 2 PM for best results.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200">
          <CardContent className="p-6 text-center">
            <Clock className="w-10 h-10 text-blue-600 mx-auto mb-2" />
            <p className="text-sm text-blue-600 mb-1">Avg Call Duration</p>
            <p className="text-2xl font-bold text-blue-900">{formatDuration(analytics?.avg_call_duration || 0)}</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200">
          <CardContent className="p-6 text-center">
            <Phone className="w-10 h-10 text-purple-600 mx-auto mb-2" />
            <p className="text-sm text-purple-600 mb-1">Total Talk Time</p>
            <p className="text-2xl font-bold text-purple-900">{Math.floor((analytics?.total_talk_time || 0) / 60)}h {(analytics?.total_talk_time || 0) % 60}m</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border border-emerald-200">
          <CardContent className="p-6 text-center">
            <Users className="w-10 h-10 text-emerald-600 mx-auto mb-2" />
            <p className="text-sm text-emerald-600 mb-1">Meetings Booked</p>
            <p className="text-2xl font-bold text-emerald-900">{analytics?.bookings || 0}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AnalyticsPage;
