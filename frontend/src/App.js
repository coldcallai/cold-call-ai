import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { 
  Phone, Users, Target, Calendar, Settings, LayoutDashboard, 
  History, Search, Plus, Play, Pause, Trash2, ChevronRight,
  PhoneCall, PhoneOff, CheckCircle, XCircle, Clock, TrendingUp,
  Building2, User, Mail, ExternalLink, AlertCircle, Filter,
  ArrowRight, Zap, UserCheck, CalendarCheck
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import LandingPage from "@/LandingPage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Navigation Sidebar
const Sidebar = () => {
  const location = useLocation();
  
  const navItems = [
    { path: "/app", icon: Filter, label: "Funnel" },
    { path: "/app/leads", icon: Search, label: "Lead Discovery" },
    { path: "/app/campaigns", icon: Target, label: "Campaigns" },
    { path: "/app/agents", icon: Users, label: "Agents" },
    { path: "/app/calls", icon: History, label: "Call History" },
    { path: "/app/settings", icon: Settings, label: "Settings" },
  ];

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
            <Phone className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              ColdCall.ai
            </h1>
            <p className="text-xs text-gray-500">AI Sales Automation</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || 
              (item.path === "/app" && location.pathname === "/app/");
            const Icon = item.icon;
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-blue-50 text-blue-600 border border-blue-100"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      
      <div className="p-4 border-t border-gray-100">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-medium text-amber-800">Demo Mode</p>
              <p className="text-xs text-amber-600 mt-0.5">Calls are simulated. Add Twilio credentials for real calls.</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

// Status Badge Component
const StatusBadge = ({ status }) => {
  const statusConfig = {
    new: { color: "bg-gray-100 text-gray-700 border-gray-200", label: "New" },
    contacted: { color: "bg-blue-50 text-blue-700 border-blue-200", label: "Contacted" },
    qualified: { color: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "Qualified" },
    not_qualified: { color: "bg-red-50 text-red-700 border-red-200", label: "Not Qualified" },
    booked: { color: "bg-purple-50 text-purple-700 border-purple-200", label: "Booked" },
    draft: { color: "bg-gray-100 text-gray-700 border-gray-200", label: "Draft" },
    active: { color: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "Active" },
    paused: { color: "bg-amber-50 text-amber-700 border-amber-200", label: "Paused" },
    completed: { color: "bg-blue-50 text-blue-700 border-blue-200", label: "Completed" },
    pending: { color: "bg-gray-100 text-gray-700 border-gray-200", label: "Pending" },
    in_progress: { color: "bg-blue-50 text-blue-700 border-blue-200", label: "In Progress" },
    failed: { color: "bg-red-50 text-red-700 border-red-200", label: "Failed" },
    no_answer: { color: "bg-amber-50 text-amber-700 border-amber-200", label: "No Answer" },
  };
  
  const config = statusConfig[status] || statusConfig.new;
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.color}`}>
      {config.label}
    </span>
  );
};

// Funnel Page - Visual Pipeline View
const FunnelPage = () => {
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedLead, setSelectedLead] = useState(null);
  const [selectedCampaign, setSelectedCampaign] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const [leadsRes, statsRes, agentsRes, campaignsRes] = await Promise.all([
        axios.get(`${API}/leads`),
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/agents`),
        axios.get(`${API}/campaigns`)
      ]);
      setLeads(leadsRes.data);
      setStats(statsRes.data);
      setAgents(agentsRes.data.filter(a => a.is_active));
      setCampaigns(campaignsRes.data.filter(c => c.status === 'active'));
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast.error("Failed to load funnel data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const simulateCall = async (leadId) => {
    if (!selectedCampaign) {
      toast.error("Please select a campaign first");
      return;
    }
    try {
      await axios.post(`${API}/calls/simulate?lead_id=${leadId}&campaign_id=${selectedCampaign}`);
      toast.success("Call started!");
      setTimeout(fetchData, 3000);
    } catch (error) {
      toast.error("Failed to start call");
    }
  };

  // Group leads by status
  const newLeads = leads.filter(l => l.status === 'new');
  const contactedLeads = leads.filter(l => l.status === 'contacted');
  const qualifiedLeads = leads.filter(l => l.status === 'qualified');
  const bookedLeads = leads.filter(l => l.status === 'booked');
  const notQualifiedLeads = leads.filter(l => l.status === 'not_qualified');

  const funnelStages = [
    { 
      id: 'new', 
      title: 'New Leads', 
      leads: newLeads, 
      icon: Zap, 
      color: 'bg-blue-500',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-700'
    },
    { 
      id: 'contacted', 
      title: 'Contacted', 
      leads: contactedLeads, 
      icon: PhoneCall, 
      color: 'bg-amber-500',
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-200',
      textColor: 'text-amber-700'
    },
    { 
      id: 'qualified', 
      title: 'Qualified', 
      leads: qualifiedLeads, 
      icon: UserCheck, 
      color: 'bg-emerald-500',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
      textColor: 'text-emerald-700'
    },
    { 
      id: 'booked', 
      title: 'Booked', 
      leads: bookedLeads, 
      icon: CalendarCheck, 
      color: 'bg-purple-500',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      textColor: 'text-purple-700'
    },
  ];

  if (loading) {
    return (
      <div className="p-6 md:p-8 space-y-6" data-testid="funnel-loading">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-96" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="funnel-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Sales Funnel
          </h1>
          <p className="text-gray-500 mt-1">Track leads through your qualification pipeline</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={selectedCampaign} onValueChange={setSelectedCampaign}>
            <SelectTrigger data-testid="funnel-campaign-select" className="w-[200px]">
              <SelectValue placeholder="Select campaign" />
            </SelectTrigger>
            <SelectContent>
              {campaigns.map(c => (
                <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button 
            data-testid="funnel-discover-btn"
            className="bg-blue-600 hover:bg-blue-700 text-white"
            onClick={() => window.location.href = '/leads'}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Leads
          </Button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Total Leads</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{leads.length}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Qualification Rate</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{stats?.qualification_rate || 0}%</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Booking Rate</p>
          <p className="text-2xl font-bold text-purple-600 mt-1">{stats?.booking_rate || 0}%</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Total Calls</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{stats?.total_calls || 0}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Not Qualified</p>
          <p className="text-2xl font-bold text-red-500 mt-1">{notQualifiedLeads.length}</p>
        </div>
      </div>

      {/* Funnel Flow Visual */}
      <div className="flex items-center justify-center gap-2 py-4">
        {funnelStages.map((stage, idx) => (
          <div key={stage.id} className="flex items-center">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${stage.bgColor} ${stage.borderColor} border`}>
              <stage.icon className={`w-4 h-4 ${stage.textColor}`} />
              <span className={`font-semibold ${stage.textColor}`}>{stage.leads.length}</span>
            </div>
            {idx < funnelStages.length - 1 && (
              <ArrowRight className="w-5 h-5 text-gray-300 mx-2" />
            )}
          </div>
        ))}
      </div>

      {/* Kanban-style Columns */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {funnelStages.map((stage) => {
          const Icon = stage.icon;
          return (
            <div key={stage.id} className="flex flex-col" data-testid={`funnel-stage-${stage.id}`}>
              {/* Column Header */}
              <div className={`${stage.bgColor} ${stage.borderColor} border rounded-t-xl p-4`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-lg ${stage.color} flex items-center justify-center`}>
                      <Icon className="w-4 h-4 text-white" />
                    </div>
                    <h3 className={`font-semibold ${stage.textColor}`} style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                      {stage.title}
                    </h3>
                  </div>
                  <span className={`text-xl font-bold ${stage.textColor}`}>{stage.leads.length}</span>
                </div>
              </div>

              {/* Column Content */}
              <div className="flex-1 bg-white border border-t-0 border-gray-200 rounded-b-xl">
                <ScrollArea className="h-[400px]">
                  {stage.leads.length === 0 ? (
                    <div className="p-6 text-center">
                      <div className={`w-12 h-12 rounded-full ${stage.bgColor} flex items-center justify-center mx-auto`}>
                        <Icon className={`w-6 h-6 ${stage.textColor} opacity-50`} />
                      </div>
                      <p className="text-sm text-gray-400 mt-3">No leads</p>
                    </div>
                  ) : (
                    <div className="p-3 space-y-2">
                      {stage.leads.map((lead) => (
                        <div 
                          key={lead.id}
                          data-testid={`funnel-lead-${lead.id}`}
                          className="bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg p-3 transition-colors cursor-pointer"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-gray-900 text-sm truncate">
                                {lead.business_name}
                              </p>
                              <p className="text-xs text-gray-500 mt-0.5">{lead.phone}</p>
                              {lead.qualification_score !== null && (
                                <div className="flex items-center gap-2 mt-2">
                                  <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                    <div 
                                      className={`h-full ${lead.qualification_score >= 60 ? 'bg-emerald-500' : 'bg-gray-400'}`}
                                      style={{ width: `${lead.qualification_score}%` }}
                                    />
                                  </div>
                                  <span className="text-xs font-medium text-gray-600">{lead.qualification_score}</span>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Action Buttons */}
                          <div className="mt-3 flex gap-2">
                            {stage.id === 'new' && (
                              <Button 
                                size="sm" 
                                className="flex-1 h-7 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                                onClick={() => simulateCall(lead.id)}
                                disabled={!selectedCampaign}
                              >
                                <Phone className="w-3 h-3 mr-1" />
                                Call
                              </Button>
                            )}
                            {stage.id === 'qualified' && (
                              <Button 
                                size="sm" 
                                className="flex-1 h-7 text-xs bg-purple-600 hover:bg-purple-700 text-white"
                                onClick={() => setSelectedLead(lead)}
                              >
                                <Calendar className="w-3 h-3 mr-1" />
                                Book
                              </Button>
                            )}
                            {stage.id === 'booked' && (
                              <div className="flex items-center gap-1 text-xs text-purple-600">
                                <CheckCircle className="w-3 h-3" />
                                <span>Meeting scheduled</span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </div>
            </div>
          );
        })}
      </div>

      {/* Booking Dialog */}
      <BookingDialog 
        lead={selectedLead} 
        onClose={() => setSelectedLead(null)}
        onSuccess={() => {
          setSelectedLead(null);
          fetchData();
        }}
      />
    </div>
  );
};

// Lead Discovery Page
const LeadDiscovery = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [searchQuery, setSearchQuery] = useState("Toast alternative");
  const [industry, setIndustry] = useState("");
  const [location, setLocation] = useState("");
  const [campaigns, setCampaigns] = useState([]);
  const [selectedLead, setSelectedLead] = useState(null);
  const [selectedCampaign, setSelectedCampaign] = useState("");
  const [viewMode, setViewMode] = useState("table");

  const intentKeywords = [
    "Toast alternative",
    "Square alternative",
    "Stripe alternative",
    "Clover alternative",
    "best POS system",
    "credit card processing",
    "payment processing",
    "merchant services",
    "reduce processing fees"
  ];

  const fetchLeads = async () => {
    try {
      const response = await axios.get(`${API}/leads`);
      setLeads(response.data);
    } catch (error) {
      toast.error("Failed to load leads");
    } finally {
      setLoading(false);
    }
  };

  const fetchCampaigns = async () => {
    try {
      const response = await axios.get(`${API}/campaigns`);
      setCampaigns(response.data.filter(c => c.status === 'active'));
    } catch (error) {
      console.error("Failed to fetch campaigns:", error);
    }
  };

  useEffect(() => {
    fetchLeads();
    fetchCampaigns();
  }, []);

  const discoverLeads = async () => {
    setDiscovering(true);
    try {
      const response = await axios.post(`${API}/leads/gpt-intent-search`, {
        search_query: searchQuery,
        industry: industry || null,
        location: location || null,
        max_results: 10
      });
      toast.success(`Discovered ${response.data.discovered} high-intent leads!`);
      fetchLeads();
    } catch (error) {
      toast.error("Failed to discover leads");
    } finally {
      setDiscovering(false);
    }
  };

  const simulateCall = async (leadId) => {
    if (!selectedCampaign) {
      toast.error("Please select a campaign first");
      return;
    }
    
    try {
      await axios.post(`${API}/calls/simulate?lead_id=${leadId}&campaign_id=${selectedCampaign}`);
      toast.success("Call started! Check call history for results.");
      setTimeout(fetchLeads, 3000);
    } catch (error) {
      toast.error("Failed to start call");
    }
  };

  const deleteLead = async (leadId) => {
    try {
      await axios.delete(`${API}/leads/${leadId}`);
      toast.success("Lead deleted");
      fetchLeads();
    } catch (error) {
      toast.error("Failed to delete lead");
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="lead-discovery-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Lead Discovery
          </h1>
          <p className="text-gray-500 mt-1">Find businesses actively searching for payment solutions</p>
        </div>
      </div>

      {/* Intent Keywords Quick Select */}
      <Card className="bg-gradient-to-r from-cyan-50 to-teal-50 border border-cyan-200 shadow-sm">
        <CardContent className="p-4">
          <p className="text-sm font-medium text-cyan-800 mb-3">High-Intent Keywords (People in Buying Mode)</p>
          <div className="flex flex-wrap gap-2">
            {intentKeywords.map((keyword) => (
              <button
                key={keyword}
                onClick={() => setSearchQuery(keyword)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                  searchQuery === keyword
                    ? 'bg-cyan-600 text-white'
                    : 'bg-white text-cyan-700 border border-cyan-300 hover:bg-cyan-100'
                }`}
              >
                {keyword}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Search Form */}
      <Card className="bg-white border border-gray-200 shadow-sm">
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="search">Search Query</Label>
              <Input
                id="search"
                data-testid="lead-search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="e.g., Toast alternative"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="industry">Industry (Optional)</Label>
              <Input
                id="industry"
                data-testid="lead-industry-input"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="e.g., Restaurant, Retail"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="location">Location (Optional)</Label>
              <Input
                id="location"
                data-testid="lead-location-input"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g., Texas, New York"
                className="mt-1"
              />
            </div>
            <div>
              <Label>Campaign for Calling</Label>
              <Select value={selectedCampaign} onValueChange={setSelectedCampaign}>
                <SelectTrigger data-testid="campaign-select" className="mt-1">
                  <SelectValue placeholder="Select campaign" />
                </SelectTrigger>
                <SelectContent>
                  {campaigns.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <Button 
              data-testid="discover-btn"
              onClick={discoverLeads} 
              disabled={discovering}
              className="bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white"
            >
              {discovering ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  AI Searching...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2" />
                  Discover High-Intent Leads
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Leads Table */}
      <Card className="bg-white border border-gray-200 shadow-sm">
        <CardHeader className="border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-center justify-between">
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Discovered Leads ({leads.length})
            </CardTitle>
            <div className="text-sm text-gray-500">
              {leads.filter(l => l.source === 'gpt_intent_search').length} from GPT Intent Search
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 space-y-4">
              {[1,2,3].map(i => <Skeleton key={i} className="h-16" />)}
            </div>
          ) : leads.length === 0 ? (
            <div className="p-12 text-center">
              <Building2 className="w-16 h-16 text-gray-300 mx-auto" />
              <p className="text-gray-500 mt-4">No leads found. Click "Discover High-Intent Leads" to find prospects in buying mode.</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {leads.map((lead) => (
                <div key={lead.id} className="p-4 hover:bg-gray-50 transition-colors" data-testid={`lead-row-${lead.id}`}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <h3 className="font-semibold text-gray-900">{lead.business_name}</h3>
                        <StatusBadge status={lead.status} />
                        {lead.source === 'gpt_intent_search' && (
                          <Badge className="bg-cyan-100 text-cyan-700 border-0">AI Found</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                        <span>{lead.phone}</span>
                        {lead.email && <span>{lead.email}</span>}
                      </div>
                      {/* Intent Signals */}
                      {lead.intent_signals && lead.intent_signals.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {lead.intent_signals.slice(0, 3).map((signal, idx) => (
                            <span 
                              key={idx} 
                              className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-amber-50 text-amber-700 border border-amber-200"
                            >
                              {signal.length > 40 ? signal.substring(0, 40) + '...' : signal}
                            </span>
                          ))}
                          {lead.intent_signals.length > 3 && (
                            <span className="text-xs text-gray-400">+{lead.intent_signals.length - 3} more</span>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {lead.qualification_score !== null && (
                        <div className="text-center px-3">
                          <p className="text-xs text-gray-500">Score</p>
                          <p className={`text-lg font-bold ${lead.qualification_score >= 60 ? 'text-emerald-600' : 'text-gray-600'}`}>
                            {lead.qualification_score}
                          </p>
                        </div>
                      )}
                      {lead.status === 'new' && (
                        <Button 
                          size="sm" 
                          data-testid={`call-lead-${lead.id}`}
                          onClick={() => simulateCall(lead.id)}
                          disabled={!selectedCampaign}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white"
                        >
                          <Phone className="w-3 h-3 mr-1" />
                          Call
                        </Button>
                      )}
                      {lead.status === 'qualified' && (
                        <Button 
                          size="sm" 
                          data-testid={`book-lead-${lead.id}`}
                          onClick={() => setSelectedLead(lead)}
                          className="bg-purple-600 hover:bg-purple-700 text-white"
                        >
                          <Calendar className="w-3 h-3 mr-1" />
                          Book
                        </Button>
                      )}
                      <Button 
                        size="sm" 
                        variant="ghost"
                        data-testid={`delete-lead-${lead.id}`}
                        onClick={() => deleteLead(lead.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Booking Dialog */}
      <BookingDialog 
        lead={selectedLead} 
        onClose={() => setSelectedLead(null)}
        onSuccess={() => {
          setSelectedLead(null);
          fetchLeads();
        }}
      />
    </div>
  );
};

// Booking Dialog Component
const BookingDialog = ({ lead, onClose, onSuccess }) => {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    if (lead) {
      fetchAgents();
    }
  }, [lead]);

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API}/agents`);
      setAgents(response.data.filter(a => a.is_active));
    } catch (error) {
      console.error("Failed to fetch agents:", error);
    }
  };

  const bookMeeting = async () => {
    if (!selectedAgent) {
      toast.error("Please select an agent");
      return;
    }

    setBooking(true);
    try {
      const response = await axios.post(`${API}/bookings`, {
        lead_id: lead.id,
        agent_id: selectedAgent
      });
      toast.success("Meeting booked! Opening Calendly...");
      window.open(response.data.calendly_link, '_blank');
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to book meeting");
    } finally {
      setBooking(false);
    }
  };

  if (!lead) return null;

  return (
    <Dialog open={!!lead} onOpenChange={() => onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Book Meeting for {lead.business_name}
          </DialogTitle>
          <DialogDescription>
            Select an agent to assign this qualified lead
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div>
            <Label>Select Agent</Label>
            <Select value={selectedAgent} onValueChange={setSelectedAgent}>
              <SelectTrigger data-testid="agent-select-booking" className="mt-1">
                <SelectValue placeholder="Choose an agent" />
              </SelectTrigger>
              <SelectContent>
                {agents.map(agent => (
                  <SelectItem key={agent.id} value={agent.id}>
                    {agent.name} ({agent.assigned_leads} leads)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {selectedAgent && agents.find(a => a.id === selectedAgent) && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                Will redirect to agent's Calendly:
              </p>
              <a 
                href={agents.find(a => a.id === selectedAgent).calendly_link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:underline flex items-center gap-1 mt-1"
              >
                {agents.find(a => a.id === selectedAgent).calendly_link}
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button 
            data-testid="confirm-booking-btn"
            onClick={bookMeeting}
            disabled={booking || !selectedAgent}
            className="bg-purple-600 hover:bg-purple-700 text-white"
          >
            {booking ? "Booking..." : "Book Meeting"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Campaigns Page
const Campaigns = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newCampaign, setNewCampaign] = useState({
    name: "",
    description: "",
    ai_script: "Hello, this is an AI assistant calling about credit card processing solutions for your business. Am I speaking with the owner or manager?",
    calls_per_day: 100
  });

  const fetchCampaigns = async () => {
    try {
      const response = await axios.get(`${API}/campaigns`);
      setCampaigns(response.data);
    } catch (error) {
      toast.error("Failed to load campaigns");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const createCampaign = async () => {
    if (!newCampaign.name || !newCampaign.ai_script) {
      toast.error("Please fill in all required fields");
      return;
    }

    try {
      await axios.post(`${API}/campaigns`, newCampaign);
      toast.success("Campaign created!");
      setShowCreate(false);
      setNewCampaign({ name: "", description: "", ai_script: "", calls_per_day: 100 });
      fetchCampaigns();
    } catch (error) {
      toast.error("Failed to create campaign");
    }
  };

  const toggleCampaign = async (campaign) => {
    const endpoint = campaign.status === 'active' ? 'pause' : 'start';
    try {
      await axios.post(`${API}/campaigns/${campaign.id}/${endpoint}`);
      toast.success(`Campaign ${endpoint === 'start' ? 'started' : 'paused'}`);
      fetchCampaigns();
    } catch (error) {
      toast.error("Failed to update campaign");
    }
  };

  const deleteCampaign = async (id) => {
    try {
      await axios.delete(`${API}/campaigns/${id}`);
      toast.success("Campaign deleted");
      fetchCampaigns();
    } catch (error) {
      toast.error("Failed to delete campaign");
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="campaigns-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Campaigns
          </h1>
          <p className="text-gray-500 mt-1">Manage your AI calling campaigns</p>
        </div>
        <Button 
          data-testid="create-campaign-btn"
          onClick={() => setShowCreate(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Campaign
        </Button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1,2,3].map(i => <Skeleton key={i} className="h-48" />)}
        </div>
      ) : campaigns.length === 0 ? (
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardContent className="p-12 text-center">
            <Target className="w-16 h-16 text-gray-300 mx-auto" />
            <p className="text-gray-500 mt-4">No campaigns yet. Create your first campaign to start calling.</p>
            <Button 
              onClick={() => setShowCreate(true)}
              className="mt-4 bg-blue-600 hover:bg-blue-700 text-white"
            >
              Create Campaign
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {campaigns.map(campaign => (
            <Card key={campaign.id} className="bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow" data-testid={`campaign-card-${campaign.id}`}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                      {campaign.name}
                    </CardTitle>
                    <StatusBadge status={campaign.status} />
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    data-testid={`delete-campaign-${campaign.id}`}
                    onClick={() => deleteCampaign(campaign.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                  {campaign.description || "No description"}
                </p>
                
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="text-center p-2 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">Total Calls</p>
                    <p className="text-lg font-semibold text-gray-900">{campaign.total_calls}</p>
                  </div>
                  <div className="text-center p-2 bg-emerald-50 rounded-lg">
                    <p className="text-xs text-gray-500">Qualified</p>
                    <p className="text-lg font-semibold text-emerald-600">{campaign.qualified_leads}</p>
                  </div>
                </div>

                <Button
                  className="w-full"
                  data-testid={`toggle-campaign-${campaign.id}`}
                  variant={campaign.status === 'active' ? 'outline' : 'default'}
                  onClick={() => toggleCampaign(campaign)}
                >
                  {campaign.status === 'active' ? (
                    <>
                      <Pause className="w-4 h-4 mr-2" />
                      Pause Campaign
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Start Campaign
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Campaign Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Create New Campaign
            </DialogTitle>
            <DialogDescription>
              Set up a new AI calling campaign with a custom script
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="campaign-name">Campaign Name *</Label>
              <Input
                id="campaign-name"
                data-testid="campaign-name-input"
                value={newCampaign.name}
                onChange={(e) => setNewCampaign({...newCampaign, name: e.target.value})}
                placeholder="e.g., Q1 Credit Card Processing Outreach"
                className="mt-1"
              />
            </div>
            
            <div>
              <Label htmlFor="campaign-desc">Description</Label>
              <Input
                id="campaign-desc"
                data-testid="campaign-desc-input"
                value={newCampaign.description}
                onChange={(e) => setNewCampaign({...newCampaign, description: e.target.value})}
                placeholder="Brief description of the campaign"
                className="mt-1"
              />
            </div>
            
            <div>
              <Label htmlFor="ai-script">AI Script *</Label>
              <Textarea
                id="ai-script"
                data-testid="campaign-script-input"
                value={newCampaign.ai_script}
                onChange={(e) => setNewCampaign({...newCampaign, ai_script: e.target.value})}
                placeholder="Enter the script the AI will use during calls..."
                className="mt-1 min-h-[150px]"
              />
            </div>
            
            <div>
              <Label htmlFor="calls-per-day">Calls Per Day</Label>
              <Input
                id="calls-per-day"
                data-testid="campaign-calls-input"
                type="number"
                value={newCampaign.calls_per_day}
                onChange={(e) => setNewCampaign({...newCampaign, calls_per_day: parseInt(e.target.value) || 0})}
                className="mt-1"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button 
              data-testid="save-campaign-btn"
              onClick={createCampaign}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Create Campaign
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Agents Page
const Agents = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newAgent, setNewAgent] = useState({
    name: "",
    email: "",
    phone: "",
    calendly_link: "",
    max_daily_calls: 50
  });

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API}/agents`);
      setAgents(response.data);
    } catch (error) {
      toast.error("Failed to load agents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const createAgent = async () => {
    if (!newAgent.name || !newAgent.email || !newAgent.calendly_link) {
      toast.error("Please fill in all required fields");
      return;
    }

    try {
      await axios.post(`${API}/agents`, newAgent);
      toast.success("Agent created!");
      setShowCreate(false);
      setNewAgent({ name: "", email: "", phone: "", calendly_link: "", max_daily_calls: 50 });
      fetchAgents();
    } catch (error) {
      toast.error("Failed to create agent");
    }
  };

  const toggleAgent = async (agent) => {
    try {
      await axios.put(`${API}/agents/${agent.id}`, { is_active: !agent.is_active });
      toast.success(`Agent ${agent.is_active ? 'deactivated' : 'activated'}`);
      fetchAgents();
    } catch (error) {
      toast.error("Failed to update agent");
    }
  };

  const deleteAgent = async (id) => {
    try {
      await axios.delete(`${API}/agents/${id}`);
      toast.success("Agent deleted");
      fetchAgents();
    } catch (error) {
      toast.error("Failed to delete agent");
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="agents-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Agents
          </h1>
          <p className="text-gray-500 mt-1">Manage sales agents and their Calendly links</p>
        </div>
        <Button 
          data-testid="create-agent-btn"
          onClick={() => setShowCreate(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Agent
        </Button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1,2,3].map(i => <Skeleton key={i} className="h-48" />)}
        </div>
      ) : agents.length === 0 ? (
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardContent className="p-12 text-center">
            <Users className="w-16 h-16 text-gray-300 mx-auto" />
            <p className="text-gray-500 mt-4">No agents yet. Add agents to receive qualified leads.</p>
            <Button 
              onClick={() => setShowCreate(true)}
              className="mt-4 bg-blue-600 hover:bg-blue-700 text-white"
            >
              Add Agent
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map(agent => (
            <Card key={agent.id} className={`bg-white border shadow-sm hover:shadow-md transition-shadow ${agent.is_active ? 'border-gray-200' : 'border-gray-300 opacity-60'}`} data-testid={`agent-card-${agent.id}`}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-semibold ${agent.is_active ? 'bg-blue-600' : 'bg-gray-400'}`}>
                      {agent.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                      <Badge variant={agent.is_active ? "default" : "secondary"}>
                        {agent.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    data-testid={`delete-agent-${agent.id}`}
                    onClick={() => deleteAgent(agent.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
                
                <div className="space-y-2 text-sm mb-4">
                  <div className="flex items-center gap-2 text-gray-600">
                    <Mail className="w-4 h-4" />
                    {agent.email}
                  </div>
                  {agent.phone && (
                    <div className="flex items-center gap-2 text-gray-600">
                      <Phone className="w-4 h-4" />
                      {agent.phone}
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-blue-600">
                    <Calendar className="w-4 h-4" />
                    <a href={agent.calendly_link} target="_blank" rel="noopener noreferrer" className="hover:underline truncate">
                      Calendly Link
                    </a>
                  </div>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-4">
                  <span className="text-sm text-gray-600">Assigned Leads</span>
                  <span className="text-lg font-semibold text-gray-900">{agent.assigned_leads}</span>
                </div>

                <Button
                  className="w-full"
                  variant="outline"
                  data-testid={`toggle-agent-${agent.id}`}
                  onClick={() => toggleAgent(agent)}
                >
                  {agent.is_active ? "Deactivate" : "Activate"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Agent Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Add New Agent
            </DialogTitle>
            <DialogDescription>
              Add a sales agent with their Calendly booking link
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="agent-name">Name *</Label>
              <Input
                id="agent-name"
                data-testid="agent-name-input"
                value={newAgent.name}
                onChange={(e) => setNewAgent({...newAgent, name: e.target.value})}
                placeholder="John Doe"
                className="mt-1"
              />
            </div>
            
            <div>
              <Label htmlFor="agent-email">Email *</Label>
              <Input
                id="agent-email"
                data-testid="agent-email-input"
                type="email"
                value={newAgent.email}
                onChange={(e) => setNewAgent({...newAgent, email: e.target.value})}
                placeholder="john@company.com"
                className="mt-1"
              />
            </div>
            
            <div>
              <Label htmlFor="agent-phone">Phone</Label>
              <Input
                id="agent-phone"
                data-testid="agent-phone-input"
                value={newAgent.phone}
                onChange={(e) => setNewAgent({...newAgent, phone: e.target.value})}
                placeholder="+1-555-0123"
                className="mt-1"
              />
            </div>
            
            <div>
              <Label htmlFor="calendly-link">Calendly Link *</Label>
              <Input
                id="calendly-link"
                data-testid="agent-calendly-input"
                value={newAgent.calendly_link}
                onChange={(e) => setNewAgent({...newAgent, calendly_link: e.target.value})}
                placeholder="https://calendly.com/john-doe/30min"
                className="mt-1"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button 
              data-testid="save-agent-btn"
              onClick={createAgent}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Add Agent
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Call History Page
const CallHistory = () => {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCall, setSelectedCall] = useState(null);

  const fetchCalls = async () => {
    try {
      const response = await axios.get(`${API}/calls`);
      setCalls(response.data);
    } catch (error) {
      toast.error("Failed to load calls");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, []);

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="call-history-page">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
          Call History
        </h1>
        <p className="text-gray-500 mt-1">View transcripts and qualification results</p>
      </div>

      <Card className="bg-white border border-gray-200 shadow-sm">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 space-y-4">
              {[1,2,3].map(i => <Skeleton key={i} className="h-16" />)}
            </div>
          ) : calls.length === 0 ? (
            <div className="p-12 text-center">
              <History className="w-16 h-16 text-gray-300 mx-auto" />
              <p className="text-gray-500 mt-4">No calls yet. Start a campaign to make calls.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Call ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Qualification</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {calls.map((call) => (
                  <TableRow key={call.id} data-testid={`call-row-${call.id}`}>
                    <TableCell className="font-mono text-sm">{call.id.slice(0, 8)}...</TableCell>
                    <TableCell>
                      <StatusBadge status={call.status} />
                    </TableCell>
                    <TableCell>{call.duration_seconds}s</TableCell>
                    <TableCell>
                      {call.qualification_result ? (
                        <div className="flex items-center gap-2">
                          {call.qualification_result.is_qualified ? (
                            <CheckCircle className="w-4 h-4 text-emerald-600" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-500" />
                          )}
                          <span className="text-sm">
                            Score: {call.qualification_result.score}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {new Date(call.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        data-testid={`view-call-${call.id}`}
                        onClick={() => setSelectedCall(call)}
                      >
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Call Details Dialog */}
      <Dialog open={!!selectedCall} onOpenChange={() => setSelectedCall(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Call Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedCall && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Status</p>
                  <StatusBadge status={selectedCall.status} />
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Duration</p>
                  <p className="font-semibold">{selectedCall.duration_seconds} seconds</p>
                </div>
              </div>

              {selectedCall.qualification_result && (
                <div className="p-4 border border-gray-200 rounded-lg">
                  <h4 className="font-semibold mb-3">Qualification Result</h4>
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div>
                      <p className="text-gray-500">Qualified</p>
                      <p className={`font-semibold ${selectedCall.qualification_result.is_qualified ? 'text-emerald-600' : 'text-red-600'}`}>
                        {selectedCall.qualification_result.is_qualified ? 'Yes' : 'No'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Decision Maker</p>
                      <p className="font-semibold">
                        {selectedCall.qualification_result.is_decision_maker ? 'Yes' : 'No'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Interest Level</p>
                      <p className="font-semibold">{selectedCall.qualification_result.interest_level}/10</p>
                    </div>
                  </div>
                  <div className="mt-3">
                    <p className="text-gray-500 text-sm">Score</p>
                    <Progress value={selectedCall.qualification_result.score} className="h-2 mt-1" />
                    <p className="text-right text-sm font-semibold mt-1">{selectedCall.qualification_result.score}/100</p>
                  </div>
                </div>
              )}

              {selectedCall.transcript && selectedCall.transcript.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-3">Transcript</h4>
                  <ScrollArea className="h-[200px] border border-gray-200 rounded-lg p-4">
                    <div className="space-y-3">
                      {selectedCall.transcript.map((msg, idx) => (
                        <div key={idx} className={`flex gap-3 ${msg.role === 'ai' ? '' : 'flex-row-reverse'}`}>
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                            msg.role === 'ai' ? 'bg-blue-100' : 'bg-gray-100'
                          }`}>
                            {msg.role === 'ai' ? (
                              <Phone className="w-4 h-4 text-blue-600" />
                            ) : (
                              <User className="w-4 h-4 text-gray-600" />
                            )}
                          </div>
                          <div className={`p-3 rounded-lg max-w-[80%] ${
                            msg.role === 'ai' ? 'bg-blue-50' : 'bg-gray-50'
                          }`}>
                            <p className="text-sm">{msg.text}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Settings Page
const SettingsPage = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [webhooks, setWebhooks] = useState([]);
  const [showCreateWebhook, setShowCreateWebhook] = useState(false);
  const [newWebhook, setNewWebhook] = useState({
    name: "",
    event_type: "lead_qualified",
    notification_emails: ""
  });
  const [testingWebhook, setTestingWebhook] = useState(null);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
    } catch (error) {
      toast.error("Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  const fetchWebhooks = async () => {
    try {
      const response = await axios.get(`${API}/webhooks`);
      setWebhooks(response.data);
    } catch (error) {
      console.error("Failed to fetch webhooks:", error);
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchWebhooks();
  }, []);

  const updateSettings = async (updates) => {
    try {
      const response = await axios.put(`${API}/settings`, updates);
      setSettings(response.data);
      toast.success("Settings updated");
    } catch (error) {
      toast.error("Failed to update settings");
    }
  };

  const createWebhook = async () => {
    if (!newWebhook.name || !newWebhook.notification_emails) {
      toast.error("Please fill in all fields");
      return;
    }

    const emails = newWebhook.notification_emails.split(',').map(e => e.trim()).filter(e => e);
    if (emails.length === 0) {
      toast.error("Please enter at least one email");
      return;
    }

    try {
      await axios.post(`${API}/webhooks`, {
        name: newWebhook.name,
        event_type: newWebhook.event_type,
        notification_emails: emails
      });
      toast.success("Webhook created!");
      setShowCreateWebhook(false);
      setNewWebhook({ name: "", event_type: "lead_qualified", notification_emails: "" });
      fetchWebhooks();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create webhook");
    }
  };

  const toggleWebhook = async (webhook) => {
    try {
      await axios.put(`${API}/webhooks/${webhook.id}`, { is_active: !webhook.is_active });
      toast.success(`Webhook ${webhook.is_active ? 'disabled' : 'enabled'}`);
      fetchWebhooks();
    } catch (error) {
      toast.error("Failed to update webhook");
    }
  };

  const deleteWebhook = async (id) => {
    try {
      await axios.delete(`${API}/webhooks/${id}`);
      toast.success("Webhook deleted");
      fetchWebhooks();
    } catch (error) {
      toast.error("Failed to delete webhook");
    }
  };

  const testWebhook = async (webhook) => {
    setTestingWebhook(webhook.id);
    try {
      await axios.post(`${API}/webhooks/test/${webhook.id}`);
      toast.success("Test notification sent!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send test notification");
    } finally {
      setTestingWebhook(null);
    }
  };

  if (loading) {
    return (
      <div className="p-6 md:p-8 space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="settings-page">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
          Settings
        </h1>
        <p className="text-gray-500 mt-1">Configure integrations, notifications, and qualification criteria</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Integration Status
            </CardTitle>
            <CardDescription>Connect external services</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center gap-3">
                <Phone className="w-5 h-5 text-gray-600" />
                <div>
                  <p className="font-medium">Twilio Voice</p>
                  <p className="text-sm text-gray-500">For making real phone calls</p>
                </div>
              </div>
              <Badge variant={settings?.twilio_configured ? "default" : "secondary"}>
                {settings?.twilio_configured ? "Connected" : "Not Connected"}
              </Badge>
            </div>
            
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center gap-3">
                <Search className="w-5 h-5 text-gray-600" />
                <div>
                  <p className="font-medium">Twitter/X API</p>
                  <p className="text-sm text-gray-500">For intent monitoring</p>
                </div>
              </div>
              <Badge variant={settings?.twitter_configured ? "default" : "secondary"}>
                {settings?.twitter_configured ? "Connected" : "Not Connected"}
              </Badge>
            </div>
            
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center gap-3">
                <Mail className="w-5 h-5 text-gray-600" />
                <div>
                  <p className="font-medium">Email Notifications</p>
                  <p className="text-sm text-gray-500">Via Resend API</p>
                </div>
              </div>
              <Badge variant={settings?.email_notifications_configured ? "default" : "secondary"}>
                {settings?.email_notifications_configured ? "Connected" : "Not Connected"}
              </Badge>
            </div>
            
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-gray-600" />
                <div>
                  <p className="font-medium">Calendly</p>
                  <p className="text-sm text-gray-500">Via agent booking links</p>
                </div>
              </div>
              <Badge variant="default">Ready</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Qualification Criteria
            </CardTitle>
            <CardDescription>Set thresholds for lead qualification</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="threshold">Qualification Threshold (Score)</Label>
              <Input
                id="threshold"
                data-testid="qual-threshold-input"
                type="number"
                value={settings?.qualification_threshold || 60}
                onChange={(e) => updateSettings({ qualification_threshold: parseInt(e.target.value) })}
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">Leads must score above this to be qualified</p>
            </div>
            
            <div>
              <Label htmlFor="interest">Minimum Interest Level (1-10)</Label>
              <Input
                id="interest"
                data-testid="min-interest-input"
                type="number"
                min="1"
                max="10"
                value={settings?.min_interest_level || 6}
                onChange={(e) => updateSettings({ min_interest_level: parseInt(e.target.value) })}
                className="mt-1"
              />
            </div>
            
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div>
                <p className="font-medium">Require Decision Maker</p>
                <p className="text-sm text-gray-500">Only qualify if speaking with owner/manager</p>
              </div>
              <Button
                variant={settings?.require_decision_maker ? "default" : "outline"}
                data-testid="require-dm-toggle"
                onClick={() => updateSettings({ require_decision_maker: !settings?.require_decision_maker })}
              >
                {settings?.require_decision_maker ? "Required" : "Optional"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Email Notifications / Webhooks Section */}
      <Card className="bg-white border border-gray-200 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Email Notifications
            </CardTitle>
            <CardDescription>Get notified when leads qualify or meetings are booked</CardDescription>
          </div>
          <Button 
            data-testid="create-webhook-btn"
            onClick={() => setShowCreateWebhook(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Notification
          </Button>
        </CardHeader>
        <CardContent>
          {!settings?.email_notifications_configured && (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg mb-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
                <div>
                  <p className="font-medium text-amber-800">Email notifications not configured</p>
                  <p className="text-sm text-amber-700 mt-1">
                    Add your <code className="bg-amber-100 px-1 rounded">RESEND_API_KEY</code> to the backend .env file to enable email notifications.
                    Get your API key at <a href="https://resend.com" target="_blank" rel="noopener noreferrer" className="underline">resend.com</a>
                  </p>
                </div>
              </div>
            </div>
          )}

          {webhooks.length === 0 ? (
            <div className="text-center py-8">
              <Mail className="w-12 h-12 text-gray-300 mx-auto" />
              <p className="text-gray-500 mt-3">No email notifications configured</p>
              <p className="text-sm text-gray-400">Add a notification to get alerts when leads qualify or meetings are booked</p>
            </div>
          ) : (
            <div className="space-y-3">
              {webhooks.map(webhook => (
                <div 
                  key={webhook.id} 
                  data-testid={`webhook-${webhook.id}`}
                  className={`p-4 border rounded-lg ${webhook.is_active ? 'border-gray-200 bg-white' : 'border-gray-100 bg-gray-50 opacity-60'}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900">{webhook.name}</h4>
                        <Badge variant={webhook.is_active ? "default" : "secondary"}>
                          {webhook.is_active ? "Active" : "Disabled"}
                        </Badge>
                        <Badge variant="outline" className="capitalize">
                          {webhook.event_type.replace('_', ' ')}
                        </Badge>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {webhook.notification_emails.map((email, idx) => (
                          <span key={idx} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700">
                            <Mail className="w-3 h-3 mr-1" />
                            {email}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        data-testid={`test-webhook-${webhook.id}`}
                        onClick={() => testWebhook(webhook)}
                        disabled={testingWebhook === webhook.id || !settings?.email_notifications_configured}
                      >
                        {testingWebhook === webhook.id ? "Sending..." : "Test"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        data-testid={`toggle-webhook-${webhook.id}`}
                        onClick={() => toggleWebhook(webhook)}
                      >
                        {webhook.is_active ? "Disable" : "Enable"}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        data-testid={`delete-webhook-${webhook.id}`}
                        onClick={() => deleteWebhook(webhook.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Webhook Dialog */}
      <Dialog open={showCreateWebhook} onOpenChange={setShowCreateWebhook}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Add Email Notification
            </DialogTitle>
            <DialogDescription>
              Configure email alerts for lead qualification or meeting booking events
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="webhook-name">Notification Name *</Label>
              <Input
                id="webhook-name"
                data-testid="webhook-name-input"
                value={newWebhook.name}
                onChange={(e) => setNewWebhook({...newWebhook, name: e.target.value})}
                placeholder="e.g., Sales Team Alert"
                className="mt-1"
              />
            </div>
            
            <div>
              <Label>Event Type *</Label>
              <Select 
                value={newWebhook.event_type} 
                onValueChange={(v) => setNewWebhook({...newWebhook, event_type: v})}
              >
                <SelectTrigger data-testid="webhook-event-select" className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="lead_qualified">Lead Qualified</SelectItem>
                  <SelectItem value="meeting_booked">Meeting Booked</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500 mt-1">
                {newWebhook.event_type === 'lead_qualified' 
                  ? 'Triggers when a lead passes qualification criteria after a call'
                  : 'Triggers when a qualified lead is assigned to an agent for booking'}
              </p>
            </div>
            
            <div>
              <Label htmlFor="webhook-emails">Notification Emails *</Label>
              <Textarea
                id="webhook-emails"
                data-testid="webhook-emails-input"
                value={newWebhook.notification_emails}
                onChange={(e) => setNewWebhook({...newWebhook, notification_emails: e.target.value})}
                placeholder="email1@example.com, email2@example.com"
                className="mt-1"
                rows={2}
              />
              <p className="text-xs text-gray-500 mt-1">Separate multiple emails with commas</p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateWebhook(false)}>Cancel</Button>
            <Button 
              data-testid="save-webhook-btn"
              onClick={createWebhook}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Create Notification
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <div className="App min-h-screen bg-gray-50">
      <BrowserRouter>
        <Routes>
          {/* Public Landing Page */}
          <Route path="/" element={<LandingPage />} />
          
          {/* Dashboard App Routes */}
          <Route path="/app/*" element={
            <div className="flex">
              <Sidebar />
              <main className="flex-1 min-h-screen">
                <Routes>
                  <Route path="/" element={<FunnelPage />} />
                  <Route path="/leads" element={<LeadDiscovery />} />
                  <Route path="/campaigns" element={<Campaigns />} />
                  <Route path="/agents" element={<Agents />} />
                  <Route path="/calls" element={<CallHistory />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </main>
            </div>
          } />
        </Routes>
        <Toaster position="top-right" richColors />
      </BrowserRouter>
    </div>
  );
}

export default App;
