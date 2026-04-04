import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate, useNavigate } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { 
  Phone, Users, Target, Calendar, Settings, LayoutDashboard, 
  History, Search, Plus, Play, Pause, Trash2, ChevronRight,
  PhoneCall, PhoneOff, CheckCircle, XCircle, Clock, TrendingUp,
  Building2, User, Mail, ExternalLink, AlertCircle, Filter,
  ArrowRight, Zap, UserCheck, CalendarCheck, Upload, Download,
  CreditCard, Package, ShoppingCart, LogOut, BarChart3, X, Edit3, Tags, RefreshCw,
  Database, Shield, Rocket, Mic, Volume2
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
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import LoginPage from "@/pages/LoginPage";
import AuthCallback from "@/pages/AuthCallback";
import UsageDashboard from "@/pages/UsageDashboard";
import BookingsPage from "@/pages/BookingsPage";
import CRMIntegrationsPage from "@/pages/CRMIntegrationsPage";
import DNCManagementPage from "@/pages/DNCManagementPage";
import ComplianceSetupPage from "@/pages/ComplianceSetupPage";
import GettingStartedPage from "@/pages/GettingStartedPage";
import TermsPage from "@/pages/TermsPage";
import PrivacyPage from "@/pages/PrivacyPage";
import HelpCenterPage from "@/pages/HelpCenterPage";
import HelpChat from "@/components/HelpChat";
import OnboardingGuide from "@/components/OnboardingGuide";
import SetupWizard from "@/components/SetupWizard";
import TrialBanner from "@/components/TrialBanner";
import PhoneVerificationModal from "@/components/PhoneVerificationModal";
import { VoiceCloneModal, VoiceSettingsModal } from "@/components/VoiceCloning";
import { HelpButton } from "@/components/ProductTour";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Supported languages for ElevenLabs multilingual_v2 (moved outside component)
const SUPPORTED_LANGUAGES = [
  { code: "en", name: "English", flag: "🇺🇸" },
  { code: "es", name: "Spanish", flag: "🇪🇸" },
  { code: "fr", name: "French", flag: "🇫🇷" },
  { code: "de", name: "German", flag: "🇩🇪" },
  { code: "it", name: "Italian", flag: "🇮🇹" },
  { code: "pt", name: "Portuguese", flag: "🇵🇹" },
  { code: "pl", name: "Polish", flag: "🇵🇱" },
  { code: "nl", name: "Dutch", flag: "🇳🇱" },
  { code: "sv", name: "Swedish", flag: "🇸🇪" },
  { code: "da", name: "Danish", flag: "🇩🇰" },
  { code: "fi", name: "Finnish", flag: "🇫🇮" },
  { code: "no", name: "Norwegian", flag: "🇳🇴" },
  { code: "ru", name: "Russian", flag: "🇷🇺" },
  { code: "uk", name: "Ukrainian", flag: "🇺🇦" },
  { code: "tr", name: "Turkish", flag: "🇹🇷" },
  { code: "ar", name: "Arabic", flag: "🇸🇦" },
  { code: "he", name: "Hebrew", flag: "🇮🇱" },
  { code: "hi", name: "Hindi", flag: "🇮🇳" },
  { code: "bn", name: "Bengali", flag: "🇧🇩" },
  { code: "ta", name: "Tamil", flag: "🇮🇳" },
  { code: "te", name: "Telugu", flag: "🇮🇳" },
  { code: "mr", name: "Marathi", flag: "🇮🇳" },
  { code: "id", name: "Indonesian", flag: "🇮🇩" },
  { code: "ms", name: "Malay", flag: "🇲🇾" },
  { code: "vi", name: "Vietnamese", flag: "🇻🇳" },
  { code: "th", name: "Thai", flag: "🇹🇭" },
  { code: "tl", name: "Filipino", flag: "🇵🇭" },
  { code: "zh", name: "Chinese (Mandarin)", flag: "🇨🇳" },
  { code: "ja", name: "Japanese", flag: "🇯🇵" },
  { code: "ko", name: "Korean", flag: "🇰🇷" },
  { code: "el", name: "Greek", flag: "🇬🇷" },
  { code: "cs", name: "Czech", flag: "🇨🇿" },
  { code: "sk", name: "Slovak", flag: "🇸🇰" },
  { code: "hu", name: "Hungarian", flag: "🇭🇺" },
  { code: "ro", name: "Romanian", flag: "🇷🇴" },
  { code: "bg", name: "Bulgarian", flag: "🇧🇬" },
  { code: "hr", name: "Croatian", flag: "🇭🇷" },
  { code: "sr", name: "Serbian", flag: "🇷🇸" },
  { code: "sl", name: "Slovenian", flag: "🇸🇮" },
  { code: "et", name: "Estonian", flag: "🇪🇪" },
  { code: "lv", name: "Latvian", flag: "🇱🇻" },
  { code: "lt", name: "Lithuanian", flag: "🇱🇹" },
  { code: "ca", name: "Catalan", flag: "🇪🇸" },
  { code: "eu", name: "Basque", flag: "🇪🇸" },
  { code: "gl", name: "Galician", flag: "🇪🇸" },
  { code: "cy", name: "Welsh", flag: "🇬🇧" },
  { code: "ga", name: "Irish", flag: "🇮🇪" },
  { code: "af", name: "Afrikaans", flag: "🇿🇦" },
  { code: "sw", name: "Swahili", flag: "🇰🇪" }
];

// Use case templates (moved outside component)
const USE_CASE_TEMPLATES = {
  sales_cold_calling: {
    label: "Sales / Cold Calling",
    description: "Qualify leads and book meetings",
    tips: "Best for: General B2B sales. Customize the opening with your value proposition.",
    prompt: `You are a sales representative for {company}. Your name is {agent_name}.

OPENING (always start with):
"Hi, this is {agent_name} from {company}. Am I speaking with the owner or manager?"

If YES (decision maker):
- Ask about their current pain points
- Discuss budget and timeline if interested
- Book a meeting if qualified

If NO (not decision maker):
- Ask: "When would be a good time to reach them?"
- Get their name for callback
- Thank them and end politely

Keep responses SHORT (1-2 sentences max) - this is a phone call, not a chat.`
  },
  credit_card_processing: {
    label: "Credit Card Processing",
    description: "Merchant services & payment processing sales",
    tips: "Best for: Payment processors, merchant services. Edit the savings percentage and objection handlers to match your offer.",
    prompt: `You are a merchant services consultant for {company}. Your name is {agent_name}.

OPENING:
"Hi, this is {agent_name} with {company}. This is an AI-assisted business call. I'm reaching out to businesses in your area because we've been helping companies save 20-40% on credit card processing fees. Is this the owner or someone who handles your merchant services?"

If YES (decision maker confirmed):
"Perfect! Quick question - are you currently locked into a long-term contract with your processor, or are you month-to-month?"

QUALIFYING QUESTIONS:
1. "What's your approximate monthly credit card volume? Ballpark is fine - under $10K, $10-50K, or over $50K?"
2. "When's the last time you had a rate review? Most businesses haven't looked in over 2 years."
3. "Are you seeing a lot of hidden fees on your statements - like PCI fees, batch fees, or statement fees?"

OBJECTION HANDLERS:

"We already have a processor / Happy with current rates":
"Totally understand. Most of our clients said the same thing before they saw our side-by-side comparison. We do free statement analyses - takes 5 minutes and shows exactly where you're overpaying. No obligation. Would you be open to a quick review?"

"Not interested":
"No problem at all. Just curious - is it the timing, or have you had a bad experience switching processors before? We actually handle the entire transition for you."

"Send me information":
"Absolutely. What I can do is have one of our specialists send you a personalized savings estimate. What email works best, and roughly what's your monthly card volume so they can customize it?"

"We're locked in a contract":
"Got it. When does your contract end? A lot of our clients are surprised to learn we can often cover early termination fees if the savings justify it."

BOOKING:
"Based on what you've shared, I think we can definitely save you money. Our specialist can do a free 10-minute rate review - they'll show you exactly where you're overpaying. Do you have 10 minutes this week?"

Keep responses SHORT (1-2 sentences) - this is a phone call.`
  },
  appointment_setter: {
    label: "Appointment Setter",
    description: "Schedule appointments and manage bookings",
    tips: "Best for: Service businesses, consultants. Add your available time slots and booking rules.",
    prompt: `You are a scheduling assistant for {company}. Your name is {agent_name}.

OPENING: "Hi, this is {agent_name} from {company}. Am I speaking with the owner or manager?"

Help callers book, reschedule, or cancel appointments. Confirm their contact information and preferred times. Send calendar invites after booking. Keep responses SHORT (1-2 sentences) - this is a phone call.`
  },
  receptionist: {
    label: "Receptionist",
    description: "Answer calls and route to departments",
    tips: "Best for: Offices, clinics. Add your department list and common FAQs.",
    prompt: `You are the front desk receptionist for {company}. Your name is {agent_name}. Greet callers warmly, ask how you can help, and route them to the appropriate department or person. Take messages if someone is unavailable. Keep responses SHORT (1-2 sentences) - this is a phone call.`
  },
  customer_service: {
    label: "Customer Service",
    description: "Handle support inquiries and issues",
    tips: "Best for: Support teams. Add common issues and troubleshooting steps for your product.",
    prompt: `You are a customer support agent for {company}. Your name is {agent_name}. Listen to the customer's issue, troubleshoot common problems, and provide solutions. Escalate to a human agent if needed. Always confirm the issue is resolved before ending the call. Keep responses SHORT (1-2 sentences) - this is a phone call.`
  },
  answering_service: {
    label: "Answering Service",
    description: "After-hours message taking",
    tips: "Best for: After-hours coverage. Customize the callback timeframe for your business hours.",
    prompt: `You are the after-hours answering service for {company}. Your name is {agent_name}. Take the caller's name, phone number, and a brief message about their inquiry. Let them know someone will return their call during business hours. Keep responses SHORT (1-2 sentences) - this is a phone call.`
  }
};

// Navigation Sidebar with Auth
const Sidebar = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const navItems = [
    { path: "/app/getting-started", icon: Rocket, label: "Getting Started" },
    { path: "/app", icon: Filter, label: "Funnel" },
    { path: "/app/usage", icon: BarChart3, label: "Usage" },
    { path: "/app/leads", icon: Search, label: "Lead Discovery" },
    { path: "/app/campaigns", icon: Target, label: "Campaigns" },
    { path: "/app/agents", icon: Users, label: "Agents" },
    { path: "/app/bookings", icon: Calendar, label: "Bookings" },
    { path: "/app/calls", icon: History, label: "Call History" },
    { path: "/app/integrations", icon: Database, label: "CRM Integrations" },
    { path: "/app/compliance", icon: Shield, label: "Compliance" },
    { path: "/app/packs", icon: Package, label: "Credit Packs" },
    { path: "/app/settings", icon: Settings, label: "Settings" },
  ];

  const handleLogout = async () => {
    await logout();
    window.location.href = "/";
  };

  // Close mobile menu when route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const SidebarContent = () => (
    <>
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
            <Phone className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              DialGenix.ai
            </h1>
            <p className="text-xs text-gray-500">AI Sales Automation</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-4 overflow-y-auto">
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
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      
      {/* User Info & Credits */}
      {user && (
        <div className="p-4 border-t border-gray-100">
          <div className="bg-gradient-to-r from-cyan-50 to-teal-50 border border-cyan-200 rounded-lg p-3 mb-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-full flex items-center justify-center">
                {user.picture ? (
                  <img src={user.picture} alt="" className="w-8 h-8 rounded-full" />
                ) : (
                  <User className="w-4 h-4 text-white" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user.name}</p>
                <p className="text-xs text-gray-500 truncate">{user.email}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-center">
              <div className="bg-white/60 rounded-md p-2">
                <p className="text-lg font-bold text-cyan-600">{user.lead_credits_remaining || 0}</p>
                <p className="text-[10px] text-gray-500">Lead Credits</p>
              </div>
              <div className="bg-white/60 rounded-md p-2">
                <p className="text-lg font-bold text-teal-600">{user.call_credits_remaining || 0}</p>
                <p className="text-[10px] text-gray-500">Call Credits</p>
              </div>
            </div>
          </div>
          
          <Button 
            onClick={handleLogout}
            variant="ghost"
            className="w-full justify-start text-gray-600 hover:text-red-600 hover:bg-red-50"
            data-testid="logout-btn"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Sign Out
          </Button>
        </div>
      )}
    </>
  );

  return (
    <>
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Phone className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            DialGenix.ai
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            console.log('Menu toggle clicked, current state:', mobileMenuOpen);
            setMobileMenuOpen(prev => !prev);
          }}
          data-testid="mobile-menu-toggle"
          className="p-2"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <LayoutDashboard className="w-6 h-6" />}
        </Button>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside className={`
        lg:hidden fixed top-0 left-0 h-full w-72 bg-white z-50 transform transition-transform duration-300 ease-in-out flex flex-col
        ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <SidebarContent />
      </aside>

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-64 bg-white border-r border-gray-200 min-h-screen flex-col">
        <SidebarContent />
      </aside>
    </>
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
  const [setupStatus, setSetupStatus] = useState(null);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const token = localStorage.getItem('session_token');
      const [leadsRes, statsRes, agentsRes, campaignsRes, setupRes] = await Promise.all([
        axios.get(`${API}/leads`),
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/agents`),
        axios.get(`${API}/campaigns`),
        axios.get(`${API}/setup/status`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: { can_make_calls: true } }))
      ]);
      setLeads(leadsRes.data);
      setStats(statsRes.data);
      setAgents(agentsRes.data.filter(a => a.is_active));
      setCampaigns(campaignsRes.data.filter(c => c.status === 'active'));
      setSetupStatus(setupRes.data);
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
    // Check if setup is complete before allowing calls
    if (setupStatus && !setupStatus.can_make_calls) {
      toast.error("Complete your setup first to make calls", {
        description: "Go to Getting Started to finish setup",
        action: {
          label: "Go to Setup",
          onClick: () => navigate("/app/getting-started")
        }
      });
      return;
    }
    
    if (!selectedCampaign) {
      toast.error("Please select a campaign first");
      return;
    }
    try {
      await axios.post(`${API}/calls/simulate?lead_id=${leadId}&campaign_id=${selectedCampaign}`);
      toast.success("Call started!");
      setTimeout(fetchData, 3000);
    } catch (error) {
      if (error.response?.status === 402) {
        toast.error("You've run out of call credits", {
          description: "Upgrade your plan to continue making calls",
          action: {
            label: "Upgrade",
            onClick: () => navigate("/app/packs")
          }
        });
      } else {
        toast.error("Failed to start call");
      }
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
  const { refreshUser } = useAuth();
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("Toast alternative");
  const [industry, setIndustry] = useState("");
  const [location, setLocation] = useState("");
  const [campaigns, setCampaigns] = useState([]);
  const [selectedLead, setSelectedLead] = useState(null);
  const [selectedCampaign, setSelectedCampaign] = useState("");
  const [activeTab, setActiveTab] = useState("discover");
  const [setupStatus, setSetupStatus] = useState(null);
  const [verifyingPhone, setVerifyingPhone] = useState(null); // Track which lead is being verified
  
  // Custom keywords state
  const [customKeywords, setCustomKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState("");
  const [showKeywordManager, setShowKeywordManager] = useState(false);
  const [bulkKeywords, setBulkKeywords] = useState("");
  
  // Preview state
  const [previewing, setPreviewing] = useState(false);
  const [previewLeads, setPreviewLeads] = useState([]);
  const [showPreview, setShowPreview] = useState(false);
  
  // Line type filter
  const [lineTypeFilter, setLineTypeFilter] = useState("all");

  const defaultIntentKeywords = [
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
  
  // Use custom keywords if any, otherwise use defaults
  const intentKeywords = customKeywords.length > 0 ? customKeywords : defaultIntentKeywords;

  const addKeyword = () => {
    const keyword = newKeyword.trim();
    if (keyword && !customKeywords.includes(keyword) && customKeywords.length < 100) {
      setCustomKeywords([...customKeywords, keyword]);
      setNewKeyword("");
    } else if (customKeywords.length >= 100) {
      toast.error("Maximum 100 keywords allowed");
    }
  };

  const removeKeyword = (keywordToRemove) => {
    setCustomKeywords(customKeywords.filter(k => k !== keywordToRemove));
  };

  const clearAllKeywords = () => {
    setCustomKeywords([]);
  };

  const addBulkKeywords = () => {
    const keywords = bulkKeywords
      .split(/[\n,]/)
      .map(k => k.trim())
      .filter(k => k && !customKeywords.includes(k));
    
    const available = 100 - customKeywords.length;
    const toAdd = keywords.slice(0, available);
    
    if (toAdd.length > 0) {
      setCustomKeywords([...customKeywords, ...toAdd]);
      setBulkKeywords("");
      toast.success(`Added ${toAdd.length} keywords`);
      if (keywords.length > available) {
        toast.warning(`${keywords.length - available} keywords skipped (100 max limit)`);
      }
    }
  };

  // Preview example leads (FREE - no credits used)
  const previewExamples = async () => {
    setPreviewing(true);
    setShowPreview(true);
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(`${API}/leads/preview-examples`, {
        search_query: searchQuery,
        industry: industry || null,
        location: location || null,
        custom_keywords: customKeywords.length > 0 ? customKeywords : null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setPreviewLeads(response.data.example_leads || []);
      toast.success("Preview generated! These are example leads based on your keywords.");
    } catch (error) {
      toast.error("Failed to generate preview");
      setPreviewLeads([]);
    } finally {
      setPreviewing(false);
    }
  };

  // Load saved keywords from backend
  const loadSavedKeywords = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/user/keywords`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.keywords && response.data.keywords.length > 0) {
        setCustomKeywords(response.data.keywords);
      }
    } catch (error) {
      console.error("Failed to load saved keywords:", error);
    }
  };

  // Save keywords to backend
  const saveKeywords = async () => {
    try {
      const token = localStorage.getItem('session_token');
      await axios.post(`${API}/user/keywords`, 
        { keywords: customKeywords },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`Saved ${customKeywords.length} keywords to your profile`);
    } catch (error) {
      toast.error("Failed to save keywords");
    }
  };

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

  const fetchSetupStatus = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/setup/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSetupStatus(response.data);
    } catch (error) {
      console.error("Failed to fetch setup status:", error);
    }
  };

  useEffect(() => {
    fetchLeads();
    fetchCampaigns();
    loadSavedKeywords();
    fetchSetupStatus();
  }, []);

  const discoverLeads = async () => {
    setDiscovering(true);
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(`${API}/leads/gpt-intent-search`, {
        search_query: searchQuery,
        industry: industry || null,
        location: location || null,
        max_results: 10,
        custom_keywords: customKeywords.length > 0 ? customKeywords : null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const { discovered, credits_used, credits_remaining } = response.data;
      toast.success(
        `Discovered ${discovered} high-intent leads! (${credits_used} credits used, ${credits_remaining} remaining)`
      );
      fetchLeads();
      // Refresh user data to update sidebar credits
      refreshUser();
    } catch (error) {
      if (error.response?.status === 402) {
        toast.error(error.response.data.detail || "Insufficient credits. Please purchase more leads.");
      } else {
        toast.error("Failed to discover leads");
      }
    } finally {
      setDiscovering(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/leads/upload-csv`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(response.data.message);
      if (response.data.errors > 0) {
        toast.warning(`${response.data.errors} rows had errors`);
      }
      fetchLeads();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to upload CSV");
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const exportLeads = async () => {
    try {
      window.open(`${API}/leads/export-csv`, '_blank');
      toast.success("Downloading leads CSV...");
    } catch (error) {
      toast.error("Failed to export leads");
    }
  };

  const simulateCall = async (leadId) => {
    // Check if setup is complete before allowing calls
    if (setupStatus && !setupStatus.can_make_calls) {
      toast.error("Complete your setup first to make calls", {
        description: "Go to Getting Started to finish setup",
        action: {
          label: "Go to Setup",
          onClick: () => navigate("/app/getting-started")
        }
      });
      return;
    }
    
    if (!selectedCampaign) {
      toast.error("Please select a campaign first");
      return;
    }
    
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(
        `${API}/calls/simulate?lead_id=${leadId}&campaign_id=${selectedCampaign}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const { credits_remaining } = response.data;
      toast.success(`Call started! (${credits_remaining} call credits remaining)`);
      setTimeout(fetchLeads, 3000);
      // Refresh user data to update sidebar credits
      refreshUser();
    } catch (error) {
      if (error.response?.status === 402) {
        toast.error(error.response.data.detail || "Insufficient call credits. Please purchase more.");
      } else {
        toast.error("Failed to start call");
      }
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

  const verifyPhone = async (leadId) => {
    setVerifyingPhone(leadId);
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(
        `${API}/leads/${leadId}/verify-phone`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const { verification } = response.data;
      const lineType = verification.line_type || 'unknown';
      const carrier = verification.carrier || 'Unknown carrier';
      
      // Update local state with verification result
      setLeads(prevLeads => 
        prevLeads.map(lead => 
          lead.id === leadId 
            ? { 
                ...lead, 
                line_type: lineType,
                carrier: carrier,
                phone_verified: verification.is_valid,
                dial_priority: verification.dial_priority
              }
            : lead
        )
      );
      
      // Show appropriate toast based on line type
      if (verification.is_mobile) {
        toast.success(`Mobile number verified: ${carrier}`, {
          description: "High pickup rate expected (80%+)"
        });
      } else if (verification.is_landline) {
        toast.info(`Landline verified: ${carrier}`, {
          description: "Business line - 20% typical pickup rate"
        });
      } else if (verification.is_voip) {
        toast.warning(`VoIP number detected: ${carrier}`, {
          description: "May have lower pickup rate"
        });
      } else {
        toast.info(`Phone verified: ${lineType}`);
      }
    } catch (error) {
      const errDetail = error.response?.data?.detail;
      const errMsg = typeof errDetail === 'string' ? errDetail : "Failed to verify phone";
      toast.error(errMsg);
    } finally {
      setVerifyingPhone(null);
    }
  };

  const verifyAllUnverified = async () => {
    const unverifiedLeads = leads.filter(l => !l.phone_verified && l.phone);
    if (unverifiedLeads.length === 0) {
      toast.info("All leads are already verified");
      return;
    }
    
    setVerifyingPhone('bulk');
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(
        `${API}/leads/verify-phones-bulk`,
        { verify_all_unverified: true },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const results = response.data.results || {};
      toast.success(`Verified ${results.verified || 0} phone numbers`, {
        description: `Mobile: ${results.mobile || 0}, Landline: ${results.landline || 0}, VoIP: ${results.voip || 0}`
      });
      
      fetchLeads(); // Refresh to show updated data
    } catch (error) {
      const errDetail = error.response?.data?.detail;
      const errMsg = typeof errDetail === 'string' ? errDetail : "Failed to bulk verify phones";
      toast.error(errMsg);
    } finally {
      setVerifyingPhone(null);
    }
  };

  // Count unverified leads
  const unverifiedCount = leads.filter(l => !l.phone_verified && l.phone).length;

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="lead-discovery-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Lead Discovery
          </h1>
          <p className="text-gray-500 mt-1">Find businesses actively searching for payment solutions</p>
        </div>
        <div className="flex items-center gap-2">
          {unverifiedCount > 0 && (
            <Button
              variant="outline"
              onClick={verifyAllUnverified}
              disabled={verifyingPhone === 'bulk'}
              className="border-blue-200 text-blue-600 hover:bg-blue-50"
              data-testid="verify-all-phones-btn"
            >
              {verifyingPhone === 'bulk' ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2" />
              )}
              Verify All ({unverifiedCount})
            </Button>
          )}
          <Button
            variant="outline"
            onClick={exportLeads}
            disabled={leads.length === 0}
            className="border-gray-300"
          >
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Tabs for Discover / Upload */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="discover" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            AI Discovery
          </TabsTrigger>
          <TabsTrigger value="upload" className="flex items-center gap-2">
            <Upload className="w-4 h-4" />
            Upload CSV
          </TabsTrigger>
        </TabsList>

        <TabsContent value="discover" className="space-y-4 mt-4">
          {/* Intent Keywords Section */}
          <Card className="bg-gradient-to-r from-cyan-50 to-teal-50 border border-cyan-200 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Tags className="w-4 h-4 text-cyan-700" />
                  <p className="text-sm font-medium text-cyan-800">
                    Intent Keywords ({customKeywords.length > 0 ? `${customKeywords.length} custom` : 'defaults'})
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowKeywordManager(!showKeywordManager)}
                  className="text-cyan-700 border-cyan-300 hover:bg-cyan-100"
                  data-testid="manage-keywords-btn"
                >
                  <Edit3 className="w-3 h-3 mr-1" />
                  {showKeywordManager ? 'Hide' : 'Manage Keywords'}
                </Button>
              </div>
              
              {/* Quick Select Keywords */}
              <div className="flex flex-wrap gap-2">
                {intentKeywords.slice(0, 15).map((keyword) => (
                  <button
                    key={keyword}
                    onClick={() => setSearchQuery(keyword)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-1 ${
                      searchQuery === keyword
                        ? 'bg-cyan-600 text-white'
                        : 'bg-white text-cyan-700 border border-cyan-300 hover:bg-cyan-100'
                    }`}
                  >
                    {keyword}
                    {customKeywords.length > 0 && (
                      <X 
                        className="w-3 h-3 ml-1 hover:text-red-500" 
                        onClick={(e) => { e.stopPropagation(); removeKeyword(keyword); }}
                      />
                    )}
                  </button>
                ))}
                {intentKeywords.length > 15 && (
                  <span className="px-3 py-1.5 text-sm text-cyan-600">
                    +{intentKeywords.length - 15} more
                  </span>
                )}
              </div>

              {/* Keyword Manager Panel */}
              {showKeywordManager && (
                <div className="mt-4 pt-4 border-t border-cyan-200 space-y-4">
                  {/* Add Single Keyword */}
                  <div>
                    <Label className="text-cyan-800 text-sm">Add Keyword</Label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        value={newKeyword}
                        onChange={(e) => setNewKeyword(e.target.value)}
                        placeholder="e.g., best CRM software"
                        className="flex-1"
                        onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
                        data-testid="new-keyword-input"
                      />
                      <Button 
                        onClick={addKeyword}
                        disabled={!newKeyword.trim() || customKeywords.length >= 100}
                        className="bg-cyan-600 hover:bg-cyan-700"
                        data-testid="add-keyword-btn"
                      >
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Bulk Add Keywords */}
                  <div>
                    <Label className="text-cyan-800 text-sm">Bulk Add (paste multiple, comma or newline separated)</Label>
                    <div className="flex gap-2 mt-1">
                      <Textarea
                        value={bulkKeywords}
                        onChange={(e) => setBulkKeywords(e.target.value)}
                        placeholder="keyword 1, keyword 2&#10;keyword 3&#10;keyword 4"
                        className="flex-1 h-20"
                        data-testid="bulk-keywords-input"
                      />
                      <Button 
                        onClick={addBulkKeywords}
                        disabled={!bulkKeywords.trim()}
                        className="bg-cyan-600 hover:bg-cyan-700 self-end"
                        data-testid="add-bulk-btn"
                      >
                        Add All
                      </Button>
                    </div>
                  </div>

                  {/* Keywords Summary */}
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-cyan-700">
                      {customKeywords.length}/100 keywords
                    </span>
                    <div className="flex gap-2">
                      {customKeywords.length > 0 && (
                        <>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={saveKeywords}
                            className="text-green-600 border-green-300 hover:bg-green-50"
                            data-testid="save-keywords-btn"
                          >
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Save Keywords
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={clearAllKeywords}
                            className="text-red-600 border-red-300 hover:bg-red-50"
                            data-testid="clear-keywords-btn"
                          >
                            <Trash2 className="w-3 h-3 mr-1" />
                            Clear All
                          </Button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* All Custom Keywords List */}
                  {customKeywords.length > 0 && (
                    <div className="bg-white rounded-lg p-3 max-h-40 overflow-y-auto">
                      <div className="flex flex-wrap gap-1">
                        {customKeywords.map((keyword, idx) => (
                          <span 
                            key={idx}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-cyan-100 text-cyan-800 rounded text-xs"
                          >
                            {keyword}
                            <X 
                              className="w-3 h-3 cursor-pointer hover:text-red-500" 
                              onClick={() => removeKeyword(keyword)}
                            />
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
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
              <div className="mt-4 flex justify-end gap-3">
                <Button 
                  variant="outline"
                  data-testid="preview-btn"
                  onClick={previewExamples} 
                  disabled={previewing}
                  className="border-cyan-500 text-cyan-700 hover:bg-cyan-50"
                >
                  {previewing ? (
                    <>
                      <Clock className="w-4 h-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Preview Examples (Free)
                    </>
                  )}
                </Button>
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

          {/* Preview Results Section */}
          {showPreview && (
            <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 shadow-sm mt-4">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Search className="w-5 h-5 text-amber-600" />
                    <CardTitle className="text-lg text-amber-800" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                      Example Leads Preview
                    </CardTitle>
                    <span className="px-2 py-0.5 bg-amber-200 text-amber-800 text-xs rounded-full">FREE</span>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setShowPreview(false)}
                    className="text-amber-600 hover:text-amber-800"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                <CardDescription className="text-amber-700">
                  These are example leads based on your keywords. Run "Discover" to find and save real leads.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {previewing ? (
                  <div className="text-center py-8">
                    <Clock className="w-8 h-8 animate-spin text-amber-500 mx-auto mb-2" />
                    <p className="text-amber-700">Generating preview examples...</p>
                  </div>
                ) : previewLeads.length > 0 ? (
                  <div className="space-y-3">
                    {previewLeads.map((lead, idx) => (
                      <div key={idx} className="bg-white rounded-lg p-4 border border-amber-200">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-semibold text-gray-900">{lead.name}</h4>
                            <p className="text-sm text-gray-600">{lead.industry} • {lead.location}</p>
                            <p className="text-sm text-gray-500 mt-1">{lead.phone}</p>
                          </div>
                          <span className="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded">Example</span>
                        </div>
                        <div className="mt-2">
                          <p className="text-xs text-gray-500 mb-1">Intent Signals:</p>
                          <div className="flex flex-wrap gap-1">
                            {(lead.intent_signals || []).slice(0, 3).map((signal, i) => (
                              <span key={i} className="px-2 py-0.5 bg-cyan-100 text-cyan-700 text-xs rounded">
                                {signal}
                              </span>
                            ))}
                          </div>
                        </div>
                        {lead.pain_point && (
                          <p className="text-xs text-gray-500 mt-2 italic">"{lead.pain_point}"</p>
                        )}
                      </div>
                    ))}
                    <div className="text-center pt-2">
                      <Button 
                        onClick={discoverLeads}
                        disabled={discovering}
                        className="bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white"
                      >
                        <Zap className="w-4 h-4 mr-2" />
                        Find Real Leads Like These
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-center py-4 text-amber-700">No preview leads generated. Try different keywords.</p>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="upload" className="mt-4">
          <Card className="bg-white border border-gray-200 shadow-sm">
            <CardHeader>
              <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                Upload Your Lead List
              </CardTitle>
              <CardDescription>
                Import leads from a CSV file. We'll call them for you.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-cyan-400 transition-colors">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-2">Drag and drop your CSV file, or click to browse</p>
                <p className="text-sm text-gray-400 mb-4">Required columns: business_name, phone</p>
                <p className="text-sm text-gray-400 mb-4">Optional: email, contact_name</p>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="csv-upload"
                  disabled={uploading}
                />
                <label htmlFor="csv-upload">
                  <Button 
                    asChild 
                    disabled={uploading}
                    className="bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white cursor-pointer"
                  >
                    <span>
                      {uploading ? (
                        <>
                          <Clock className="w-4 h-4 mr-2 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4 mr-2" />
                          Choose CSV File
                        </>
                      )}
                    </span>
                  </Button>
                </label>
              </div>
              
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-700 mb-2">CSV Template</p>
                <code className="text-xs text-gray-600 block bg-white p-3 rounded border">
                  business_name,phone,email,contact_name<br/>
                  "Joe's Pizza","+1-555-0123","joe@joespizza.com","Joe Smith"<br/>
                  "Main St Retail","+1-555-0124","info@mainst.com","Sarah Johnson"
                </code>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Leads Table */}
      <Card className="bg-white border border-gray-200 shadow-sm">
        <CardHeader className="border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-center justify-between">
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Discovered Leads ({leads.length})
            </CardTitle>
            <div className="flex items-center gap-4">
              {/* Line Type Filter */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Filter:</span>
                <Select value={lineTypeFilter} onValueChange={setLineTypeFilter}>
                  <SelectTrigger className="w-[140px] h-8" data-testid="line-type-filter">
                    <SelectValue placeholder="All Types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="mobile">Mobile Only</SelectItem>
                    <SelectItem value="landline">Landline Only</SelectItem>
                    <SelectItem value="voip">VoIP Only</SelectItem>
                    <SelectItem value="unverified">Unverified</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="text-sm text-gray-500">
                {leads.filter(l => l.source === 'gpt_intent_search').length} from GPT Intent Search
              </div>
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
              {leads
                .filter(lead => {
                  if (lineTypeFilter === 'all') return true;
                  if (lineTypeFilter === 'unverified') return !lead.phone_verified;
                  if (lineTypeFilter === 'mobile') return ['mobile', 'cellphone', 'wireless'].includes(lead.line_type?.toLowerCase());
                  if (lineTypeFilter === 'landline') return ['landline', 'fixedline', 'fixed'].includes(lead.line_type?.toLowerCase());
                  if (lineTypeFilter === 'voip') return ['voip', 'nonfixedvoip', 'non-fixed voip', 'virtual'].includes(lead.line_type?.toLowerCase());
                  return true;
                })
                .map((lead) => (
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
                        <span className="flex items-center gap-2">
                          {lead.phone}
                          {/* Line Type Badge */}
                          {lead.line_type && lead.line_type !== 'unknown' && (
                            <Badge 
                              className={`text-xs ${
                                lead.line_type === 'mobile' || lead.line_type === 'cellphone' || lead.line_type === 'wireless'
                                  ? 'bg-green-100 text-green-700 border-green-200'
                                  : lead.line_type === 'landline' || lead.line_type === 'fixedline'
                                    ? 'bg-blue-100 text-blue-700 border-blue-200'
                                    : lead.line_type === 'voip' || lead.line_type === 'nonFixedVoip'
                                      ? 'bg-orange-100 text-orange-700 border-orange-200'
                                      : 'bg-gray-100 text-gray-600'
                              }`}
                              data-testid={`line-type-${lead.id}`}
                            >
                              {lead.line_type === 'mobile' || lead.line_type === 'cellphone' || lead.line_type === 'wireless' ? 'Mobile' :
                               lead.line_type === 'landline' || lead.line_type === 'fixedline' ? 'Landline' :
                               lead.line_type === 'voip' || lead.line_type === 'nonFixedVoip' ? 'VoIP' : lead.line_type}
                            </Badge>
                          )}
                          {/* Verify Button */}
                          {!lead.phone_verified && lead.phone && (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 px-2 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                              onClick={() => verifyPhone(lead.id)}
                              disabled={verifyingPhone === lead.id}
                              data-testid={`verify-phone-${lead.id}`}
                            >
                              {verifyingPhone === lead.id ? (
                                <RefreshCw className="w-3 h-3 animate-spin" />
                              ) : (
                                <>
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  Verify
                                </>
                              )}
                            </Button>
                          )}
                          {lead.phone_verified && !lead.line_type && (
                            <CheckCircle className="w-4 h-4 text-green-500" title="Phone verified" />
                          )}
                        </span>
                        {lead.email && <span>{lead.email}</span>}
                      </div>
                      {/* Carrier info if available */}
                      {lead.carrier && (
                        <p className="text-xs text-gray-400 mt-0.5">{lead.carrier}</p>
                      )}
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
  const { token } = useAuth();
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [notes, setNotes] = useState("");
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    if (lead) {
      fetchAgents();
    }
  }, [lead]);

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API}/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
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
        agent_id: selectedAgent,
        notes: notes || null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Show success with booking link
      toast.success(
        <div>
          <p className="font-medium">Meeting booked successfully!</p>
          <p className="text-sm text-gray-600 mt-1">Opening personalized Calendly link...</p>
        </div>
      );
      
      // Open the personalized booking link
      window.open(response.data.booking_link, '_blank');
      onSuccess();
    } catch (error) {
      const detail = error.response?.data?.detail || "Failed to book meeting";
      if (error.response?.status === 403) {
        toast.error("Calendar booking requires Professional plan or higher");
      } else {
        toast.error(detail);
      }
    } finally {
      setBooking(false);
    }
  };

  if (!lead) return null;

  const selectedAgentData = agents.find(a => a.id === selectedAgent);

  return (
    <Dialog open={!!lead} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Book Meeting for {lead.business_name}
          </DialogTitle>
          <DialogDescription>
            Select an agent to assign this qualified lead. A personalized booking link will be generated with the lead's info pre-filled.
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
                {agents.length === 0 ? (
                  <div className="p-2 text-sm text-gray-500 text-center">
                    No agents available. Create an agent first.
                  </div>
                ) : (
                  agents.map(agent => (
                    <SelectItem key={agent.id} value={agent.id}>
                      <div className="flex items-center gap-2">
                        <span>{agent.name}</span>
                        <span className="text-gray-500 text-xs">
                          ({agent.booked_meetings || 0} meetings)
                        </span>
                      </div>
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label>Notes (optional)</Label>
            <Input
              placeholder="Add notes about this lead..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1"
            />
          </div>
          
          {selectedAgentData && (
            <div className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-100">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Calendar className="w-4 h-4 text-purple-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    Personalized Calendly Link
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    The booking link will include:
                  </p>
                  <ul className="text-xs text-gray-500 mt-1 space-y-0.5">
                    {lead.contact_name && <li>• Name: {lead.contact_name}</li>}
                    {lead.email && <li>• Email: {lead.email}</li>}
                    {lead.phone && <li>• Phone: {lead.phone}</li>}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button 
            data-testid="confirm-booking-btn"
            onClick={bookMeeting}
            disabled={booking || !selectedAgent}
            className="bg-purple-600 hover:bg-purple-700 text-white gap-2"
          >
            {booking ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Booking...
              </>
            ) : (
              <>
                <Calendar className="w-4 h-4" />
                Book Meeting
              </>
            )}
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
  const [showFollowUpSettings, setShowFollowUpSettings] = useState(null); // campaign for settings modal
  const [followUpSettings, setFollowUpSettings] = useState({
    enabled: true,
    no_answer_retry_enabled: true,
    no_answer_retry_count: 3,
    no_answer_retry_delay_hours: 24,
    voicemail_followup_enabled: true,
    voicemail_followup_delay_hours: 48
  });
  const [newCampaign, setNewCampaign] = useState({
    name: "",
    description: "",
    ai_script: "Hello, this is an AI assistant calling about credit card processing solutions for your business. Am I speaking with the owner or manager?",
    calls_per_day: 100,
    voicemail_enabled: true,
    voicemail_message: "",
    response_wait_seconds: 4,
    company_name: "",
    icp_config: {
      target_industries: [],
      preferred_company_sizes: ["11-50", "51-200"],
      min_intent_signals: 1,
      preferred_roles: ["Owner", "CEO", "Manager", "Director"]
    },
    min_icp_score: 0
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
      setNewCampaign({ name: "", description: "", ai_script: "", calls_per_day: 100, voicemail_enabled: true, voicemail_message: "", response_wait_seconds: 4, company_name: "", icp_config: { target_industries: [], preferred_company_sizes: ["11-50", "51-200"], min_intent_signals: 1, preferred_roles: ["Owner", "CEO", "Manager", "Director"] }, min_icp_score: 0 });
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

  const openFollowUpSettings = async (campaign) => {
    setShowFollowUpSettings(campaign);
    try {
      const response = await axios.get(`${API}/campaigns/${campaign.id}/followup-settings`);
      setFollowUpSettings(response.data.settings);
    } catch (error) {
      // Use defaults if no settings exist
      setFollowUpSettings({
        enabled: true,
        no_answer_retry_enabled: true,
        no_answer_retry_count: 3,
        no_answer_retry_delay_hours: 24,
        voicemail_followup_enabled: true,
        voicemail_followup_delay_hours: 48
      });
    }
  };

  const saveFollowUpSettings = async () => {
    if (!showFollowUpSettings) return;
    
    try {
      const formData = new FormData();
      Object.entries(followUpSettings).forEach(([key, value]) => {
        formData.append(key, value);
      });
      
      await axios.put(`${API}/campaigns/${showFollowUpSettings.id}/followup-settings`, formData);
      toast.success("Follow-up settings saved!");
      setShowFollowUpSettings(null);
      fetchCampaigns();
    } catch (error) {
      toast.error("Failed to save follow-up settings");
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
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      data-testid={`followup-settings-${campaign.id}`}
                      onClick={() => openFollowUpSettings(campaign)}
                      className="text-cyan-600 hover:text-cyan-700 hover:bg-cyan-50"
                      title="Follow-up Settings"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </Button>
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

            <div>
              <Label htmlFor="company-name">Your Company Name</Label>
              <Input
                id="company-name"
                value={newCampaign.company_name}
                onChange={(e) => setNewCampaign({...newCampaign, company_name: e.target.value})}
                placeholder="e.g., ABC Solutions"
                className="mt-1"
              />
              <p className="text-xs text-gray-400 mt-1">Used in AI greeting and voicemail</p>
            </div>

            {/* AI Conversation Settings */}
            <div className="border-t pt-4 mt-4">
              <h4 className="font-medium mb-3">AI Conversation Settings</h4>
              
              <div className="mb-4">
                <Label htmlFor="response-wait">Response Wait Time (seconds)</Label>
                <div className="flex items-center gap-3 mt-1">
                  <Input
                    id="response-wait"
                    type="number"
                    min="1"
                    max="10"
                    value={newCampaign.response_wait_seconds}
                    onChange={(e) => setNewCampaign({...newCampaign, response_wait_seconds: parseInt(e.target.value) || 4})}
                    className="w-24"
                  />
                  <span className="text-sm text-gray-500">seconds</span>
                  <div className="flex-1">
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={newCampaign.response_wait_seconds}
                      onChange={(e) => setNewCampaign({...newCampaign, response_wait_seconds: parseInt(e.target.value)})}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                    />
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  How long AI waits for caller to respond before continuing. Recommended: 4-6 seconds.
                </p>
              </div>
            </div>

            {/* Voicemail Drop Settings */}
            <div className="border-t pt-4 mt-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <Label className="text-base font-medium">Voicemail Drop</Label>
                  <p className="text-sm text-gray-500">Auto-leave voicemail when machine detected (saves ~$0.14/call)</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newCampaign.voicemail_enabled}
                    onChange={(e) => setNewCampaign({...newCampaign, voicemail_enabled: e.target.checked})}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-cyan-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500"></div>
                </label>
              </div>
              
              {newCampaign.voicemail_enabled && (
                <div>
                  <Label htmlFor="voicemail-message">Custom Voicemail (optional)</Label>
                  <Textarea
                    id="voicemail-message"
                    value={newCampaign.voicemail_message}
                    onChange={(e) => setNewCampaign({...newCampaign, voicemail_message: e.target.value})}
                    placeholder="Hi {contact_name}, this is a quick message for {business_name}. I'm calling from {company_name} about an opportunity..."
                    className="mt-1 min-h-[80px]"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Variables: {'{contact_name}'}, {'{business_name}'}, {'{company_name}'}
                  </p>
                </div>
              )}
            </div>

            {/* ICP (Ideal Customer Profile) Settings */}
            <div className="border-t pt-4 mt-4">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-5 h-5 text-cyan-500" />
                <h4 className="font-medium">Ideal Customer Profile (ICP)</h4>
              </div>
              <p className="text-sm text-gray-500 mb-4">Configure which leads are prioritized for calling based on their fit.</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Target Company Sizes</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {["1-10", "11-50", "51-200", "201-500", "500+"].map(size => (
                      <button
                        key={size}
                        type="button"
                        onClick={() => {
                          const current = newCampaign.icp_config?.preferred_company_sizes || [];
                          const updated = current.includes(size) 
                            ? current.filter(s => s !== size)
                            : [...current, size];
                          setNewCampaign({
                            ...newCampaign, 
                            icp_config: {...newCampaign.icp_config, preferred_company_sizes: updated}
                          });
                        }}
                        className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
                          (newCampaign.icp_config?.preferred_company_sizes || []).includes(size)
                            ? "bg-cyan-100 border-cyan-500 text-cyan-700"
                            : "border-gray-300 text-gray-600 hover:border-gray-400"
                        }`}
                      >
                        {size} employees
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <Label>Preferred Roles</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {["Owner", "CEO", "Manager", "Director", "VP", "CFO"].map(role => (
                      <button
                        key={role}
                        type="button"
                        onClick={() => {
                          const current = newCampaign.icp_config?.preferred_roles || [];
                          const updated = current.includes(role) 
                            ? current.filter(r => r !== role)
                            : [...current, role];
                          setNewCampaign({
                            ...newCampaign, 
                            icp_config: {...newCampaign.icp_config, preferred_roles: updated}
                          });
                        }}
                        className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
                          (newCampaign.icp_config?.preferred_roles || []).includes(role)
                            ? "bg-cyan-100 border-cyan-500 text-cyan-700"
                            : "border-gray-300 text-gray-600 hover:border-gray-400"
                        }`}
                      >
                        {role}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <Label htmlFor="target-industries">Target Industries (comma-separated)</Label>
                <Input
                  id="target-industries"
                  placeholder="e.g., Restaurant, Retail, Healthcare, Professional Services"
                  value={(newCampaign.icp_config?.target_industries || []).join(", ")}
                  onChange={(e) => {
                    const industries = e.target.value ? e.target.value.split(",").map(i => i.trim()).filter(i => i) : [];
                    setNewCampaign({
                      ...newCampaign,
                      icp_config: {...newCampaign.icp_config, target_industries: industries}
                    });
                  }}
                  className="mt-1"
                />
                <p className="text-xs text-gray-400 mt-1">Leave empty to target all industries</p>
              </div>

              <div className="mt-4">
                <Label htmlFor="min-icp">Minimum ICP Score to Dial</Label>
                <div className="flex items-center gap-3 mt-1">
                  <Input
                    id="min-icp"
                    type="number"
                    min="0"
                    max="100"
                    value={newCampaign.min_icp_score || 0}
                    onChange={(e) => setNewCampaign({...newCampaign, min_icp_score: parseInt(e.target.value) || 0})}
                    className="w-24"
                  />
                  <span className="text-sm text-gray-500">/ 100</span>
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="10"
                      value={newCampaign.min_icp_score || 0}
                      onChange={(e) => setNewCampaign({...newCampaign, min_icp_score: parseInt(e.target.value)})}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                    />
                  </div>
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>0 - Call all leads</span>
                  <span>40 - Skip D-tier</span>
                  <span>60 - Only A/B tier</span>
                  <span>80 - Only A-tier</span>
                </div>
              </div>
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

      {/* Follow-Up Settings Modal */}
      <Dialog open={!!showFollowUpSettings} onOpenChange={() => setShowFollowUpSettings(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              <RefreshCw className="w-5 h-5 text-cyan-500" />
              Follow-Up Settings
            </DialogTitle>
            <DialogDescription>
              Configure automatic follow-up calls for "{showFollowUpSettings?.name}"
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Master Toggle */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <Label className="text-base font-medium">Enable Auto Follow-Ups</Label>
                <p className="text-sm text-gray-500">Automatically schedule retry calls</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={followUpSettings.enabled}
                  onChange={(e) => setFollowUpSettings({...followUpSettings, enabled: e.target.checked})}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-cyan-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500"></div>
              </label>
            </div>

            {followUpSettings.enabled && (
              <>
                {/* No-Answer Retry Settings */}
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <PhoneOff className="w-4 h-4 text-orange-500" />
                      <Label className="font-medium">No-Answer Retries</Label>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={followUpSettings.no_answer_retry_enabled}
                        onChange={(e) => setFollowUpSettings({...followUpSettings, no_answer_retry_enabled: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-orange-500"></div>
                    </label>
                  </div>

                  {followUpSettings.no_answer_retry_enabled && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-sm text-gray-600">Max Retries</Label>
                        <Select
                          value={String(followUpSettings.no_answer_retry_count)}
                          onValueChange={(v) => setFollowUpSettings({...followUpSettings, no_answer_retry_count: parseInt(v)})}
                        >
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="1">1 retry</SelectItem>
                            <SelectItem value="2">2 retries</SelectItem>
                            <SelectItem value="3">3 retries</SelectItem>
                            <SelectItem value="5">5 retries</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-sm text-gray-600">Delay Between</Label>
                        <Select
                          value={String(followUpSettings.no_answer_retry_delay_hours)}
                          onValueChange={(v) => setFollowUpSettings({...followUpSettings, no_answer_retry_delay_hours: parseInt(v)})}
                        >
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="4">4 hours</SelectItem>
                            <SelectItem value="12">12 hours</SelectItem>
                            <SelectItem value="24">24 hours</SelectItem>
                            <SelectItem value="48">48 hours</SelectItem>
                            <SelectItem value="72">72 hours</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  )}
                </div>

                {/* Voicemail Follow-Up Settings */}
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-blue-500" />
                      <Label className="font-medium">Voicemail Follow-Up</Label>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={followUpSettings.voicemail_followup_enabled}
                        onChange={(e) => setFollowUpSettings({...followUpSettings, voicemail_followup_enabled: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-500"></div>
                    </label>
                  </div>

                  {followUpSettings.voicemail_followup_enabled && (
                    <div>
                      <Label className="text-sm text-gray-600">Follow up after voicemail</Label>
                      <Select
                        value={String(followUpSettings.voicemail_followup_delay_hours)}
                        onValueChange={(v) => setFollowUpSettings({...followUpSettings, voicemail_followup_delay_hours: parseInt(v)})}
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="24">24 hours</SelectItem>
                          <SelectItem value="48">48 hours (recommended)</SelectItem>
                          <SelectItem value="72">72 hours</SelectItem>
                          <SelectItem value="96">4 days</SelectItem>
                          <SelectItem value="168">1 week</SelectItem>
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-gray-400 mt-2">
                        Give leads time to listen to voicemail before calling back
                      </p>
                    </div>
                  )}
                </div>

                {/* Info Box */}
                <div className="bg-cyan-50 border border-cyan-200 rounded-lg p-4">
                  <p className="text-sm text-cyan-800">
                    <strong>How it works:</strong> When a call ends with no-answer or voicemail, 
                    DialGenix automatically schedules a follow-up call based on these settings. 
                    Follow-ups stop when the lead answers or gets booked.
                  </p>
                </div>
              </>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFollowUpSettings(null)}>Cancel</Button>
            <Button 
              onClick={saveFollowUpSettings}
              className="bg-cyan-600 hover:bg-cyan-700 text-white"
              data-testid="save-followup-settings-btn"
            >
              Save Settings
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
  const [showVoiceClone, setShowVoiceClone] = useState(false);
  const [showVoiceSettings, setShowVoiceSettings] = useState(null); // agent for voice settings
  const [previewingVoice, setPreviewingVoice] = useState(null); // agent id being previewed
  const [playingAudio, setPlayingAudio] = useState(null); // audio element reference

  const [newAgent, setNewAgent] = useState({
    name: "",
    company_name: "",
    email: "",
    phone: "",
    calendly_link: "",
    max_daily_calls: 50,
    use_case: "sales_cold_calling",
    system_prompt: USE_CASE_TEMPLATES.sales_cold_calling.prompt,
    language: "en"
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

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (playingAudio) {
        playingAudio.pause();
        playingAudio.src = "";
      }
    };
  }, [playingAudio]);

  const previewAgentVoice = async (agent) => {
    // If already previewing this agent, stop it
    if (previewingVoice === agent.id && playingAudio) {
      playingAudio.pause();
      setPlayingAudio(null);
      setPreviewingVoice(null);
      return;
    }

    // Stop any currently playing audio
    if (playingAudio) {
      playingAudio.pause();
    }

    setPreviewingVoice(agent.id);
    const voiceId = agent.voice_type === "cloned" ? agent.cloned_voice_id : (agent.preset_voice_id || "21m00Tcm4TlvDq8ikWAM");
    const previewText = `Hi, this is ${agent.name}. I'm your AI sales agent, ready to help you connect with qualified leads and close more deals!`;

    const formData = new FormData();
    formData.append("text", previewText);
    formData.append("voice_id", voiceId);

    try {
      const response = await axios.post(`${API}/voices/preview`, formData);
      const audio = new Audio(response.data.audio);
      
      audio.onended = () => {
        setPlayingAudio(null);
        setPreviewingVoice(null);
      };
      
      audio.onerror = () => {
        toast.error("Failed to play audio");
        setPlayingAudio(null);
        setPreviewingVoice(null);
      };

      setPlayingAudio(audio);
      await audio.play();
      toast.success(`Playing ${agent.name}'s voice...`);
    } catch (error) {
      console.error("Preview failed:", error);
      toast.error("Failed to generate voice preview");
      setPreviewingVoice(null);
    }
  };

  const createAgent = async () => {
    if (!newAgent.name || !newAgent.email || !newAgent.calendly_link) {
      toast.error("Please fill in all required fields");
      return;
    }

    try {
      await axios.post(`${API}/agents`, newAgent);
      toast.success("Agent created!");
      setShowCreate(false);
      setNewAgent({ 
        name: "", 
        email: "", 
        phone: "", 
        calendly_link: "", 
        max_daily_calls: 50,
        use_case: "sales_cold_calling",
        system_prompt: USE_CASE_TEMPLATES.sales_cold_calling.prompt
      });
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
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Agents
          </h1>
          <p className="text-gray-500 mt-1">Manage sales agents and their Calendly links</p>
        </div>
        <div className="flex gap-2">
          <Button 
            data-testid="clone-voice-btn"
            onClick={() => setShowVoiceClone(true)}
            variant="outline"
            className="border-purple-300 text-purple-700 hover:bg-purple-50"
          >
            <Mic className="w-4 h-4 mr-2" />
            Clone Voice
          </Button>
          <Button 
            data-testid="create-agent-btn"
            onClick={() => setShowCreate(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Agent
          </Button>
        </div>
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

                {/* Voice Settings Indicator */}
                <div className="flex items-center gap-2 p-3 bg-purple-50 rounded-lg mb-4">
                  <Volume2 className="w-4 h-4 text-purple-600" />
                  <div className="flex-1">
                    <span className="text-sm text-gray-700">
                      {agent.voice_type === "cloned" ? agent.cloned_voice_name || "Cloned Voice" : "Preset Voice"}
                    </span>
                    {agent.voice_type === "cloned" && (
                      <Badge className="ml-2 bg-purple-100 text-purple-700 text-xs">Custom</Badge>
                    )}
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => previewAgentVoice(agent)}
                    disabled={previewingVoice && previewingVoice !== agent.id}
                    className={`${previewingVoice === agent.id ? 'text-green-600 hover:text-green-700 hover:bg-green-100' : 'text-purple-600 hover:text-purple-700 hover:bg-purple-100'}`}
                    data-testid={`preview-voice-${agent.id}`}
                    title={previewingVoice === agent.id ? "Stop preview" : "Preview voice"}
                  >
                    {previewingVoice === agent.id ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowVoiceSettings(agent)}
                    className="text-purple-600 hover:text-purple-700 hover:bg-purple-100"
                    data-testid={`voice-settings-${agent.id}`}
                  >
                    <Settings className="w-4 h-4" />
                  </Button>
                </div>

                <div className="flex gap-2">
                  <Button
                    className="flex-1"
                    variant="outline"
                    data-testid={`toggle-agent-${agent.id}`}
                    onClick={() => toggleAgent(agent)}
                  >
                    {agent.is_active ? "Deactivate" : "Activate"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Agent Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Create AI Agent
            </DialogTitle>
            <DialogDescription>
              Configure your virtual AI caller — choose a voice, language, and script
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Use Case Selector */}
            <div>
              <Label htmlFor="use-case">Use Case *</Label>
              <select
                id="use-case"
                data-testid="agent-use-case-select"
                value={newAgent.use_case}
                onChange={(e) => {
                  const useCase = e.target.value;
                  const template = USE_CASE_TEMPLATES[useCase];
                  setNewAgent({
                    ...newAgent, 
                    use_case: useCase,
                    system_prompt: template.prompt
                  });
                }}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {Object.entries(USE_CASE_TEMPLATES).map(([key, template]) => (
                  <option key={key} value={key}>{template.label}</option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {USE_CASE_TEMPLATES[newAgent.use_case]?.description}
              </p>
              {USE_CASE_TEMPLATES[newAgent.use_case]?.tips && (
                <p className="text-xs text-blue-600 mt-1 bg-blue-50 px-2 py-1 rounded">
                  💡 {USE_CASE_TEMPLATES[newAgent.use_case]?.tips}
                </p>
              )}
            </div>
            
            <div>
              <Label htmlFor="agent-name">AI Agent Name *</Label>
              <Input
                id="agent-name"
                data-testid="agent-name-input"
                value={newAgent.name}
                onChange={(e) => setNewAgent({...newAgent, name: e.target.value})}
                placeholder="Sarah (Sales Agent)"
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">What your AI will call itself on calls</p>
            </div>

            <div>
              <Label htmlFor="company-name">Company Name *</Label>
              <Input
                id="company-name"
                data-testid="agent-company-input"
                value={newAgent.company_name}
                onChange={(e) => setNewAgent({...newAgent, company_name: e.target.value})}
                placeholder="DialGenix"
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">Company the AI represents (replaces {'{company}'} in script)</p>
            </div>
            
            <div>
              <Label htmlFor="agent-email">Notification Email *</Label>
              <Input
                id="agent-email"
                data-testid="agent-email-input"
                type="email"
                value={newAgent.email}
                onChange={(e) => setNewAgent({...newAgent, email: e.target.value})}
                placeholder="alerts@yourcompany.com"
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">Receive alerts when this agent qualifies leads</p>
            </div>
            
            <div>
              <Label htmlFor="agent-phone">Outbound Phone Number</Label>
              <Input
                id="agent-phone"
                data-testid="agent-phone-input"
                value={newAgent.phone}
                onChange={(e) => setNewAgent({...newAgent, phone: e.target.value})}
                placeholder="+14155551234 (your Twilio number)"
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">Twilio number the AI calls FROM (leave blank to use default)</p>
            </div>
            
            <div>
              <Label htmlFor="calendly-link">Meeting Booking Link *</Label>
              <Input
                id="calendly-link"
                data-testid="agent-calendly-input"
                value={newAgent.calendly_link}
                onChange={(e) => setNewAgent({...newAgent, calendly_link: e.target.value})}
                placeholder="https://calendly.com/your-name/30min"
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">Where qualified leads can book meetings</p>
            </div>

            {/* Language Selection */}
            <div>
              <Label htmlFor="language" className="flex items-center gap-2">
                Language
                <span className="text-xs text-gray-400 font-normal">(AI will speak in this language)</span>
              </Label>
              <select
                id="language"
                value={newAgent.language}
                onChange={(e) => setNewAgent({...newAgent, language: e.target.value})}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.flag} {lang.name}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">Supports 50+ languages via ElevenLabs multilingual model</p>
            </div>
            
            {/* System Prompt (Advanced) */}
            <div>
              <Label htmlFor="system-prompt" className="flex items-center gap-2">
                AI Script 
                <span className="text-xs text-gray-400 font-normal">(customize if needed)</span>
              </Label>
              
              {/* Pro Tips Box */}
              <div className="mt-2 mb-3 bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-sm font-medium text-amber-900 mb-2 flex items-center gap-1">
                  <Zap className="w-4 h-4" /> Script Best Practices
                </p>
                <ul className="text-xs text-amber-800 space-y-1">
                  <li>✓ <strong>Always qualify first:</strong> "Am I speaking with the owner or manager?"</li>
                  <li>✓ <strong>Keep it short:</strong> 1-2 sentences per response max</li>
                  <li>✓ <strong>Use {'{contact_name}'}</strong> if Apollo is connected for personalization</li>
                  <li>✓ <strong>Add pauses:</strong> Use "..." for natural breathing room</li>
                </ul>
              </div>

              <textarea
                id="system-prompt"
                data-testid="agent-prompt-input"
                value={newAgent.system_prompt}
                onChange={(e) => setNewAgent({...newAgent, system_prompt: e.target.value})}
                placeholder="Enter custom AI instructions..."
                rows={12}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono resize-y min-h-[200px]"
              />
              <p className="text-xs text-gray-400 mt-1">
                Variables: <code className="bg-gray-100 px-1 rounded">{'{agent_name}'}</code> = AI's name, 
                <code className="bg-gray-100 px-1 rounded ml-1">{'{company}'}</code> = company name, 
                <code className="bg-gray-100 px-1 rounded ml-1">{'{contact_name}'}</code> = lead's name (if available)
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button 
              data-testid="save-agent-btn"
              onClick={createAgent}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Create AI Agent
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Voice Clone Modal */}
      <VoiceCloneModal
        isOpen={showVoiceClone}
        onClose={() => setShowVoiceClone(false)}
        onVoiceCloned={(voice) => {
          toast.success(`Voice "${voice.name}" cloned successfully!`);
          setShowVoiceClone(false);
        }}
      />

      {/* Voice Settings Modal */}
      {showVoiceSettings && (
        <VoiceSettingsModal
          isOpen={!!showVoiceSettings}
          onClose={() => setShowVoiceSettings(null)}
          agent={showVoiceSettings}
          onSave={() => {
            fetchAgents();
            setShowVoiceSettings(null);
          }}
        />
      )}
    </div>
  );
};

// Call History Page
const CallHistory = () => {
  const { token } = useAuth();
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCall, setSelectedCall] = useState(null);
  const [subscriptionFeatures, setSubscriptionFeatures] = useState(null);
  const [playingAudio, setPlayingAudio] = useState(null);
  const [loadingTranscript, setLoadingTranscript] = useState(false);
  const [transcriptData, setTranscriptData] = useState(null);

  const fetchCalls = async () => {
    try {
      const [callsRes, featuresRes] = await Promise.all([
        axios.get(`${API}/calls`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/subscription/features`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setCalls(callsRes.data);
      setSubscriptionFeatures(featuresRes.data.features);
    } catch (error) {
      toast.error("Failed to load calls");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, [token]);

  const playRecording = async (call) => {
    if (!subscriptionFeatures?.call_recording) {
      toast.error("Call recording requires Starter plan or higher");
      return;
    }
    
    if (!call.recording_url) {
      toast.error("No recording available for this call");
      return;
    }

    try {
      // Get audio stream
      const response = await axios.get(
        `${API}/calls/${call.id}/recording/stream`,
        { 
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      
      const audioUrl = URL.createObjectURL(response.data);
      const audio = new Audio(audioUrl);
      
      // Stop any currently playing audio
      if (playingAudio) {
        playingAudio.pause();
      }
      
      setPlayingAudio(audio);
      audio.play();
      
      audio.onended = () => {
        setPlayingAudio(null);
        URL.revokeObjectURL(audioUrl);
      };
      
      toast.success("Playing recording...");
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Recording access requires a higher subscription tier");
      } else {
        toast.error("Failed to play recording");
      }
    }
  };

  const stopRecording = () => {
    if (playingAudio) {
      playingAudio.pause();
      setPlayingAudio(null);
    }
  };

  const loadTranscript = async (call) => {
    if (!subscriptionFeatures?.call_transcription) {
      toast.error("Transcription requires Professional plan or higher");
      return;
    }

    setLoadingTranscript(true);
    try {
      const response = await axios.get(
        `${API}/calls/${call.id}/transcript`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTranscriptData(response.data);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Transcription requires Professional plan or higher");
      } else if (error.response?.status === 404) {
        toast.info("No transcript available. Request one below.");
      } else {
        toast.error("Failed to load transcript");
      }
    } finally {
      setLoadingTranscript(false);
    }
  };

  const requestTranscription = async (call) => {
    try {
      await axios.post(
        `${API}/calls/${call.id}/transcribe`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Transcription requested! Check back in a minute.");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to request transcription");
    }
  };

  const openCallDetails = async (call) => {
    setSelectedCall(call);
    setTranscriptData(null);
    
    // Auto-load transcript if user has access and call has one
    if (subscriptionFeatures?.call_transcription && call.full_transcript) {
      loadTranscript(call);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="call-history-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Call History
          </h1>
          <p className="text-gray-500 mt-1">View recordings, transcripts, and qualification results</p>
        </div>
        
        {/* Feature badges */}
        <div className="flex items-center gap-2">
          {subscriptionFeatures?.call_recording ? (
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
              <CheckCircle className="w-3 h-3 mr-1" /> Recordings
            </Badge>
          ) : (
            <Badge variant="outline" className="bg-gray-50 text-gray-500">
              Recordings (Starter+)
            </Badge>
          )}
          {subscriptionFeatures?.call_transcription ? (
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
              <CheckCircle className="w-3 h-3 mr-1" /> Transcripts
            </Badge>
          ) : (
            <Badge variant="outline" className="bg-gray-50 text-gray-500">
              Transcripts (Pro+)
            </Badge>
          )}
        </div>
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
                  <TableHead>Recording</TableHead>
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
                      {call.recording_url ? (
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8 w-8 p-0"
                            onClick={() => playingAudio ? stopRecording() : playRecording(call)}
                            disabled={!subscriptionFeatures?.call_recording}
                          >
                            {playingAudio ? (
                              <Pause className="w-4 h-4 text-blue-600" />
                            ) : (
                              <Play className="w-4 h-4 text-blue-600" />
                            )}
                          </Button>
                          {call.full_transcript && (
                            <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700">
                              Transcript
                            </Badge>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">-</span>
                      )}
                    </TableCell>
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
                        onClick={() => openCallDetails(call)}
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

      {/* Call Details Dialog - Enhanced with Recording & Transcript */}
      <Dialog open={!!selectedCall} onOpenChange={() => { setSelectedCall(null); setTranscriptData(null); stopRecording(); }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Call Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedCall && (
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Status</p>
                  <StatusBadge status={selectedCall.status} />
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Duration</p>
                  <p className="font-semibold">{selectedCall.duration_seconds}s</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Answered By</p>
                  <p className="font-semibold capitalize">{selectedCall.answered_by || "Unknown"}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Date</p>
                  <p className="font-semibold">{new Date(selectedCall.created_at).toLocaleString()}</p>
                </div>
              </div>

              {/* Recording Player */}
              {selectedCall.recording_url && subscriptionFeatures?.call_recording && (
                <div className="p-4 border border-blue-200 rounded-lg bg-blue-50/50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-100 rounded-full">
                        <Phone className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">Call Recording</p>
                        <p className="text-sm text-gray-500">
                          {selectedCall.recording_duration_seconds || selectedCall.duration_seconds}s duration
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={() => playingAudio ? stopRecording() : playRecording(selectedCall)}
                      className="gap-2"
                    >
                      {playingAudio ? (
                        <>
                          <Pause className="w-4 h-4" /> Stop
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4" /> Play Recording
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )}

              {/* Qualification Result */}
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

              {/* Full Transcript (Whisper) */}
              {subscriptionFeatures?.call_transcription && (
                <div className="border border-purple-200 rounded-lg overflow-hidden">
                  <div className="p-4 bg-purple-50 border-b border-purple-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-purple-900">Full Transcript</h4>
                        {selectedCall.transcription_status === "processing" && (
                          <Badge className="bg-yellow-100 text-yellow-800">Processing...</Badge>
                        )}
                      </div>
                      {!transcriptData && !loadingTranscript && (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => loadTranscript(selectedCall)}
                            disabled={!selectedCall.full_transcript}
                          >
                            Load Transcript
                          </Button>
                          {!selectedCall.full_transcript && selectedCall.recording_url && (
                            <Button
                              size="sm"
                              onClick={() => requestTranscription(selectedCall)}
                            >
                              Request Transcription
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="p-4 bg-white">
                    {loadingTranscript ? (
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-4 w-5/6" />
                      </div>
                    ) : transcriptData ? (
                      <div className="space-y-4">
                        {/* Full text */}
                        <div className="p-3 bg-gray-50 rounded-lg">
                          <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                            {transcriptData.full_transcript}
                          </p>
                        </div>
                        
                        {/* Timestamped segments */}
                        {transcriptData.segments && transcriptData.segments.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 mb-2">Timestamped Segments</p>
                            <ScrollArea className="h-[150px] border rounded-lg p-2">
                              <div className="space-y-2">
                                {transcriptData.segments.map((segment, idx) => (
                                  <div key={idx} className="flex gap-3 text-sm">
                                    <span className="text-gray-400 font-mono w-20 flex-shrink-0">
                                      {Math.floor(segment.start / 60)}:{String(Math.floor(segment.start % 60)).padStart(2, '0')}
                                    </span>
                                    <span className="text-gray-700">{segment.text}</span>
                                  </div>
                                ))}
                              </div>
                            </ScrollArea>
                          </div>
                        )}
                      </div>
                    ) : selectedCall.full_transcript ? (
                      <p className="text-sm text-gray-500">Click "Load Transcript" to view.</p>
                    ) : (
                      <p className="text-sm text-gray-500">
                        No transcript available. 
                        {selectedCall.recording_url ? " Click 'Request Transcription' to generate one." : " No recording found."}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* AI Conversation Transcript (existing) */}
              {selectedCall.transcript && selectedCall.transcript.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-3">AI Conversation Log</h4>
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
  
  // Team management state
  const [teamMembers, setTeamMembers] = useState([]);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [loadingTeam, setLoadingTeam] = useState(false);
  
  // Number Pool state
  const [numberPool, setNumberPool] = useState([]);
  const [showAddNumber, setShowAddNumber] = useState(false);
  const [newNumber, setNewNumber] = useState("");
  const [rotationMode, setRotationMode] = useState("round-robin");
  const [numberPoolEnabled, setNumberPoolEnabled] = useState(false);
  
  // Integration setup modals
  const [showTwilioSetup, setShowTwilioSetup] = useState(false);
  const [showTwitterSetup, setShowTwitterSetup] = useState(false);
  const [showEmailSetup, setShowEmailSetup] = useState(false);
  const [showCalendlySetup, setShowCalendlySetup] = useState(false);
  
  // Integration form states
  const [twilioForm, setTwilioForm] = useState({
    account_sid: "",
    auth_token: "",
    phone_number: ""
  });
  const [twitterForm, setTwitterForm] = useState({
    api_key: "",
    api_secret: "",
    bearer_token: ""
  });
  const [emailForm, setEmailForm] = useState({
    resend_api_key: "",
    from_email: ""
  });
  const [calendlyForm, setCalendlyForm] = useState({
    calendly_url: ""
  });
  const [apolloForm, setApolloForm] = useState({
    api_key: ""
  });
  
  // Additional modal states
  const [showApolloSetup, setShowApolloSetup] = useState(false);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
      // Load number pool settings
      if (response.data.number_pool) {
        setNumberPool(response.data.number_pool || []);
        setRotationMode(response.data.rotation_mode || "round-robin");
        setNumberPoolEnabled(response.data.number_pool_enabled || false);
      }
      // Load integration settings into forms
      if (response.data.twilio_account_sid) {
        setTwilioForm({
          account_sid: response.data.twilio_account_sid || "",
          auth_token: response.data.twilio_auth_token ? "••••••••" : "",
          phone_number: response.data.twilio_phone_number || ""
        });
      }
      if (response.data.twitter_api_key) {
        setTwitterForm({
          api_key: response.data.twitter_api_key ? "••••••••" : "",
          api_secret: response.data.twitter_api_secret ? "••••••••" : "",
          bearer_token: response.data.twitter_bearer_token ? "••••••••" : ""
        });
      }
      if (response.data.resend_api_key) {
        setEmailForm({
          resend_api_key: response.data.resend_api_key ? "••••••••" : "",
          from_email: response.data.from_email || ""
        });
      }
      if (response.data.calendly_url) {
        setCalendlyForm({
          calendly_url: response.data.calendly_url || ""
        });
      }
      if (response.data.apollo_api_key) {
        setApolloForm({
          api_key: response.data.apollo_api_key ? "••••••••" : ""
        });
      }
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

  const fetchTeamMembers = async () => {
    setLoadingTeam(true);
    try {
      const response = await axios.get(`${API}/team/members`);
      setTeamMembers(response.data);
    } catch (error) {
      console.error("Failed to fetch team members:", error);
    } finally {
      setLoadingTeam(false);
    }
  };

  const inviteTeamMember = async () => {
    if (!inviteEmail) {
      toast.error("Please enter an email address");
      return;
    }
    try {
      await axios.post(`${API}/team/invite`, {
        email: inviteEmail,
        role: inviteRole
      });
      toast.success(`Invitation sent to ${inviteEmail}`);
      setShowInviteModal(false);
      setInviteEmail("");
      fetchTeamMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send invitation");
    }
  };

  const removeTeamMember = async (memberId) => {
    if (!confirm("Are you sure you want to remove this team member?")) return;
    try {
      await axios.delete(`${API}/team/members/${memberId}`);
      toast.success("Team member removed");
      fetchTeamMembers();
    } catch (error) {
      toast.error("Failed to remove team member");
    }
  };

  const updateMemberRole = async (memberId, newRole) => {
    try {
      await axios.put(`${API}/team/members/${memberId}`, { role: newRole });
      toast.success("Role updated");
      fetchTeamMembers();
    } catch (error) {
      toast.error("Failed to update role");
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchWebhooks();
    fetchTeamMembers();
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
            {/* Twilio Voice */}
            <div 
              onClick={() => setShowTwilioSetup(true)}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Phone className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium">Twilio Voice</p>
                  <p className="text-sm text-gray-500">For making real phone calls</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={settings?.twilio_configured ? "default" : "secondary"}>
                  {settings?.twilio_configured ? "Connected" : "Not Connected"}
                </Badge>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
              </div>
            </div>
            
            {/* Twitter/X API */}
            <div 
              onClick={() => setShowTwitterSetup(true)}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <Search className="w-5 h-5 text-gray-600" />
                </div>
                <div>
                  <p className="font-medium">Twitter/X API</p>
                  <p className="text-sm text-gray-500">For intent monitoring</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={settings?.twitter_configured ? "default" : "secondary"}>
                  {settings?.twitter_configured ? "Connected" : "Not Connected"}
                </Badge>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
              </div>
            </div>
            
            {/* Email Notifications */}
            <div 
              onClick={() => setShowEmailSetup(true)}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Mail className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="font-medium">Email Notifications</p>
                  <p className="text-sm text-gray-500">Via Resend API</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={settings?.email_notifications_configured ? "default" : "secondary"}>
                  {settings?.email_notifications_configured ? "Connected" : "Not Connected"}
                </Badge>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
              </div>
            </div>
            
            {/* Calendly */}
            <div 
              onClick={() => setShowCalendlySetup(true)}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium">Calendly</p>
                  <p className="text-sm text-gray-500">For booking meetings</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={settings?.calendly_url ? "default" : "secondary"}>
                  {settings?.calendly_url ? "Connected" : "Not Connected"}
                </Badge>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
              </div>
            </div>

            {/* Apollo.io Lead Enrichment */}
            <div 
              onClick={() => setShowApolloSetup(true)}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <Database className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <p className="font-medium">Apollo.io</p>
                  <p className="text-sm text-gray-500">Lead enrichment & contact names</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={settings?.apollo_configured ? "default" : "secondary"}>
                  {settings?.apollo_configured ? "Connected" : "Not Connected"}
                </Badge>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Twilio Setup Modal */}
        {showTwilioSetup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-lg mx-4">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Phone className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <CardTitle>Connect Twilio Voice</CardTitle>
                    <CardDescription>Required for making real phone calls</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-blue-900 mb-2">How to get your Twilio credentials:</p>
                  <ol className="text-blue-800 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://console.twilio.com" target="_blank" rel="noopener noreferrer" className="underline">console.twilio.com</a></li>
                    <li>Copy your Account SID and Auth Token from the dashboard</li>
                    <li>Buy a phone number from Phone Numbers → Buy a Number</li>
                  </ol>
                </div>
                
                <div>
                  <Label htmlFor="twilio_sid">Account SID</Label>
                  <Input
                    id="twilio_sid"
                    placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    value={twilioForm.account_sid}
                    onChange={(e) => setTwilioForm({...twilioForm, account_sid: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
                
                <div>
                  <Label htmlFor="twilio_token">Auth Token</Label>
                  <Input
                    id="twilio_token"
                    type="password"
                    placeholder="Enter your auth token"
                    value={twilioForm.auth_token}
                    onChange={(e) => setTwilioForm({...twilioForm, auth_token: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
                
                <div>
                  <Label htmlFor="twilio_phone">Phone Number</Label>
                  <Input
                    id="twilio_phone"
                    placeholder="+14155551234"
                    value={twilioForm.phone_number}
                    onChange={(e) => setTwilioForm({...twilioForm, phone_number: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">Your Twilio phone number in E.164 format</p>
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button variant="outline" onClick={() => setShowTwilioSetup(false)} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    if (!twilioForm.account_sid || !twilioForm.auth_token || !twilioForm.phone_number) {
                      toast.error("Please fill in all fields");
                      return;
                    }
                    try {
                      await updateSettings({
                        twilio_account_sid: twilioForm.account_sid,
                        twilio_auth_token: twilioForm.auth_token,
                        twilio_phone_number: twilioForm.phone_number,
                        twilio_configured: true
                      });
                      setShowTwilioSetup(false);
                      toast.success("Twilio connected successfully!");
                    } catch (error) {
                      toast.error("Failed to save Twilio settings");
                    }
                  }}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  Connect Twilio
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Twitter Setup Modal */}
        {showTwitterSetup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-lg mx-4">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Search className="w-5 h-5 text-gray-600" />
                  </div>
                  <div>
                    <CardTitle>Connect Twitter/X API</CardTitle>
                    <CardDescription>For monitoring buyer intent signals</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-gray-900 mb-2">How to get your X API credentials:</p>
                  <ol className="text-gray-700 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://developer.twitter.com" target="_blank" rel="noopener noreferrer" className="underline text-blue-600">developer.twitter.com</a></li>
                    <li>Create a project and app</li>
                    <li>Generate API keys and Bearer Token</li>
                  </ol>
                </div>
                
                <div>
                  <Label htmlFor="twitter_key">API Key</Label>
                  <Input
                    id="twitter_key"
                    type="password"
                    placeholder="Enter your API key"
                    value={twitterForm.api_key}
                    onChange={(e) => setTwitterForm({...twitterForm, api_key: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
                
                <div>
                  <Label htmlFor="twitter_secret">API Secret</Label>
                  <Input
                    id="twitter_secret"
                    type="password"
                    placeholder="Enter your API secret"
                    value={twitterForm.api_secret}
                    onChange={(e) => setTwitterForm({...twitterForm, api_secret: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
                
                <div>
                  <Label htmlFor="twitter_bearer">Bearer Token</Label>
                  <Input
                    id="twitter_bearer"
                    type="password"
                    placeholder="Enter your bearer token"
                    value={twitterForm.bearer_token}
                    onChange={(e) => setTwitterForm({...twitterForm, bearer_token: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button variant="outline" onClick={() => setShowTwitterSetup(false)} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    if (!twitterForm.api_key || !twitterForm.api_secret) {
                      toast.error("Please fill in API key and secret");
                      return;
                    }
                    try {
                      await updateSettings({
                        twitter_api_key: twitterForm.api_key,
                        twitter_api_secret: twitterForm.api_secret,
                        twitter_bearer_token: twitterForm.bearer_token,
                        twitter_configured: true
                      });
                      setShowTwitterSetup(false);
                      toast.success("Twitter/X connected successfully!");
                    } catch (error) {
                      toast.error("Failed to save Twitter settings");
                    }
                  }}
                  className="flex-1 bg-gray-900 hover:bg-gray-800"
                >
                  Connect Twitter/X
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Email Setup Modal */}
        {showEmailSetup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-lg mx-4">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <Mail className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <CardTitle>Connect Email Notifications</CardTitle>
                    <CardDescription>Get notified when leads are qualified</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-purple-900 mb-2">How to get your Resend API key:</p>
                  <ol className="text-purple-800 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://resend.com" target="_blank" rel="noopener noreferrer" className="underline">resend.com</a> and create an account</li>
                    <li>Verify your domain (or use their test domain)</li>
                    <li>Go to API Keys → Create API Key</li>
                  </ol>
                </div>
                
                <div>
                  <Label htmlFor="resend_key">Resend API Key</Label>
                  <Input
                    id="resend_key"
                    type="password"
                    placeholder="re_xxxxxxxxxxxxxxxxxxxxxxxxx"
                    value={emailForm.resend_api_key}
                    onChange={(e) => setEmailForm({...emailForm, resend_api_key: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
                
                <div>
                  <Label htmlFor="from_email">From Email Address</Label>
                  <Input
                    id="from_email"
                    type="email"
                    placeholder="notifications@yourdomain.com"
                    value={emailForm.from_email}
                    onChange={(e) => setEmailForm({...emailForm, from_email: e.target.value})}
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">Must be from a verified domain in Resend</p>
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button variant="outline" onClick={() => setShowEmailSetup(false)} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    if (!emailForm.resend_api_key) {
                      toast.error("Please enter your Resend API key");
                      return;
                    }
                    try {
                      await updateSettings({
                        resend_api_key: emailForm.resend_api_key,
                        from_email: emailForm.from_email,
                        email_notifications_configured: true
                      });
                      setShowEmailSetup(false);
                      toast.success("Email notifications connected!");
                    } catch (error) {
                      toast.error("Failed to save email settings");
                    }
                  }}
                  className="flex-1 bg-purple-600 hover:bg-purple-700"
                >
                  Connect Email
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Calendly Setup Modal */}
        {showCalendlySetup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-lg mx-4">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <CardTitle>Connect Calendly</CardTitle>
                    <CardDescription>Let AI book meetings on your calendar</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-green-900 mb-2">How to get your Calendly link:</p>
                  <ol className="text-green-800 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://calendly.com" target="_blank" rel="noopener noreferrer" className="underline">calendly.com</a></li>
                    <li>Create an event type (e.g., "15 Min Discovery Call")</li>
                    <li>Copy the scheduling link</li>
                  </ol>
                </div>
                
                <div>
                  <Label htmlFor="calendly_url">Calendly Scheduling Link</Label>
                  <Input
                    id="calendly_url"
                    placeholder="https://calendly.com/yourname/15min"
                    value={calendlyForm.calendly_url}
                    onChange={(e) => setCalendlyForm({...calendlyForm, calendly_url: e.target.value})}
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">The AI will direct qualified leads to book here</p>
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <p className="text-sm text-amber-800">
                    <strong>Tip:</strong> You can also set different Calendly links per agent in the agent settings.
                  </p>
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button variant="outline" onClick={() => setShowCalendlySetup(false)} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    if (!calendlyForm.calendly_url) {
                      toast.error("Please enter your Calendly link");
                      return;
                    }
                    try {
                      await updateSettings({
                        calendly_url: calendlyForm.calendly_url
                      });
                      setShowCalendlySetup(false);
                      toast.success("Calendly connected!");
                    } catch (error) {
                      toast.error("Failed to save Calendly settings");
                    }
                  }}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  Connect Calendly
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Apollo.io Setup Modal */}
        {showApolloSetup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                    <Database className="w-5 h-5 text-orange-600" />
                  </div>
                  <div>
                    <CardTitle>Connect Apollo.io</CardTitle>
                    <CardDescription>Enrich leads with owner/manager contact names</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Benefits */}
                <div className="bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-200 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-500" />
                    Why Connect Apollo?
                  </h4>
                  <ul className="text-sm text-orange-800 space-y-1">
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span><strong>Get contact names</strong> — Know who you're calling before dialing</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span><strong>Identify decision makers</strong> — Owner, Manager, CEO titles</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span><strong>Better personalization</strong> — "Hi John, this is Sarah..."</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span><strong>Higher conversion</strong> — 40% better response with names</span>
                    </li>
                  </ul>
                </div>

                {/* Pricing Info */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-blue-900 mb-2">Apollo.io Pricing:</p>
                  <ul className="text-blue-800 space-y-1">
                    <li>• <strong>Free tier:</strong> 100 credits/month (enough to test)</li>
                    <li>• <strong>Basic:</strong> $49/mo for 5,000 credits</li>
                    <li>• <strong>Professional:</strong> $99/mo for unlimited</li>
                  </ul>
                  <p className="mt-2 text-blue-700">1 credit = 1 lead enriched with contact info</p>
                </div>
                
                {/* Setup Instructions */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-gray-900 mb-2">How to get your Apollo API key:</p>
                  <ol className="text-gray-700 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://app.apollo.io" target="_blank" rel="noopener noreferrer" className="underline text-blue-600">app.apollo.io</a> (create free account)</li>
                    <li>Click Settings (gear icon) → Integrations</li>
                    <li>Find "API Keys" section → Create new key</li>
                    <li>Copy and paste the key below</li>
                  </ol>
                </div>
                
                <div>
                  <Label htmlFor="apollo_key">Apollo API Key</Label>
                  <Input
                    id="apollo_key"
                    type="password"
                    placeholder="Enter your Apollo API key"
                    value={apolloForm.api_key}
                    onChange={(e) => setApolloForm({...apolloForm, api_key: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>

                {/* What Happens Next */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <p className="text-sm text-green-800">
                    <strong>Once connected:</strong> When you discover or import leads, we'll automatically fetch contact names and titles. Your AI will then personalize calls: "Hi [Name], am I speaking with the owner?"
                  </p>
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button variant="outline" onClick={() => setShowApolloSetup(false)} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    if (!apolloForm.api_key || apolloForm.api_key === "••••••••") {
                      toast.error("Please enter your Apollo API key");
                      return;
                    }
                    try {
                      await updateSettings({
                        apollo_api_key: apolloForm.api_key,
                        apollo_configured: true
                      });
                      setShowApolloSetup(false);
                      toast.success("Apollo.io connected! Leads will now be enriched with contact names.");
                    } catch (error) {
                      toast.error("Failed to save Apollo settings");
                    }
                  }}
                  className="flex-1 bg-orange-600 hover:bg-orange-700"
                >
                  Connect Apollo
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Number Pool / Caller ID Rotation Card */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }} className="flex items-center gap-2">
                  <RefreshCw className="w-5 h-5 text-blue-600" />
                  Caller ID Rotation
                </CardTitle>
                <CardDescription>Rotate through multiple numbers for higher answer rates</CardDescription>
              </div>
              <Badge variant={numberPoolEnabled && numberPool.length >= 2 ? "default" : "secondary"}>
                {numberPoolEnabled && numberPool.length >= 2 ? `${numberPool.length} Numbers Active` : "Not Active"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Benefits Section */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-4">
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                Why Use Number Rotation?
              </h4>
              <div className="grid md:grid-cols-2 gap-3 text-sm">
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span><strong>+30-40% answer rates</strong> with local presence</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span><strong>Avoid spam flags</strong> by spreading calls</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span><strong>Professional appearance</strong> like a real team</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span><strong>No easy callbacks</strong> — numbers rotate</span>
                </div>
              </div>
            </div>

            {/* Setup Instructions */}
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <h4 className="font-semibold text-gray-900 mb-3">How to Set Up:</h4>
              <ol className="space-y-2 text-sm text-gray-700">
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">1</span>
                  <span><strong>Buy Twilio numbers</strong> — Go to <a href="https://console.twilio.com/us1/develop/phone-numbers/manage/incoming" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Twilio Console</a> → Phone Numbers → Buy a Number (~$1-2/month each)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">2</span>
                  <span><strong>Add 5-10 numbers</strong> — Mix of local area codes matching your target regions</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">3</span>
                  <span><strong>Paste numbers below</strong> — Format: +1XXXXXXXXXX (include country code)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">4</span>
                  <span><strong>Choose rotation mode</strong> — Round-robin (sequential), Random, or Geographic</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">5</span>
                  <span><strong>Enable rotation</strong> — Toggle on and your campaigns will auto-rotate</span>
                </li>
              </ol>
            </div>

            {/* Enable Toggle */}
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-white">
              <div>
                <p className="font-medium">Enable Number Rotation</p>
                <p className="text-sm text-gray-500">Requires at least 2 numbers in pool</p>
              </div>
              <Button
                variant={numberPoolEnabled ? "default" : "outline"}
                onClick={() => {
                  if (numberPool.length < 2 && !numberPoolEnabled) {
                    toast.error("Add at least 2 numbers to enable rotation");
                    return;
                  }
                  const newValue = !numberPoolEnabled;
                  setNumberPoolEnabled(newValue);
                  updateSettings({ number_pool_enabled: newValue });
                }}
                disabled={numberPool.length < 2}
              >
                {numberPoolEnabled ? "Enabled" : "Disabled"}
              </Button>
            </div>

            {/* Rotation Mode Selector */}
            <div>
              <Label className="mb-2 block">Rotation Mode</Label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: "round-robin", label: "Round Robin", desc: "Sequential order" },
                  { value: "random", label: "Random", desc: "Randomized each call" },
                  { value: "geographic", label: "Geographic", desc: "Match lead area code" }
                ].map((mode) => (
                  <button
                    key={mode.value}
                    onClick={() => {
                      setRotationMode(mode.value);
                      updateSettings({ rotation_mode: mode.value });
                    }}
                    className={`p-3 rounded-lg border-2 text-center transition-all ${
                      rotationMode === mode.value
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:border-blue-300"
                    }`}
                  >
                    <p className={`font-medium text-sm ${rotationMode === mode.value ? "text-blue-700" : "text-gray-700"}`}>
                      {mode.label}
                    </p>
                    <p className="text-xs text-gray-500">{mode.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Number Pool List */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label>Your Number Pool ({numberPool.length} numbers)</Label>
                <Button
                  size="sm"
                  onClick={() => setShowAddNumber(true)}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Number
                </Button>
              </div>

              {numberPool.length === 0 ? (
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Phone className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 mb-2">No numbers in pool yet</p>
                  <p className="text-sm text-gray-400">Add Twilio numbers to start rotating caller IDs</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {numberPool.map((number, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-700">{index + 1}</span>
                        </div>
                        <div>
                          <p className="font-mono font-medium text-gray-900">{number}</p>
                          <p className="text-xs text-gray-500">
                            Area code: {number.slice(2, 5)}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const updated = numberPool.filter((_, i) => i !== index);
                          setNumberPool(updated);
                          updateSettings({ number_pool: updated });
                          toast.success("Number removed");
                        }}
                        className="text-red-500 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Add Number Modal */}
            {showAddNumber && (
              <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <Card className="w-full max-w-md mx-4">
                  <CardHeader>
                    <CardTitle>Add Twilio Number</CardTitle>
                    <CardDescription>Enter a phone number from your Twilio account</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="newNumber">Phone Number</Label>
                      <Input
                        id="newNumber"
                        placeholder="+14155551234"
                        value={newNumber}
                        onChange={(e) => setNewNumber(e.target.value)}
                        className="mt-1 font-mono"
                      />
                      <p className="text-xs text-gray-500 mt-1">Format: +1XXXXXXXXXX (include country code)</p>
                    </div>
                    
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                      <p className="text-sm text-amber-800">
                        <strong>Important:</strong> This number must be purchased in your Twilio account and configured for voice calls.
                      </p>
                    </div>
                  </CardContent>
                  <div className="flex gap-2 p-6 pt-0">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowAddNumber(false);
                        setNewNumber("");
                      }}
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={() => {
                        // Validate phone number format
                        const phoneRegex = /^\+1[0-9]{10}$/;
                        if (!phoneRegex.test(newNumber)) {
                          toast.error("Invalid format. Use +1XXXXXXXXXX");
                          return;
                        }
                        if (numberPool.includes(newNumber)) {
                          toast.error("This number is already in your pool");
                          return;
                        }
                        const updated = [...numberPool, newNumber];
                        setNumberPool(updated);
                        updateSettings({ number_pool: updated });
                        setShowAddNumber(false);
                        setNewNumber("");
                        toast.success("Number added to pool!");
                      }}
                      className="flex-1 bg-blue-600 hover:bg-blue-700"
                    >
                      Add Number
                    </Button>
                  </div>
                </Card>
              </div>
            )}

            {/* Pricing Note */}
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4">
              <h4 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
                <CreditCard className="w-4 h-4" />
                Cost Breakdown
              </h4>
              <div className="text-sm text-green-800 space-y-1">
                <p><strong>Twilio numbers:</strong> ~$1-2/month per number (paid to Twilio)</p>
                <p><strong>Rotation feature:</strong> Included with Professional+ plans, or $39/month add-on</p>
                <p className="text-green-600 mt-2">💡 Tip: Start with 5-10 numbers for optimal rotation</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Team Management Card */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }} className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-indigo-600" />
                  Team Management
                </CardTitle>
                <CardDescription>Invite team members and manage access</CardDescription>
              </div>
              <Badge variant={teamMembers.length > 0 ? "default" : "secondary"}>
                {teamMembers.length + 1} {teamMembers.length === 0 ? "User" : "Users"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Plan Info */}
            <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
              <h4 className="font-semibold text-indigo-900 mb-2 flex items-center gap-2">
                <Zap className="w-4 h-4 text-indigo-600" />
                Team Seats by Plan
              </h4>
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div className="bg-white rounded-lg p-3 text-center border border-indigo-100">
                  <p className="font-medium text-gray-900">Starter</p>
                  <p className="text-2xl font-bold text-indigo-600">1</p>
                  <p className="text-xs text-gray-500">seat</p>
                </div>
                <div className="bg-white rounded-lg p-3 text-center border border-indigo-100">
                  <p className="font-medium text-gray-900">Professional</p>
                  <p className="text-2xl font-bold text-indigo-600">5</p>
                  <p className="text-xs text-gray-500">seats</p>
                </div>
                <div className="bg-white rounded-lg p-3 text-center border border-indigo-100">
                  <p className="font-medium text-gray-900">Unlimited</p>
                  <p className="text-2xl font-bold text-indigo-600">5</p>
                  <p className="text-xs text-gray-500">seats</p>
                </div>
              </div>
            </div>

            {/* Current User (Owner) */}
            <div>
              <Label className="mb-3 block">Account Owner</Label>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center text-white font-semibold">
                    {settings?.email?.charAt(0)?.toUpperCase() || "U"}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{settings?.email || "Loading..."}</p>
                    <p className="text-sm text-gray-500">Account Owner</p>
                  </div>
                </div>
                <Badge className="bg-indigo-600">Owner</Badge>
              </div>
            </div>

            {/* Team Members List */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label>Team Members ({teamMembers.length})</Label>
                <Button
                  size="sm"
                  onClick={() => setShowInviteModal(true)}
                  className="bg-indigo-600 hover:bg-indigo-700"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Invite Member
                </Button>
              </div>

              {loadingTeam ? (
                <div className="text-center py-8 text-gray-500">Loading team...</div>
              ) : teamMembers.length === 0 ? (
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Users className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 mb-2">No team members yet</p>
                  <p className="text-sm text-gray-400">Invite colleagues to collaborate on campaigns</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {teamMembers.map((member) => (
                    <div key={member.id} className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 hover:border-indigo-200 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-semibold">
                          {member.email?.charAt(0)?.toUpperCase() || "?"}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{member.email}</p>
                          <p className="text-sm text-gray-500">
                            {member.status === "pending" ? "Invitation pending" : `Joined ${new Date(member.joined_at).toLocaleDateString()}`}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <select
                          value={member.role}
                          onChange={(e) => updateMemberRole(member.id, e.target.value)}
                          className="text-sm border border-gray-300 rounded-md px-2 py-1"
                        >
                          <option value="member">Member</option>
                          <option value="admin">Admin</option>
                        </select>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeTeamMember(member.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Role Permissions Info */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-3">Role Permissions</h4>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-medium text-gray-700 mb-2">👤 Member</p>
                  <ul className="text-gray-600 space-y-1">
                    <li>• View all campaigns & leads</li>
                    <li>• Create & edit agents</li>
                    <li>• Make calls</li>
                    <li>• View call recordings</li>
                  </ul>
                </div>
                <div>
                  <p className="font-medium text-gray-700 mb-2">👑 Admin</p>
                  <ul className="text-gray-600 space-y-1">
                    <li>• All Member permissions</li>
                    <li>• Manage team members</li>
                    <li>• View billing & usage</li>
                    <li>• Change settings</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Invite Team Member Modal */}
        {showInviteModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md mx-4">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <Mail className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <CardTitle>Invite Team Member</CardTitle>
                    <CardDescription>Send an invitation to join your team</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="invite-email">Email Address</Label>
                  <Input
                    id="invite-email"
                    type="email"
                    placeholder="colleague@company.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="mt-1"
                  />
                </div>
                
                <div>
                  <Label htmlFor="invite-role">Role</Label>
                  <select
                    id="invite-role"
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="member">Member — Can use platform, view data</option>
                    <option value="admin">Admin — Can manage team & settings</option>
                  </select>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> They'll receive an email invitation to create an account and join your team.
                  </p>
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowInviteModal(false);
                    setInviteEmail("");
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={inviteTeamMember}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700"
                >
                  Send Invitation
                </Button>
              </div>
            </Card>
          </div>
        )}

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

// Credit Packs Page
const CreditPacks = () => {
  const { user, refreshUser, sessionToken } = useAuth();
  const [packs, setPacks] = useState({ subscription_plans: {}, lead_packs: [], call_packs: [], topup_packs: [] });
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(null);
  const [activeTab, setActiveTab] = useState("subscriptions");
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [checkingPayment, setCheckingPayment] = useState(false);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const [packsRes, historyRes] = await Promise.all([
        axios.get(`${API}/packs`),
        axios.get(`${API}/payments/history`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: { transactions: [] } }))
      ]);
      setPacks(packsRes.data);
      setPaymentHistory(historyRes.data.transactions || []);
    } catch (error) {
      toast.error("Failed to load packs");
    } finally {
      setLoading(false);
    }
  };

  // Check for payment success on page load
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    const success = urlParams.get('success');
    const canceled = urlParams.get('canceled');
    
    if (canceled) {
      toast.info("Payment was canceled");
      window.history.replaceState({}, '', window.location.pathname);
    } else if (sessionId && success) {
      checkPaymentStatus(sessionId);
    }
    
    fetchData();
  }, []);

  const checkPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 5;
    setCheckingPayment(true);
    
    if (attempts >= maxAttempts) {
      setCheckingPayment(false);
      toast.warning("Payment status check timed out. Please check your email for confirmation.");
      return;
    }
    
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/checkout/status/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.payment_status === 'paid') {
        toast.success(`Payment successful! ${response.data.leads_added > 0 ? `+${response.data.leads_added} leads` : ''} ${response.data.calls_added > 0 ? `+${response.data.calls_added} calls` : ''}`);
        refreshUser();
        fetchData();
        setCheckingPayment(false);
        window.history.replaceState({}, '', window.location.pathname);
      } else if (response.data.status === 'expired') {
        toast.error("Payment session expired. Please try again.");
        setCheckingPayment(false);
        window.history.replaceState({}, '', window.location.pathname);
      } else {
        // Still pending, poll again
        setTimeout(() => checkPaymentStatus(sessionId, attempts + 1), 2000);
      }
    } catch (error) {
      console.error('Error checking payment:', error);
      setCheckingPayment(false);
      toast.error("Error checking payment status");
    }
  };

  const initiateCheckout = async (itemType, itemId, billingCycle = 'monthly') => {
    setPurchasing(`${itemType}_${itemId}`);
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(`${API}/checkout/create-session`, {
        item_type: itemType,
        item_id: itemId,
        origin_url: window.location.origin,
        billing_cycle: billingCycle
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Redirect to Stripe checkout
      window.location.href = response.data.checkout_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create checkout session");
      setPurchasing(null);
    }
  };

  if (loading || checkingPayment) {
    return (
      <div className="p-6 md:p-8 space-y-6">
        <div className="text-center py-12">
          <Clock className="w-12 h-12 text-cyan-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">{checkingPayment ? "Verifying payment..." : "Loading..."}</p>
        </div>
      </div>
    );
  }

  const plans = Object.entries(packs.subscription_plans || {}).map(([key, plan]) => ({
    id: key,
    ...plan
  }));

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="credit-packs-page">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
          Pricing & Plans
        </h1>
        <p className="text-gray-500 mt-1">Choose a plan or purchase additional credits</p>
      </div>

      {/* Current Balance */}
      <Card className="bg-gradient-to-r from-cyan-500 to-teal-500 text-white border-0 shadow-lg">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-cyan-100 text-sm font-medium">Your Current Balance</p>
              <div className="flex items-center gap-8 mt-3">
                <div>
                  <p className="text-4xl font-bold">{user?.lead_credits_remaining?.toLocaleString() || 0}</p>
                  <p className="text-cyan-100 text-sm">Lead Credits</p>
                </div>
                <div className="h-12 w-px bg-white/30" />
                <div>
                  <p className="text-4xl font-bold">{user?.call_credits_remaining?.toLocaleString() || 0}</p>
                  <p className="text-cyan-100 text-sm">Call Credits</p>
                </div>
              </div>
            </div>
            <div className="text-right">
              <Badge className="bg-white/20 text-white border-0 text-sm">
                {user?.subscription_tier ? packs.subscription_plans?.[user.subscription_tier]?.name || 'Free Trial' : 'Free Trial'}
              </Badge>
              <p className="text-cyan-100 text-sm mt-2">{user?.subscription_status === 'active' ? 'Active' : 'Inactive'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full max-w-2xl grid-cols-4">
          <TabsTrigger value="subscriptions">Subscriptions</TabsTrigger>
          <TabsTrigger value="leads">Lead Packs</TabsTrigger>
          <TabsTrigger value="calls">Call Packs</TabsTrigger>
          <TabsTrigger value="topups">Top-ups</TabsTrigger>
        </TabsList>

        {/* Subscription Plans */}
        <TabsContent value="subscriptions" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan) => (
              <Card key={plan.id} className={`bg-white border relative ${plan.id === 'professional' ? 'border-cyan-500 shadow-lg' : 'border-gray-200'}`}>
                {plan.id === 'professional' && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-full text-xs font-medium">
                    Most Popular
                  </div>
                )}
                <CardContent className="p-6">
                  <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                  <div className="mt-3">
                    <span className="text-3xl font-bold text-gray-900">${plan.price}</span>
                    <span className="text-gray-500">/mo</span>
                  </div>
                  <ul className="mt-4 space-y-2">
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-cyan-500" />
                      <span>{plan.leads_per_month.toLocaleString()} leads/mo</span>
                    </li>
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-cyan-500" />
                      <span>{plan.calls_per_month === -1 ? 'Unlimited' : plan.calls_per_month.toLocaleString()} calls/mo</span>
                    </li>
                    {plan.features?.slice(0, 3).map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-gray-400" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button
                    className={`w-full mt-6 ${plan.id === 'professional' ? 'bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600' : 'bg-gray-900 hover:bg-gray-800'} text-white`}
                    onClick={() => initiateCheckout('subscription', plan.id)}
                    disabled={purchasing === `subscription_${plan.id}`}
                    data-testid={`buy-${plan.id}-btn`}
                  >
                    {purchasing === `subscription_${plan.id}` ? (
                      <Clock className="w-4 h-4 animate-spin" />
                    ) : user?.subscription_tier === plan.id ? (
                      'Current Plan'
                    ) : (
                      'Subscribe'
                    )}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
          <p className="text-center text-gray-500 text-sm mt-6">
            Save 5% with quarterly billing or 15% with annual billing
          </p>
        </TabsContent>

        {/* Lead Packs */}
        <TabsContent value="leads" className="mt-6">
          <p className="text-sm text-gray-600 mb-4">Auto-replenishing lead subscriptions for consistent prospecting.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {(packs.lead_packs || []).map((pack) => (
              <Card key={pack.id} className="bg-white border border-gray-200 hover:border-cyan-300 hover:shadow-md transition-all">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-cyan-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Search className="w-6 h-6 text-cyan-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900">{pack.name}</h3>
                  <p className="text-3xl font-bold text-gray-900 mt-2">${pack.price}</p>
                  <p className="text-sm text-gray-500 mt-1">${pack.per_lead?.toFixed(3) || (pack.price / pack.quantity).toFixed(3)}/lead</p>
                  {pack.recurring && <Badge className="mt-2 bg-cyan-100 text-cyan-700">Monthly</Badge>}
                  <Button
                    className="w-full mt-4 bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white"
                    onClick={() => initiateCheckout('lead_pack', pack.id)}
                    disabled={purchasing === `lead_pack_${pack.id}`}
                  >
                    {purchasing === `lead_pack_${pack.id}` ? <Clock className="w-4 h-4 animate-spin" /> : 'Subscribe'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Call Packs */}
        <TabsContent value="calls" className="mt-6">
          <p className="text-sm text-gray-600 mb-4">Overage protection - buy extra calls when you need them.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {(packs.call_packs || []).map((pack) => (
              <Card key={pack.id} className="bg-white border border-gray-200 hover:border-violet-300 hover:shadow-md transition-all">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-violet-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Phone className="w-6 h-6 text-violet-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900">{pack.name}</h3>
                  <p className="text-3xl font-bold text-gray-900 mt-2">${pack.price}</p>
                  <p className="text-sm text-gray-500 mt-1">${pack.per_call?.toFixed(4) || (pack.price / pack.quantity).toFixed(4)}/call</p>
                  <Button
                    className="w-full mt-4 bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white"
                    onClick={() => initiateCheckout('call_pack', pack.id)}
                    disabled={purchasing === `call_pack_${pack.id}`}
                  >
                    {purchasing === `call_pack_${pack.id}` ? <Clock className="w-4 h-4 animate-spin" /> : 'Buy Now'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Top-up Packs */}
        <TabsContent value="topups" className="mt-6">
          <p className="text-sm text-gray-600 mb-4">One-time top-ups at premium rates. For occasional needs only.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {(packs.topup_packs || []).map((pack) => (
              <Card key={pack.id} className="bg-white border border-gray-200 hover:border-amber-300 hover:shadow-md transition-all">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Zap className="w-6 h-6 text-amber-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900">{pack.name}</h3>
                  <p className="text-3xl font-bold text-gray-900 mt-2">${pack.price}</p>
                  <p className="text-sm text-gray-500 mt-1">${pack.per_unit?.toFixed(2) || (pack.price / pack.quantity).toFixed(2)}/unit</p>
                  <Badge className="mt-2 bg-amber-100 text-amber-700">One-time</Badge>
                  <Button
                    className="w-full mt-4 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white"
                    onClick={() => initiateCheckout('topup', pack.id)}
                    disabled={purchasing === `topup_${pack.id}`}
                  >
                    {purchasing === `topup_${pack.id}` ? <Clock className="w-4 h-4 animate-spin" /> : 'Top Up'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Payment History */}
      {paymentHistory.length > 0 && (
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Payment History
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {paymentHistory.slice(0, 10).map((tx, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      tx.item_type === 'subscription' ? 'bg-cyan-100' :
                      tx.item_type === 'lead_pack' ? 'bg-cyan-100' :
                      tx.item_type === 'call_pack' ? 'bg-violet-100' : 'bg-amber-100'
                    }`}>
                      {tx.item_type === 'subscription' ? <CreditCard className="w-4 h-4 text-cyan-600" /> :
                       tx.item_type === 'lead_pack' ? <Search className="w-4 h-4 text-cyan-600" /> :
                       tx.item_type === 'call_pack' ? <Phone className="w-4 h-4 text-violet-600" /> :
                       <Zap className="w-4 h-4 text-amber-600" />}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{tx.item_name}</p>
                      <p className="text-xs text-gray-500">{new Date(tx.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">${tx.amount}</p>
                    <Badge className={tx.payment_status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}>
                      {tx.payment_status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Phone className="w-12 h-12 text-blue-600 animate-pulse mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

// App Router - handles OAuth callback detection
const AppRouter = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const [showSetupWizard, setShowSetupWizard] = useState(false);
  const [showPhoneVerification, setShowPhoneVerification] = useState(false);
  
  // Check if user needs setup wizard (first time login, setup not complete)
  useEffect(() => {
    if (user && !user.setup_wizard_completed && location.pathname.startsWith('/app')) {
      setShowSetupWizard(true);
    }
  }, [user, location.pathname]);

  // Check if trial user needs phone verification
  useEffect(() => {
    if (user && location.pathname.startsWith('/app')) {
      const trialStatus = user.trial_status;
      const isTrial = trialStatus?.is_trial || (!user.subscription_tier || user.subscription_tier === null);
      const phoneVerified = user.phone_verified;
      
      // Show phone verification modal if trial user hasn't verified phone
      if (isTrial && !phoneVerified) {
        setShowPhoneVerification(true);
      }
    }
  }, [user, location.pathname]);

  const handlePhoneVerified = () => {
    setShowPhoneVerification(false);
    // Refresh user data to get updated phone_verified status
    if (refreshUser) {
      refreshUser();
    } else {
      window.location.reload();
    }
  };

  // CRITICAL: Check URL fragment for session_id synchronously during render
  // This prevents race conditions by processing OAuth callback FIRST
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/help" element={<HelpCenterPage />} />
        
        {/* Protected Dashboard Routes */}
        <Route path="/app/*" element={
          <ProtectedRoute>
            <div className="flex flex-col min-h-screen">
              {/* Trial Banner - Shows at top of entire dashboard */}
              <TrialBanner user={user} />
              
              <div className="flex flex-col lg:flex-row flex-1">
                <Sidebar />
                <main className="flex-1 min-h-screen lg:pt-0 pt-14">
                  <Routes>
                    <Route path="/" element={<FunnelPage />} />
                    <Route path="/getting-started" element={<GettingStartedPage />} />
                    <Route path="/usage" element={<UsageDashboard />} />
                    <Route path="/leads" element={<LeadDiscovery />} />
                    <Route path="/campaigns" element={<Campaigns />} />
                    <Route path="/agents" element={<Agents />} />
                    <Route path="/bookings" element={<BookingsPage />} />
                    <Route path="/calls" element={<CallHistory />} />
                    <Route path="/integrations" element={<CRMIntegrationsPage />} />
                    <Route path="/dnc" element={<DNCManagementPage />} />
                    <Route path="/compliance" element={<ComplianceSetupPage />} />
                    <Route path="/packs" element={<CreditPacks />} />
                    <Route path="/settings" element={<SettingsPage />} />
                  </Routes>
                </main>
                
                {/* Help Chat - Always visible in dashboard */}
                <HelpChat currentPage={location.pathname} />
                
                {/* Floating Help Button with Tours */}
                <HelpButton currentPage={location.pathname} />
              </div>
            </div>
            
            {/* Setup Wizard - Shows for new users who haven't completed setup */}
            {showSetupWizard && (
              <SetupWizard 
                user={user}
                onComplete={() => setShowSetupWizard(false)}
                onNavigate={(path) => {
                  navigate(path);
                }}
              />
            )}

            {/* Phone Verification Modal - Shows for trial users who haven't verified phone */}
            {showPhoneVerification && user && (
              <PhoneVerificationModal
                isOpen={showPhoneVerification}
                onClose={() => setShowPhoneVerification(false)}
                onVerified={handlePhoneVerified}
                userEmail={user.email}
              />
            )}
          </ProtectedRoute>
        } />
      </Routes>
    </>
  );
};

// Main App Component
function App() {
  return (
    <div className="App min-h-screen bg-gray-50">
      <BrowserRouter>
        <AuthProvider>
          <AppRouter />
          <Toaster position="top-right" richColors />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
