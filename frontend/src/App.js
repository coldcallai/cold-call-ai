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
import AIColdCallingPage from "@/pages/AIColdCallingPage";
import VoiceAISalesPage from "@/pages/VoiceAISalesPage";
import AISalesDialerPage from "@/pages/AISalesDialerPage";
import AutomatedColdCallingPage from "@/pages/AutomatedColdCallingPage";
import AIAppointmentSetterPage from "@/pages/AIAppointmentSetterPage";
import AnalyticsPage from "@/pages/AnalyticsPage";
import HelpChat from "@/components/HelpChat";
import OnboardingGuide from "@/components/OnboardingGuide";
import SetupWizard from "@/components/SetupWizard";
import TrialBanner from "@/components/TrialBanner";
import PhoneVerificationModal from "@/components/PhoneVerificationModal";
import { VoiceCloneModal, VoiceSettingsModal } from "@/components/VoiceCloning";
import { HelpButton } from "@/components/ProductTour";
import Sidebar from "@/components/Sidebar";
import StatusBadge from "@/components/StatusBadge";
import TrustLine from "@/components/TrustLine";
import FunnelPage from "@/pages/FunnelPage";
import LeadDiscovery from "@/pages/LeadDiscoveryPage";
import BookingDialog from "@/components/BookingDialog";
import Campaigns from "@/pages/CampaignsPage";
import Agents from "@/pages/AgentsPage";
import CallHistory from "@/pages/CallHistoryPage";
import SettingsPage from "@/pages/SettingsPage";
import ReviewRequestsPage from "@/pages/ReviewRequestsPage";
import CreditPacks from "@/pages/CreditPacksPage";
import ROICalculatorPage from "@/pages/ROICalculatorPage";

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

// All page components extracted to separate files:
// - @/components/Sidebar.jsx
// - @/components/StatusBadge.jsx  
// - @/components/BookingDialog.jsx
// - @/pages/FunnelPage.jsx
// - @/pages/LeadDiscoveryPage.jsx
// - @/pages/CampaignsPage.jsx
// - @/pages/AgentsPage.jsx
// - @/pages/CallHistoryPage.jsx
// - @/pages/SettingsPage.jsx
// - @/pages/CreditPacksPage.jsx

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
        <Route path="/roi-calculator" element={<ROICalculatorPage />} />
        <Route path="/ai-cold-calling" element={<AIColdCallingPage />} />
        <Route path="/voice-ai-sales" element={<VoiceAISalesPage />} />
        <Route path="/ai-sales-dialer" element={<AISalesDialerPage />} />
        <Route path="/automated-cold-calling" element={<AutomatedColdCallingPage />} />
        <Route path="/ai-appointment-setter" element={<AIAppointmentSetterPage />} />
        
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
                    <Route path="/analytics" element={<AnalyticsPage />} />
                    <Route path="/integrations" element={<CRMIntegrationsPage />} />
                    <Route path="/dnc" element={<DNCManagementPage />} />
                    <Route path="/compliance" element={<ComplianceSetupPage />} />
                    <Route path="/packs" element={<CreditPacks />} />
                    <Route path="/settings" element={<SettingsPage />} />
                    <Route path="/reviews" element={<ReviewRequestsPage />} />
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
