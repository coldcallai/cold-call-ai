import { useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Phone, Zap, Calendar, CheckCircle, ArrowRight, Play, 
  Users, Clock, Shield, Headphones, BarChart3,
  ChevronDown, Bot, Target, Menu, X, Upload, Volume2, Pause, Loader2,
  Search, MessageSquare, PhoneCall, Mail
} from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

// Call Yourself Demo Component for Landing Page
const CallYourselfHero = () => {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [called, setCalled] = useState(false);
  const navigate = useNavigate();

  const handleCallYourself = async () => {
    if (!phoneNumber.trim()) {
      toast.error("Please enter your phone number");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/demo/call-yourself`,
        { phone_number: phoneNumber }
      );
      
      toast.success("Your phone will ring in a few seconds!");
      setCalled(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to initiate demo call");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-cyan-600 to-teal-600 border border-cyan-400/30 rounded-2xl p-6 md:p-8 max-w-4xl mx-auto shadow-lg">
      <div className="flex flex-col md:flex-row items-center gap-6">
        <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center shadow-lg flex-shrink-0">
          <PhoneCall className="w-8 h-8 text-white" />
        </div>
        <div className="flex-1 text-center md:text-left">
          <h3 className="text-xl md:text-2xl font-bold text-white mb-2">
            Experience the AI Voice Yourself
          </h3>
          <p className="text-cyan-100">
            Don't just take our word for it — call your own phone and hear exactly what your prospects will experience.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
          {!called ? (
            <>
              <Input
                type="tel"
                placeholder="+1 (555) 123-4567"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="w-full sm:w-48 bg-white border-white text-gray-900 placeholder:text-gray-400"
                data-testid="landing-demo-phone"
              />
              <Button
                onClick={handleCallYourself}
                disabled={loading}
                className="w-full sm:w-auto bg-white hover:bg-gray-100 text-cyan-700 font-semibold px-6"
                data-testid="landing-call-yourself-btn"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Phone className="w-4 h-4 mr-2" />
                )}
                {loading ? "Calling..." : "Call Me"}
              </Button>
            </>
          ) : (
            <div className="flex items-center gap-2 text-white">
              <CheckCircle className="w-5 h-5" />
              <span>Check your phone!</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Audio Player Component for Demo Narration
const DemoAudioPlayer = ({ stepId }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const audioRef = useRef(null);

  const playNarration = async () => {
    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Use static pre-generated audio files
      const audioUrl = `/audio/demo_${stepId}.mp3`;
      
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        await audioRef.current.play();
        setIsPlaying(true);
      }
    } catch (err) {
      console.error("Error loading narration:", err);
      setError("Audio unavailable");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAudioEnd = () => {
    setIsPlaying(false);
  };

  return (
    <div className="inline-flex items-center gap-2">
      <audio ref={audioRef} onEnded={handleAudioEnd} />
      <Button
        onClick={playNarration}
        disabled={isLoading}
        size="sm"
        className="rounded-full bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 border border-cyan-500/30 px-4"
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : isPlaying ? (
          <Pause className="w-4 h-4" />
        ) : (
          <Volume2 className="w-4 h-4" />
        )}
        <span className="ml-2 text-sm">{isPlaying ? "Pause" : "Listen"}</span>
      </Button>
      {error && <span className="text-xs text-yellow-400">{error}</span>}
    </div>
  );
};

const LandingPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [openFaq, setOpenFaq] = useState(null);
  const [pricingTab, setPricingTab] = useState("full"); // "byol" or "full"
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // Demo request form state
  const [demoForm, setDemoForm] = useState({
    name: "",
    email: "",
    phone: "",
    companySize: ""
  });
  const [demoSubmitting, setDemoSubmitting] = useState(false);
  const [demoSuccess, setDemoSuccess] = useState(false);

  const handleDemoRequest = async (e) => {
    e.preventDefault();
    setDemoSubmitting(true);
    
    try {
      await axios.post(`${API}/demo-requests`, demoForm);
      setDemoSuccess(true);
      setDemoForm({ name: "", email: "", phone: "", companySize: "" });
      toast.success("Demo request submitted! We'll contact you shortly.");
    } catch (error) {
      console.error("Demo request failed:", error);
      toast.error("Something went wrong. Please try again.");
    } finally {
      setDemoSubmitting(false);
    }
  };

  const goToLogin = () => {
    navigate('/login');
  };

  const goToCalendly = () => {
    window.open('https://calendly.com/dialgenix/15-30min', '_blank');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    alert(`Thanks! We'll contact you at ${email}`);
    setEmail("");
  };

  const steps = [
    {
      number: "01",
      title: "Discover Leads",
      description: "AI finds businesses actively looking for your services through web search and social signals.",
      icon: Target,
    },
    {
      number: "02", 
      title: "AI Calls & Qualifies",
      description: "Our AI makes natural-sounding calls, identifies decision makers, and scores interest level.",
      icon: Phone,
    },
    {
      number: "03",
      title: "Book Meetings",
      description: "Qualified leads are automatically routed to your sales team's calendar. You close.",
      icon: Calendar,
    },
  ];

  const features = [
    {
      icon: Bot,
      title: "AI-Powered Conversations",
      description: "Natural language AI that handles objections and qualifies prospects like your best rep.",
    },
    {
      icon: Upload,
      title: "Upload Your Own List",
      description: "Already have leads? Upload your CSV and let AI call them all. Unlimited uploads supported.",
    },
    {
      icon: Zap,
      title: "Instant Lead Discovery",
      description: "Find businesses with buying intent powered by Apollo.io's 275M+ B2B contact database with verified emails & direct dials.",
    },
    {
      icon: BarChart3,
      title: "Smart Qualification",
      description: "Decision maker verification and interest scoring on every call.",
    },
    {
      icon: Calendar,
      title: "Auto Calendar Booking",
      description: "Qualified leads book directly into your team's Calendly. No manual handoff.",
    },
    {
      icon: Headphones,
      title: "Call Recordings & Transcripts",
      description: "Review every conversation. Train your AI. Improve your pitch.",
    },
  ];

  const pricingPlans = [
    {
      name: "Pay-as-you-go",
      price: "0",
      period: "/month",
      description: "No commitment, pay per use",
      features: [
        "$0.50 per AI call",
        "$0.25 per lead discovered",
        "CSV export & upload",
        "Basic ICP scoring",
        "3-day call recordings",
        "Perfect for testing",
      ],
      cta: "Start Free",
      popular: false,
      isPayg: true,
    },
    {
      name: "Test Drive",
      price: "49",
      period: "/month",
      description: "Try the AI dialer",
      features: [
        "50 AI calls included",
        "Upload your own leads",
        "Full call recordings",
        "AI qualifying & booking",
        "CSV upload",
        "1 user",
      ],
      cta: "Get Started",
      popular: false,
      isTestDrive: true,
    },
  ];

  // BYOL Plans - Bring Your Own List
  const byolPlans = [
    {
      name: "BYOL Starter",
      price: "199",
      period: "/month",
      description: "Bring your own leads",
      features: [
        "250 AI calls/month",
        "Upload your CSV",
        "AI qualifies & books",
        "Call recordings",
        "7-day storage",
        "1 user",
      ],
      cta: "Get Started",
      popular: false,
    },
    {
      name: "BYOL Pro",
      price: "449",
      period: "/month",
      description: "Scale your outreach",
      features: [
        "750 AI calls/month",
        "Upload unlimited CSVs",
        "AI qualifies & books",
        "Call transcripts",
        "30-day storage",
        "Custom scripts",
        "3 users",
      ],
      cta: "Get Started",
      popular: true,
    },
    {
      name: "BYOL Scale",
      price: "799",
      period: "/month",
      description: "High-volume calling",
      features: [
        "1,500 AI calls/month",
        "Upload unlimited CSVs",
        "AI qualifies & books",
        "Call transcripts",
        "60-day storage",
        "Priority support",
        "5 users",
      ],
      cta: "Get Started",
      popular: false,
    },
  ];

  // Full Service Plans - Lead Discovery + Calling
  const fullServicePlans = [
    {
      name: "Discovery Starter",
      price: "399",
      period: "/month",
      description: "We find & call leads",
      features: [
        "500 intent leads/mo",
        "250 AI calls/month",
        "Apollo.io lead discovery",
        "AI qualifies & books",
        "7-day recordings",
        "1 user",
      ],
      cta: "Get Started",
      popular: false,
    },
    {
      name: "Discovery Pro",
      price: "899",
      period: "/month",
      description: "Full-service sales",
      features: [
        "1,500 intent leads/mo",
        "750 AI calls/month",
        "Apollo.io lead discovery",
        "AI qualifies & books",
        "Call transcripts",
        "30-day recordings",
        "3 users",
      ],
      cta: "Get Started",
      popular: true,
    },
    {
      name: "Discovery Elite",
      price: "1,599",
      period: "/month",
      description: "Enterprise lead gen",
      features: [
        "3,000 intent leads/mo",
        "2,000 AI calls/month",
        "Apollo.io lead discovery",
        "AI qualifies & books",
        "90-day recordings",
        "Priority support",
        "5 users",
      ],
      cta: "Get Started",
      popular: false,
    },
  ];

  // Inbound AI Plans - Answer incoming calls
  const inboundPlans = [
    {
      name: "Inbound Lite",
      price: "99",
      period: "/month",
      description: "For small businesses",
      features: [
        "50 inbound calls/month",
        "24/7 AI answering",
        "Basic call routing",
        "SMS notifications",
        "Call recordings",
        "1 phone number",
      ],
      cta: "Get Started",
      popular: false,
    },
    {
      name: "Inbound Starter",
      price: "199",
      period: "/month",
      description: "Never miss a call",
      features: [
        "150 inbound calls/month",
        "24/7 AI answering",
        "Call qualification",
        "Instant booking",
        "Call transcripts",
        "SMS notifications",
        "2 phone numbers",
      ],
      cta: "Get Started",
      popular: false,
    },
    {
      name: "Inbound Pro",
      price: "399",
      period: "/month",
      description: "High-volume inbound",
      features: [
        "500 inbound calls/month",
        "24/7 AI answering",
        "Custom scripts",
        "Calendar integration",
        "Call transcripts",
        "CRM sync",
        "5 phone numbers",
      ],
      cta: "Get Started",
      popular: true,
    },
  ];

  const faqs = [
    {
      question: "How does the AI make phone calls?",
      answer: "Our AI uses advanced speech synthesis and natural language processing to have real conversations. It sounds natural, handles objections, and knows when to hand off to a human.",
    },
    {
      question: "How does AI handle inbound calls to book meetings?",
      answer: "When a customer calls your business, our AI answers instantly—24/7. It greets them naturally, asks qualifying questions, answers FAQs about your services, and books appointments directly on your calendar. No hold music, no missed calls, no voicemail tag.",
    },
    {
      question: "What if someone asks to speak to a human?",
      answer: "The AI immediately offers to schedule a callback with your team or can transfer to a live agent if you have that set up.",
    },
    {
      question: "How do you find leads?",
      answer: "We combine web search, social media monitoring (Twitter/X), and intent signals to find businesses actively looking for solutions like yours.",
    },
    {
      question: "Can I customize what the AI says?",
      answer: "Absolutely. You write the script, set the qualification criteria, and the AI follows your playbook.",
    },
    {
      question: "How do I get started?",
      answer: "Book a free demo with our team. We'll show you how DialGenix works and help you set up your first campaign.",
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Announcement Bar */}
      <div className="bg-gradient-to-r from-cyan-500 via-teal-500 to-emerald-500 py-2 px-4">
        <p className="text-center text-sm text-white font-medium">
          Now onboarding a limited number of new clients →
        </p>
      </div>

      {/* Navigation */}
      <nav className="bg-[#0B1628] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-gradient-to-br from-cyan-400 to-teal-500 rounded-lg flex items-center justify-center">
                <Phone className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold text-white">DialGenix.ai</span>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <a href="#how-it-works" className="text-sm text-gray-300 hover:text-white transition-colors">How It Works</a>
              <a href="#features" className="text-sm text-gray-300 hover:text-white transition-colors">Features</a>
              <a href="#pricing" className="text-sm text-gray-300 hover:text-white transition-colors">Pricing</a>
              <a href="#faq" className="text-sm text-gray-300 hover:text-white transition-colors">FAQ</a>
            </div>

            <div className="hidden md:flex items-center gap-3">
              <button 
                onClick={goToLogin}
                className="rounded-full border border-gray-600 text-white hover:bg-white/10 bg-transparent px-4 py-2 text-sm cursor-pointer"
              >
                Log in
              </button>
              <button 
                onClick={goToCalendly}
                className="rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white px-4 py-2 text-sm cursor-pointer"
              >
                Get started
              </button>
            </div>

            <button 
              className="md:hidden p-2 text-white"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden bg-[#0B1628] border-t border-gray-800 py-4 px-4">
              <div className="flex flex-col space-y-4">
                <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)} className="text-gray-300 hover:text-white py-2">How It Works</a>
                <a href="#features" onClick={() => setMobileMenuOpen(false)} className="text-gray-300 hover:text-white py-2">Features</a>
                <a href="#pricing" onClick={() => setMobileMenuOpen(false)} className="text-gray-300 hover:text-white py-2">Pricing</a>
                <a href="#faq" onClick={() => setMobileMenuOpen(false)} className="text-gray-300 hover:text-white py-2">FAQ</a>
                <div className="pt-4 border-t border-gray-800 flex flex-col gap-3">
                  <button 
                    onClick={() => { setMobileMenuOpen(false); goToLogin(); }}
                    className="w-full rounded-full border border-gray-600 text-white hover:bg-white/10 bg-transparent px-4 py-3 text-sm text-center cursor-pointer"
                  >
                    Log in
                  </button>
                  <button 
                    onClick={() => { setMobileMenuOpen(false); goToCalendly(); }}
                    className="w-full rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white px-4 py-3 text-sm text-center cursor-pointer"
                  >
                    Get started
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Hero Section - Dark */}
      <section className="bg-[#0B1628] pt-20 pb-32 px-6 relative overflow-hidden">
        {/* Gradient orb effect */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-gradient-to-r from-cyan-500/20 via-teal-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-5xl mx-auto text-center relative">
          <h1 className="text-5xl md:text-7xl font-bold leading-tight tracking-tight">
            <span className="text-white">The </span>
            <span className="bg-gradient-to-r from-cyan-400 via-teal-400 to-emerald-400 bg-clip-text text-transparent">AI Cold Calling</span>
            <br />
            <span className="bg-gradient-to-r from-cyan-400 via-teal-400 to-emerald-400 bg-clip-text text-transparent">Platform </span>
            <span className="text-white">for modern sales</span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-400 mt-8 max-w-3xl mx-auto leading-relaxed">
            Stop wasting time on manual dialing. Let our AI agents find leads, have natural, human-like conversations, and book meetings for you <span className="text-cyan-400">➤</span> on autopilot.
          </p>
          
          <p className="text-cyan-400 font-medium mt-4 text-lg">
            Inbound, outbound prospecting, live transfers, and appointment booking—automatically.
          </p>

          {/* Lead Capture Form */}
          <div className="mt-10 max-w-2xl mx-auto">
            <form onSubmit={handleDemoRequest} className="bg-gray-800/60 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 shadow-xl shadow-cyan-500/5">
              <p className="text-white font-semibold text-lg mb-4 text-center">Get a Free Demo</p>
              <div className="grid md:grid-cols-2 gap-4">
                <input
                  type="text"
                  placeholder="Full Name"
                  value={demoForm.name}
                  onChange={(e) => setDemoForm({...demoForm, name: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-900/80 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
                  required
                />
                <input
                  type="email"
                  placeholder="Business Email"
                  value={demoForm.email}
                  onChange={(e) => setDemoForm({...demoForm, email: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-900/80 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
                  required
                />
                <input
                  type="tel"
                  placeholder="Phone Number"
                  value={demoForm.phone}
                  onChange={(e) => setDemoForm({...demoForm, phone: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-900/80 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
                  required
                />
                <select
                  value={demoForm.companySize}
                  onChange={(e) => setDemoForm({...demoForm, companySize: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-900/80 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
                  required
                >
                  <option value="" className="text-gray-500">Company Size</option>
                  <option value="1-10">1-10 employees</option>
                  <option value="11-50">11-50 employees</option>
                  <option value="51-200">51-200 employees</option>
                  <option value="201-500">201-500 employees</option>
                  <option value="500+">500+ employees</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={demoSubmitting}
                className="w-full mt-4 py-3 px-6 bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {demoSubmitting ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Calendar className="w-5 h-5" />
                    Book Your Free Demo
                  </>
                )}
              </button>
              {demoSuccess && (
                <p className="mt-3 text-center text-emerald-400 text-sm">
                  ✓ Thanks! We'll contact you within 24 hours to schedule your demo.
                </p>
              )}
              <p className="text-xs text-gray-500 text-center mt-3">
                Free 15-min consultation • See results first
              </p>
            </form>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10">
            <a href="#demo">
              <Button className="rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white px-8 py-6 text-base font-medium border-0">
                <Play className="w-4 h-4 mr-2" />
                See the demo
              </Button>
            </a>
            <a href="#how-it-works">
              <Button variant="outline" className="rounded-full border-gray-600 text-white hover:bg-white/10 bg-transparent px-8 py-6 text-base">
                Learn more about DialGenix.ai
              </Button>
            </a>
          </div>

          {/* Feature badges */}
          <div className="flex items-center justify-center gap-6 mt-8 flex-wrap">
            <span className="flex items-center gap-2 text-gray-300 text-sm">
              <CheckCircle className="w-4 h-4 text-cyan-400" />
              Lead Discovery
            </span>
            <span className="flex items-center gap-2 text-gray-300 text-sm">
              <CheckCircle className="w-4 h-4 text-cyan-400" />
              AI Conversations
            </span>
            <span className="flex items-center gap-2 text-gray-300 text-sm">
              <CheckCircle className="w-4 h-4 text-cyan-400" />
              Auto-Booking
            </span>
            <span className="flex items-center gap-2 text-gray-300 text-sm">
              <CheckCircle className="w-4 h-4 text-cyan-400" />
              VM Drops
            </span>
          </div>

          {/* Human-like AI callout */}
          <div className="mt-10 max-w-2xl mx-auto">
            <p className="text-gray-200 text-center text-base leading-relaxed bg-gradient-to-r from-cyan-600/20 via-teal-600/30 to-cyan-600/20 border border-cyan-400/40 rounded-xl px-6 py-4 backdrop-blur-sm shadow-lg shadow-cyan-500/10">
              Our AI voice agents don't just talk—they <span className="text-cyan-300 font-semibold">connect</span>. Powered by voice cloning and trained with human-like energy, warmth, and natural conversation flow, they build rapport and qualify leads just like your best sales rep would.
            </p>
          </div>

          {/* Trust logos */}
          <div className="mt-16 space-y-8">
            {/* Partner Logos */}
            <div>
              <p className="text-sm text-gray-500 mb-4">Powered by enterprise-grade technology</p>
              <div className="flex items-center justify-center gap-10 flex-wrap">
                {/* Twilio */}
                <div className="flex items-center gap-2 bg-gray-800/50 px-5 py-3 rounded-lg">
                  <svg className="w-6 h-6 text-red-500" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0C5.381 0 0 5.381 0 12s5.381 12 12 12 12-5.381 12-12S18.619 0 12 0zm0 20.16c-4.499 0-8.16-3.661-8.16-8.16S7.501 3.84 12 3.84s8.16 3.661 8.16 8.16-3.661 8.16-8.16 8.16zm3.36-11.52c1.32 0 2.4 1.08 2.4 2.4s-1.08 2.4-2.4 2.4-2.4-1.08-2.4-2.4 1.08-2.4 2.4-2.4zm-6.72 0c1.32 0 2.4 1.08 2.4 2.4s-1.08 2.4-2.4 2.4-2.4-1.08-2.4-2.4 1.08-2.4 2.4-2.4z"/>
                  </svg>
                  <span className="text-white font-bold text-lg">twilio</span>
                </div>
                {/* OpenAI */}
                <div className="flex items-center gap-2 bg-gray-800/50 px-5 py-3 rounded-lg">
                  <svg className="w-6 h-6 text-emerald-400" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.896zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/>
                  </svg>
                  <span className="text-white font-bold text-lg">OpenAI</span>
                </div>
                {/* ElevenLabs */}
                <div className="flex items-center gap-2 bg-gray-800/50 px-5 py-3 rounded-lg">
                  <svg className="w-6 h-6 text-purple-400" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="7" y="4" width="3" height="16" rx="1"/>
                    <rect x="14" y="4" width="3" height="16" rx="1"/>
                  </svg>
                  <span className="text-white font-bold text-lg">ElevenLabs</span>
                </div>
                {/* Stripe */}
                <div className="flex items-center gap-2 bg-gray-800/50 px-5 py-3 rounded-lg">
                  <svg className="w-6 h-6 text-indigo-400" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-6.99-2.109l-.9 5.555C5.175 22.99 8.385 24 11.714 24c2.641 0 4.843-.624 6.328-1.813 1.664-1.305 2.525-3.236 2.525-5.732 0-4.128-2.524-5.851-6.591-7.305z"/>
                  </svg>
                  <span className="text-white font-bold text-lg">Stripe</span>
                </div>
                {/* Calendly */}
                <div className="flex items-center gap-2 bg-gray-800/50 px-5 py-3 rounded-lg">
                  <svg className="w-6 h-6 text-blue-400" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20a2 2 0 002 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11zM9 11H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm-8 4H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/>
                  </svg>
                  <span className="text-white font-bold text-lg">Calendly</span>
                </div>
                {/* Apollo.io */}
                <div className="flex items-center gap-2 bg-gray-800/50 px-5 py-3 rounded-lg">
                  <svg className="w-6 h-6 text-orange-400" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                  </svg>
                  <span className="text-white font-bold text-lg">Apollo.io</span>
                </div>
                {/* MongoDB */}
                <div className="flex items-center gap-2 bg-gray-800/50 px-5 py-3 rounded-lg">
                  <svg className="w-6 h-6 text-green-500" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                  </svg>
                  <span className="text-white font-bold text-lg">MongoDB</span>
                </div>
                {/* GoHighLevel */}
                <div className="flex items-center gap-2 bg-gray-800/50 px-5 py-3 rounded-lg">
                  <svg className="w-6 h-6 text-yellow-400" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                  <span className="text-white font-bold text-lg">GoHighLevel</span>
                </div>
              </div>
            </div>
            
            {/* Stats & Trust Badges */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
              <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 border border-gray-700/50 rounded-xl p-5 text-center">
                <div className="text-3xl font-bold text-cyan-400 mb-1">99.9%</div>
                <div className="text-sm text-gray-400">Uptime SLA</div>
              </div>
              <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 border border-gray-700/50 rounded-xl p-5 text-center">
                <div className="text-3xl font-bold text-emerald-400 mb-1">256-bit</div>
                <div className="text-sm text-gray-400">SSL Encryption</div>
              </div>
              <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 border border-gray-700/50 rounded-xl p-5 text-center">
                <div className="text-3xl font-bold text-purple-400 mb-1">50+</div>
                <div className="text-sm text-gray-400">AI Voice Options</div>
              </div>
              <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 border border-gray-700/50 rounded-xl p-5 text-center">
                <div className="text-3xl font-bold text-orange-400 mb-1">24/7</div>
                <div className="text-sm text-gray-400">Automated Calling</div>
              </div>
            </div>
            
            {/* Compliance Badges */}
            <div className="flex items-center justify-center gap-6 flex-wrap">
              <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-4 py-2 rounded-full text-sm font-medium">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                TCPA Compliant
              </div>
              <div className="flex items-center gap-2 bg-blue-500/10 border border-blue-500/30 text-blue-400 px-4 py-2 rounded-full text-sm font-medium">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                GDPR Ready
              </div>
              <div className="flex items-center gap-2 bg-purple-500/10 border border-purple-500/30 text-purple-400 px-4 py-2 rounded-full text-sm font-medium">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                SOC 2 Type II
              </div>
              <div className="flex items-center gap-2 bg-orange-500/10 border border-orange-500/30 text-orange-400 px-4 py-2 rounded-full text-sm font-medium">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                DNC List Verified
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Product Demo Section */}
      <section id="demo" className="bg-gradient-to-b from-[#0B1628] to-[#0a0f1a] py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <span className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-full text-cyan-400 text-sm font-medium mb-6">
              <Play className="w-4 h-4" />
              See It In Action
            </span>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Your AI Sales Pipeline
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Watch how DialGenix.ai automates your entire cold calling workflow
            </p>
          </div>
        </div>

        {/* White strip behind Call Yourself Demo */}
        <div className="bg-white py-8 -mx-6 px-6 mb-8">
          <div className="max-w-6xl mx-auto">
            <CallYourselfHero />
          </div>
        </div>

        <div className="max-w-6xl mx-auto">

          {/* Demo Screenshots */}
          <div className="space-y-20">
            {/* Screenshot 1: Sales Funnel */}
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="order-2 lg:order-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/20 border border-emerald-500/30 rounded-full text-emerald-400 text-sm font-medium">
                    Step 1
                  </div>
                  <DemoAudioPlayer stepId="step1" />
                </div>
                <h3 className="text-3xl font-bold text-white mb-4">Visual Sales Funnel</h3>
                <p className="text-gray-400 text-lg mb-6">
                  Track every lead through your pipeline — from discovery to booked meeting. 
                  See real-time stats on qualification rates, calls made, and bookings.
                </p>
                <ul className="space-y-3">
                  <li className="flex items-center gap-3 text-gray-300">
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                    Drag-and-drop lead management
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                    One-click AI calling
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                    Real-time conversion metrics
                  </li>
                </ul>
              </div>
              <div className="order-1 lg:order-2">
                <div className="bg-gradient-to-br from-cyan-500/10 to-teal-500/10 rounded-2xl p-4 border border-cyan-500/20">
                  {/* Styled Funnel Mockup */}
                  <div className="bg-[#0B1628] rounded-xl p-4 shadow-2xl">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-700">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-teal-500 rounded-lg"></div>
                        <span className="text-white font-semibold">Sales Pipeline</span>
                      </div>
                      <div className="flex gap-4 text-xs">
                        <span className="text-gray-400">Total: <span className="text-white">248 leads</span></span>
                        <span className="text-gray-400">Rate: <span className="text-green-400">3.6%</span></span>
                      </div>
                    </div>
                    {/* Funnel Columns */}
                    <div className="grid grid-cols-4 gap-2">
                      {/* New */}
                      <div className="bg-gray-800/50 rounded-lg p-2">
                        <div className="text-xs text-emerald-400 font-medium mb-2 flex justify-between">
                          <span>New</span><span className="bg-emerald-500/20 px-1.5 rounded">70</span>
                        </div>
                        <div className="space-y-1.5">
                          <div className="bg-gray-700/50 rounded p-1.5 text-xs">
                            <div className="text-white text-[10px]">Acme Corp</div>
                            <div className="text-gray-500 text-[8px]">+1 555-0123</div>
                          </div>
                          <div className="bg-gray-700/50 rounded p-1.5 text-xs">
                            <div className="text-white text-[10px]">TechStart Inc</div>
                            <div className="text-gray-500 text-[8px]">+1 555-0456</div>
                          </div>
                        </div>
                      </div>
                      {/* Contacted */}
                      <div className="bg-gray-800/50 rounded-lg p-2">
                        <div className="text-xs text-blue-400 font-medium mb-2 flex justify-between">
                          <span>Contacted</span><span className="bg-blue-500/20 px-1.5 rounded">136</span>
                        </div>
                        <div className="space-y-1.5">
                          <div className="bg-gray-700/50 rounded p-1.5 text-xs">
                            <div className="text-white text-[10px]">GlobalTech</div>
                            <div className="text-green-400 text-[8px]">Interested</div>
                          </div>
                          <div className="bg-gray-700/50 rounded p-1.5 text-xs">
                            <div className="text-white text-[10px]">DataFlow</div>
                            <div className="text-yellow-400 text-[8px]">Call back</div>
                          </div>
                        </div>
                      </div>
                      {/* Qualified */}
                      <div className="bg-gray-800/50 rounded-lg p-2">
                        <div className="text-xs text-purple-400 font-medium mb-2 flex justify-between">
                          <span>Qualified</span><span className="bg-purple-500/20 px-1.5 rounded">42</span>
                        </div>
                        <div className="space-y-1.5">
                          <div className="bg-gray-700/50 rounded p-1.5 text-xs">
                            <div className="text-white text-[10px]">MegaSales Co</div>
                            <div className="text-purple-400 text-[8px]">Hot lead</div>
                          </div>
                          <div className="bg-gray-700/50 rounded p-1.5 text-xs">
                            <div className="text-white text-[10px]">CloudFirst</div>
                            <div className="text-purple-400 text-[8px]">Decision maker</div>
                          </div>
                        </div>
                      </div>
                      {/* Booked */}
                      <div className="bg-gray-800/50 rounded-lg p-2">
                        <div className="text-xs text-orange-400 font-medium mb-2 flex justify-between">
                          <span>Booked</span><span className="bg-orange-500/20 px-1.5 rounded">5</span>
                        </div>
                        <div className="space-y-1.5">
                          <div className="bg-gray-700/50 rounded p-1.5 text-xs border border-green-500/30">
                            <div className="text-white text-[10px]">Enterprise Ltd</div>
                            <div className="text-green-400 text-[8px]">Tomorrow 2pm</div>
                          </div>
                          <div className="bg-gray-700/50 rounded p-1.5 text-xs border border-green-500/30">
                            <div className="text-white text-[10px]">ScaleUp Inc</div>
                            <div className="text-green-400 text-[8px]">Friday 10am</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Screenshot 2: Lead Discovery */}
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <div className="bg-gradient-to-br from-cyan-500/10 to-teal-500/10 rounded-2xl p-4 border border-cyan-500/20">
                  {/* Styled Lead Discovery Mockup */}
                  <div className="bg-[#0B1628] rounded-xl p-4 shadow-2xl">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-700">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-cyan-500 rounded-lg flex items-center justify-center">
                          <Search className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-white font-semibold">Lead Discovery</span>
                      </div>
                      <button className="bg-cyan-500 text-white text-xs px-3 py-1.5 rounded-lg">+ Find Leads</button>
                    </div>
                    {/* Search Keywords */}
                    <div className="bg-gray-800/50 rounded-lg p-3 mb-3">
                      <div className="text-xs text-gray-400 mb-2">Active Keywords</div>
                      <div className="flex flex-wrap gap-2">
                        <span className="bg-blue-500/20 text-blue-400 text-xs px-2 py-1 rounded-full">HVAC repair</span>
                        <span className="bg-blue-500/20 text-blue-400 text-xs px-2 py-1 rounded-full">plumbing services</span>
                        <span className="bg-blue-500/20 text-blue-400 text-xs px-2 py-1 rounded-full">roofing contractor</span>
                      </div>
                    </div>
                    {/* Results Table */}
                    <div className="space-y-2">
                      <div className="grid grid-cols-4 text-xs text-gray-500 px-2">
                        <span>Business</span>
                        <span>Phone</span>
                        <span>Type</span>
                        <span>Score</span>
                      </div>
                      <div className="bg-gray-800/30 rounded-lg p-2 grid grid-cols-4 items-center text-xs">
                        <div>
                          <div className="text-white">ABC Plumbing</div>
                          <div className="text-gray-500 text-[10px]">Miami, FL</div>
                        </div>
                        <span className="text-gray-300">+1 305-555-0123</span>
                        <span className="text-green-400 bg-green-500/20 px-1.5 py-0.5 rounded text-[10px] w-fit">Mobile</span>
                        <span className="text-cyan-400">92%</span>
                      </div>
                      <div className="bg-gray-800/30 rounded-lg p-2 grid grid-cols-4 items-center text-xs">
                        <div>
                          <div className="text-white">FastFix HVAC</div>
                          <div className="text-gray-500 text-[10px]">Tampa, FL</div>
                        </div>
                        <span className="text-gray-300">+1 813-555-0456</span>
                        <span className="text-blue-400 bg-blue-500/20 px-1.5 py-0.5 rounded text-[10px] w-fit">Landline</span>
                        <span className="text-cyan-400">87%</span>
                      </div>
                      <div className="bg-gray-800/30 rounded-lg p-2 grid grid-cols-4 items-center text-xs">
                        <div>
                          <div className="text-white">Pro Roofing Co</div>
                          <div className="text-gray-500 text-[10px]">Orlando, FL</div>
                        </div>
                        <span className="text-gray-300">+1 407-555-0789</span>
                        <span className="text-green-400 bg-green-500/20 px-1.5 py-0.5 rounded text-[10px] w-fit">Mobile</span>
                        <span className="text-cyan-400">85%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-full text-blue-400 text-sm font-medium">
                    Step 2
                  </div>
                  <DemoAudioPlayer stepId="step2" />
                </div>
                <h3 className="text-3xl font-bold text-white mb-4">AI Lead Discovery</h3>
                <p className="text-gray-400 text-lg mb-6">
                  Enter your target keywords and let AI find businesses actively searching for solutions like yours. 
                  Or upload your own CSV with existing leads.
                </p>
                <ul className="space-y-3">
                  <li className="flex items-center gap-3 text-gray-300">
                    <CheckCircle className="w-5 h-5 text-blue-400" />
                    Intent-based lead discovery
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <CheckCircle className="w-5 h-5 text-blue-400" />
                    CSV upload for existing lists
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <CheckCircle className="w-5 h-5 text-blue-400" />
                    Phone verification (Mobile/Landline)
                  </li>
                </ul>
              </div>
            </div>

            {/* Screenshot 3: Call History */}
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="order-2 lg:order-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-500/20 border border-purple-500/30 rounded-full text-purple-400 text-sm font-medium">
                    Step 3
                  </div>
                  <DemoAudioPlayer stepId="step3" />
                </div>
                <h3 className="text-3xl font-bold text-white mb-4">Call Recordings & Results</h3>
                <p className="text-gray-400 text-lg mb-6">
                  Review every AI conversation. See call transcripts, qualification scores, 
                  and listen to recordings to train your AI further.
                </p>
                <ul className="space-y-3">
                  <li className="flex items-center gap-3 text-gray-300">
                    <CheckCircle className="w-5 h-5 text-purple-400" />
                    Full call recordings
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <CheckCircle className="w-5 h-5 text-purple-400" />
                    AI transcription
                  </li>
                  <li className="flex items-center gap-3 text-gray-300">
                    <CheckCircle className="w-5 h-5 text-purple-400" />
                    Qualification scoring
                  </li>
                </ul>
              </div>
              <div className="order-1 lg:order-2">
                <div className="bg-gradient-to-br from-cyan-500/10 to-teal-500/10 rounded-2xl p-4 border border-cyan-500/20">
                  {/* Styled Call History Mockup */}
                  <div className="bg-[#0B1628] rounded-xl p-4 shadow-2xl">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-700">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-purple-400 to-pink-500 rounded-lg flex items-center justify-center">
                          <Phone className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-white font-semibold">Call History</span>
                      </div>
                      <div className="flex gap-2 text-xs">
                        <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded">12 Completed</span>
                        <span className="bg-orange-500/20 text-orange-400 px-2 py-1 rounded">3 Booked</span>
                      </div>
                    </div>
                    {/* Call Records */}
                    <div className="space-y-2">
                      {/* Call 1 - Booked */}
                      <div className="bg-gray-800/50 rounded-lg p-3 border-l-2 border-green-500">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center">
                              <Calendar className="w-3 h-3 text-green-400" />
                            </div>
                            <span className="text-white text-sm font-medium">ABC Plumbing</span>
                            <span className="bg-green-500/20 text-green-400 text-[10px] px-2 py-0.5 rounded-full">BOOKED</span>
                          </div>
                          <span className="text-gray-500 text-xs">2:34 min</span>
                        </div>
                        <div className="text-gray-400 text-xs ml-8">"Interested in demo, scheduled for Thursday 3pm"</div>
                        <div className="flex gap-2 mt-2 ml-8">
                          <button className="text-[10px] text-cyan-400 bg-cyan-500/10 px-2 py-1 rounded">Play Recording</button>
                          <button className="text-[10px] text-gray-400 bg-gray-700/50 px-2 py-1 rounded">Transcript</button>
                        </div>
                      </div>
                      {/* Call 2 - Qualified */}
                      <div className="bg-gray-800/50 rounded-lg p-3 border-l-2 border-purple-500">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center">
                              <CheckCircle className="w-3 h-3 text-purple-400" />
                            </div>
                            <span className="text-white text-sm font-medium">FastFix HVAC</span>
                            <span className="bg-purple-500/20 text-purple-400 text-[10px] px-2 py-0.5 rounded-full">QUALIFIED</span>
                          </div>
                          <span className="text-gray-500 text-xs">1:52 min</span>
                        </div>
                        <div className="text-gray-400 text-xs ml-8">"Decision maker, needs follow-up next week"</div>
                      </div>
                      {/* Call 3 - VM Drop */}
                      <div className="bg-gray-800/50 rounded-lg p-3 border-l-2 border-orange-500">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 bg-orange-500/20 rounded-full flex items-center justify-center">
                              <MessageSquare className="w-3 h-3 text-orange-400" />
                            </div>
                            <span className="text-white text-sm font-medium">Pro Roofing Co</span>
                            <span className="bg-orange-500/20 text-orange-400 text-[10px] px-2 py-0.5 rounded-full">VM DROP</span>
                          </div>
                          <span className="text-gray-500 text-xs">0:30 min</span>
                        </div>
                        <div className="text-gray-400 text-xs ml-8">"Left voicemail, auto-retry scheduled"</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* CTA after demo */}
          <div className="text-center mt-20">
            <button 
              onClick={goToCalendly}
              className="rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white px-10 py-6 text-lg font-medium border-0 inline-flex items-center cursor-pointer transition-all"
            >
              Get Started
              <ArrowRight className="w-5 h-5 ml-2" />
            </button>
            <p className="text-gray-500 mt-4">Book a demo and see DialGenix in action.</p>
          </div>
        </div>
      </section>

      {/* Upload Your Own List Callout */}
      <section className="bg-gradient-to-r from-[#0B1628] to-[#1a2744] py-12 px-6 border-t border-b border-cyan-500/20">
        <div className="max-w-5xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="flex items-center gap-6">
              <div className="w-16 h-16 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-2xl flex items-center justify-center flex-shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white mb-1">Already have leads? Upload your list!</h3>
                <p className="text-gray-400">
                  Upload your CSV with phone numbers and let our AI call them all. <span className="text-cyan-400 font-medium">Unlimited uploads</span> starting at $199/mo.
                </p>
              </div>
            </div>
            <button 
              onClick={goToLogin}
              className="rounded-full bg-white text-gray-900 hover:bg-gray-100 px-6 py-4 text-base font-medium whitespace-nowrap inline-flex items-center cursor-pointer"
            >
              Upload CSV Now
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          </div>
        </div>
      </section>

      {/* AI Capabilities Section */}
      <section className="bg-gradient-to-b from-[#0a0f1a] to-[#0B1628] py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left: Text Content */}
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-full mb-6">
                <Zap className="w-4 h-4 text-cyan-400" />
                <span className="text-cyan-400 text-sm font-medium">AI-Powered Outbound</span>
              </div>
              
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6 leading-tight">
                Scale your outreach to <span className="bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">thousands of calls</span> simultaneously
              </h2>
              
              <p className="text-gray-400 text-lg mb-8 leading-relaxed">
                Our AI voice agents conduct natural, human-like conversations at scale. They handle lead qualification, 
                appointment scheduling, and follow-ups—without writing a single line of code. When a prospect shows 
                interest, the AI seamlessly hands off warm leads to your human sales team.
              </p>

              <div className="space-y-4">
                {[
                  { 
                    icon: "🎯", 
                    title: "Multi-Turn Conversations", 
                    desc: "AI navigates complex dialogues, handles objections, and adapts to any response" 
                  },
                  { 
                    icon: "🔗", 
                    title: "CRM Integration Ready", 
                    desc: "Connect to HubSpot, Salesforce, Go High Level (GHL), or your existing tools via API" 
                  },
                  { 
                    icon: "📞", 
                    title: "Intelligent Call Routing", 
                    desc: "Hot leads instantly transferred to available reps with full context" 
                  },
                  { 
                    icon: "⚡", 
                    title: "No-Code Setup", 
                    desc: "Launch campaigns in minutes with our intuitive campaign builder" 
                  },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-start gap-4 p-4 bg-white/5 rounded-xl border border-white/10 hover:border-cyan-500/30 transition-colors">
                    <span className="text-2xl">{item.icon}</span>
                    <div>
                      <h4 className="text-white font-semibold mb-1">{item.title}</h4>
                      <p className="text-gray-400 text-sm">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Visual/Stats */}
            <div className="relative">
              <div className="bg-gradient-to-br from-cyan-500/20 to-teal-500/20 rounded-3xl p-8 border border-cyan-500/20">
                {/* Simulated Call Interface */}
                <div className="bg-[#0B1628] rounded-2xl p-6 mb-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-full flex items-center justify-center">
                      <Phone className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-white font-medium">AI Agent Active</p>
                      <p className="text-cyan-400 text-sm">Making 847 simultaneous calls</p>
                    </div>
                    <div className="ml-auto flex items-center gap-2">
                      <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                      <span className="text-green-400 text-sm">Live</span>
                    </div>
                  </div>
                  
                  {/* Conversation Preview */}
                  <div className="space-y-3 text-sm">
                    <div className="flex gap-3">
                      <span className="text-cyan-400 font-medium min-w-[40px]">AI:</span>
                      <span className="text-gray-300">"Hi, this is Sarah from ABC Solutions. Am I speaking with the owner?"</span>
                    </div>
                    <div className="flex gap-3">
                      <span className="text-amber-400 font-medium min-w-[40px]">Lead:</span>
                      <span className="text-gray-300">"Yes, this is Mike. What's this about?"</span>
                    </div>
                    <div className="flex gap-3">
                      <span className="text-cyan-400 font-medium min-w-[40px]">AI:</span>
                      <span className="text-gray-300">"Great to connect, Mike! We help businesses like yours reduce payment processing fees by up to 40%..."</span>
                    </div>
                  </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { value: "1000+", label: "Calls/hour" },
                    { value: "92%", label: "Answer rate" },
                    { value: "3.2x", label: "More meetings" },
                  ].map((stat, idx) => (
                    <div key={idx} className="text-center p-4 bg-white/5 rounded-xl">
                      <p className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
                        {stat.value}
                      </p>
                      <p className="text-gray-400 text-xs mt-1">{stat.label}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Floating Elements */}
              <div className="absolute -top-4 -right-4 bg-green-500 text-white px-4 py-2 rounded-full text-sm font-medium shadow-lg">
                24/7 Automated
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section - White */}
      <section className="bg-white py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">The cold calling problem</h2>
            <p className="text-gray-600 text-lg">Your sales team is wasting time on tasks AI can do better</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { value: "65%", label: "of sales rep time spent NOT selling", source: "Salesforce" },
              { value: "8+", label: "attempts needed to reach a prospect", source: "RAIN Group" },
              { value: "$15K", label: "average cost to hire one SDR/month", source: "Bridge Group" },
            ].map((stat, idx) => (
              <div 
                key={idx} 
                className="bg-gray-50 rounded-2xl p-8 text-center"
              >
                <p className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-cyan-500 to-teal-500 bg-clip-text text-transparent">
                  {stat.value}
                </p>
                <p className="text-gray-700 mt-4 text-lg">{stat.label}</p>
                <p className="text-gray-400 text-sm mt-2">{stat.source}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works - Light Gray */}
      <section id="how-it-works" className="bg-gray-50 py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Your plays, your way</h2>
            <p className="text-gray-600 text-lg max-w-2xl mx-auto">
              With DialGenix.ai, the orchestration of tasks for both AI Agents and human reps happens in a single workflow.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div key={idx} className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-4 mb-6">
                    <span className="text-4xl font-bold text-gray-200">{step.number}</span>
                    <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl flex items-center justify-center">
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">{step.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{step.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Features - White */}
      <section id="features" className="bg-white py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Everything you need to scale outbound</h2>
            <p className="text-gray-600 text-lg">Powerful features that replace an entire SDR team</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <div 
                  key={idx}
                  className="bg-gray-50 rounded-2xl p-6 hover:bg-gray-100 transition-colors"
                >
                  <div className="w-12 h-12 bg-gradient-to-br from-cyan-100 to-teal-100 rounded-xl flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 text-teal-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Inbound AI Section - NEW */}
      <section className="bg-gradient-to-b from-[#0B1628] to-[#0f1c32] py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <span className="text-cyan-400 text-sm font-medium uppercase tracking-wide">AI-Powered Inbound</span>
              <h2 className="text-3xl md:text-4xl font-bold text-white mt-2 mb-6" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                Turn Every Missed Call Into a Booking—Automatically
              </h2>
              <p className="text-gray-400 text-lg mb-8">
                Never lose a lead to voicemail again. Our AI answers every call 24/7, qualifies prospects, 
                and books appointments directly on your calendar—even at 2am.
              </p>
              
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Phone className="w-5 h-5 text-cyan-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold">24/7 Call Answering</h4>
                    <p className="text-gray-400 text-sm">AI picks up instantly—no hold music, no missed opportunities</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <MessageSquare className="w-5 h-5 text-cyan-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold">Natural Conversations</h4>
                    <p className="text-gray-400 text-sm">Answers questions, handles objections, sounds completely human</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Calendar className="w-5 h-5 text-cyan-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold">Instant Booking</h4>
                    <p className="text-gray-400 text-sm">Books appointments directly on your calendar in real-time</p>
                  </div>
                </div>
              </div>
              
              <button 
                onClick={goToCalendly}
                className="mt-8 rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white px-8 py-4 text-lg font-medium inline-flex items-center gap-2 cursor-pointer transition-all"
              >
                See Inbound AI in Action
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
            
            <div className="bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-8">
              <div className="text-center mb-6">
                <h3 className="text-white text-xl font-semibold mb-2">Perfect For</h3>
                <p className="text-gray-400">Service businesses that can't afford to miss calls</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                {[
                  { icon: "🏠", name: "Roofers" },
                  { icon: "⚡", name: "Electricians" },
                  { icon: "🔧", name: "Plumbers" },
                  { icon: "❄️", name: "HVAC" },
                  { icon: "🏢", name: "Real Estate" },
                  { icon: "⚖️", name: "Law Firms" },
                  { icon: "🦷", name: "Dental" },
                  { icon: "🏥", name: "Medical" },
                ].map((industry, idx) => (
                  <div key={idx} className="bg-white/5 rounded-lg p-3 text-center">
                    <span className="text-2xl">{industry.icon}</span>
                    <p className="text-white text-sm mt-1">{industry.name}</p>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 p-4 bg-gradient-to-r from-cyan-500/20 to-teal-500/20 rounded-lg border border-cyan-500/30">
                <p className="text-cyan-300 text-sm text-center">
                  <span className="font-semibold">💡 Did you know?</span> 80% of callers won't leave a voicemail—they'll just call your competitor.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Live Transfer Section */}
      <section className="bg-gradient-to-b from-[#0f1c32] to-[#0B1628] py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <span className="text-orange-400 text-sm font-medium uppercase tracking-wide">Live Transfers</span>
              <h2 className="text-3xl md:text-4xl font-bold text-white mt-2 mb-6" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                Instant Live Transfers When It Matters Most
              </h2>
              <p className="text-gray-400 text-lg mb-8">
                Turn high-intent conversations into real opportunities—instantly.
              </p>
              
              <div className="space-y-6">
                <div>
                  <h4 className="text-white font-semibold text-lg mb-3">How It Works</h4>
                  <p className="text-gray-400 mb-4">When a prospect shows strong interest, DialGenix takes action in real time:</p>
                  
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-orange-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-orange-400 text-xs font-bold">1</span>
                      </div>
                      <p className="text-gray-300">Detects buying signals and high intent automatically</p>
                    </div>
                    
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-orange-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-orange-400 text-xs font-bold">2</span>
                      </div>
                      <div>
                        <p className="text-gray-300">Asks:</p>
                        <p className="text-orange-300 italic mt-1">"Would you like me to connect you with a team member now to go over this in more detail?"</p>
                      </div>
                    </div>
                    
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-orange-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-orange-400 text-xs font-bold">3</span>
                      </div>
                      <p className="text-gray-300">If they say yes → <span className="text-white font-medium">instantly transfers the call to your team</span></p>
                    </div>
                    
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-orange-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-orange-400 text-xs font-bold">4</span>
                      </div>
                      <div>
                        <p className="text-gray-300">Smooth handoff:</p>
                        <p className="text-orange-300 italic mt-1">"Great! Let me connect you with a team member right now. Please hold."</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-8">
              <h3 className="text-white text-xl font-semibold mb-6 text-center">Why It Matters</h3>
              
              <div className="space-y-4">
                <div className="flex items-center gap-4 p-4 bg-orange-500/10 rounded-lg border border-orange-500/20">
                  <Zap className="w-8 h-8 text-orange-400 flex-shrink-0" />
                  <p className="text-white">Connect with prospects at <span className="text-orange-400 font-semibold">peak interest</span></p>
                </div>
                
                <div className="flex items-center gap-4 p-4 bg-orange-500/10 rounded-lg border border-orange-500/20">
                  <Phone className="w-8 h-8 text-orange-400 flex-shrink-0" />
                  <p className="text-white">Eliminate delays that <span className="text-orange-400 font-semibold">cost you deals</span></p>
                </div>
                
                <div className="flex items-center gap-4 p-4 bg-orange-500/10 rounded-lg border border-orange-500/20">
                  <Target className="w-8 h-8 text-orange-400 flex-shrink-0" />
                  <p className="text-white">Increase conversions with <span className="text-orange-400 font-semibold">real-time human follow-up</span></p>
                </div>
                
                <div className="flex items-center gap-4 p-4 bg-orange-500/10 rounded-lg border border-orange-500/20">
                  <CheckCircle className="w-8 h-8 text-orange-400 flex-shrink-0" />
                  <p className="text-white">No more <span className="text-orange-400 font-semibold">missed high-value opportunities</span></p>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-gradient-to-r from-orange-500/20 to-amber-500/20 rounded-lg border border-orange-500/30">
                <p className="text-orange-300 text-sm text-center font-medium">
                  🔥 The Result: Your hottest leads go from conversation → live conversation with your team in seconds.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison - Light Gray */}
      <section className="bg-gray-50 py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">DialGenix.ai vs. Hiring SDRs</h2>
            <p className="text-gray-600 text-lg">See why AI-powered calling makes sense</p>
          </div>

          <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
            <div className="grid grid-cols-3 text-center border-b border-gray-100">
              <div className="p-6"></div>
              <div className="p-6 bg-gradient-to-b from-cyan-50 to-white">
                <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl flex items-center justify-center mx-auto mb-2">
                  <Phone className="w-5 h-5 text-white" />
                </div>
                <p className="font-semibold text-gray-900">DialGenix.ai</p>
              </div>
              <div className="p-6">
                <div className="w-10 h-10 bg-gray-200 rounded-xl flex items-center justify-center mx-auto mb-2">
                  <Users className="w-5 h-5 text-gray-500" />
                </div>
                <p className="font-semibold text-gray-500">Hiring SDRs</p>
              </div>
            </div>

            {[
              { metric: "Monthly Cost", ai: "$199-899", human: "$12,000+" },
              { metric: "Calls Per Day", ai: "500+", human: "50-80" },
              { metric: "Time to Start", ai: "Same day", human: "2-3 months" },
              { metric: "Consistency", ai: "100%", human: "Variable" },
              { metric: "Availability", ai: "24/7", human: "8 hours" },
              { metric: "Scale Up/Down", ai: "Instant", human: "Weeks" },
            ].map((row, idx) => (
              <div key={idx} className="grid grid-cols-3 text-center border-b border-gray-50 last:border-0">
                <div className="p-4 text-gray-600 text-sm flex items-center justify-center font-medium">{row.metric}</div>
                <div className="p-4 bg-cyan-50/30 font-semibold text-teal-600">{row.ai}</div>
                <div className="p-4 text-gray-400">{row.human}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Value Proposition Callout - Above Pricing */}
      <section className="bg-gradient-to-b from-gray-50 to-white py-16 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="text-center bg-gradient-to-r from-blue-600/10 via-cyan-600/15 to-blue-600/10 border border-cyan-500/30 rounded-2xl px-8 py-8 backdrop-blur-sm shadow-lg">
            <p className="text-gray-800 text-lg md:text-xl leading-relaxed font-medium">
              Create your own call scripts, handle objections with confidence, and seamlessly book meetings—all in one place. 
              <span className="text-cyan-600 font-semibold"> Take control of your outreach</span> and turn more conversations into sales.
            </p>
          </div>
        </div>
      </section>

      {/* Pricing - White */}
      <section id="pricing" className="bg-white py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Simple, transparent pricing</h2>
            <p className="text-gray-600 text-lg">Choose your path: Bring your own leads or let us find them for you</p>
          </div>

          {/* Pricing Toggle */}
          <div className="flex justify-center mb-12">
            <div className="inline-flex bg-gray-100 rounded-full p-1 flex-wrap justify-center gap-1">
              <button 
                onClick={() => setPricingTab('byol')}
                className={`px-5 py-3 rounded-full text-sm font-medium transition-all ${
                  pricingTab === 'byol' 
                    ? 'bg-white shadow text-gray-900' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                📋 Outbound (BYOL)
              </button>
              <button 
                onClick={() => setPricingTab('full')}
                className={`px-5 py-3 rounded-full text-sm font-medium transition-all ${
                  pricingTab === 'full' 
                    ? 'bg-gradient-to-r from-cyan-500 to-teal-500 shadow text-white' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                🚀 Outbound (Full Service)
              </button>
              <button 
                onClick={() => setPricingTab('inbound')}
                className={`px-5 py-3 rounded-full text-sm font-medium transition-all ${
                  pricingTab === 'inbound' 
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 shadow text-white' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                📞 Inbound AI
              </button>
            </div>
          </div>

          {/* BYOL Description */}
          {pricingTab === 'byol' && (
            <div className="text-center mb-8">
              <p className="text-gray-600">Already have a lead list? Upload your CSV and let our AI call, qualify, and book meetings.</p>
            </div>
          )}

          {/* Full Service Description */}
          {pricingTab === 'full' && (
            <div className="text-center mb-8">
              <p className="text-teal-600 font-medium">✨ Only DialGenix finds high-intent leads with GPT AND calls them automatically</p>
            </div>
          )}

          {/* Entry Plans (always shown) */}
          <div className="grid md:grid-cols-2 gap-6 max-w-2xl mx-auto mb-8">
            {pricingPlans.map((plan, idx) => (
              <div 
                key={idx}
                className={`relative bg-white border rounded-2xl p-6 ${
                  plan.isPayg
                    ? 'border-purple-300 shadow-md shadow-purple-500/10'
                    : 'border-gray-200'
                }`}
              >
                {plan.isPayg && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full text-sm font-medium">
                    No Commitment
                  </div>
                )}
                
                <h3 className="text-lg font-semibold text-gray-900 mb-1">{plan.name}</h3>
                <p className="text-gray-500 text-xs mb-4">{plan.description}</p>
                
                <div className="mb-4">
                  {plan.isPayg ? (
                    <div>
                      <span className="text-3xl font-bold text-gray-900">$0</span>
                      <span className="text-gray-500 text-sm">/month</span>
                      <p className="text-xs text-purple-600 font-medium mt-1">Pay only for what you use</p>
                    </div>
                  ) : (
                    <>
                      <span className="text-3xl font-bold text-gray-900">${plan.price}</span>
                      <span className="text-gray-500 text-sm">{plan.period}</span>
                    </>
                  )}
                </div>

                <ul className="space-y-2 mb-6">
                  {plan.features.map((feature, fidx) => (
                    <li key={fidx} className="flex items-center gap-2 text-xs">
                      <CheckCircle className={`w-4 h-4 flex-shrink-0 ${plan.isPayg ? 'text-purple-500' : 'text-teal-500'}`} />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button 
                  onClick={goToLogin}
                  className={`w-full rounded-full py-3 text-sm font-medium cursor-pointer transition-all ${
                    plan.isPayg
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-900 border-0'
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>

          {/* BYOL Plans */}
          {pricingTab === 'byol' && (
            <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
              {byolPlans.map((plan, idx) => (
                <div 
                  key={idx}
                  className={`relative bg-white border rounded-2xl p-6 ${
                    plan.popular 
                      ? 'border-blue-500 shadow-lg shadow-blue-500/10' 
                      : 'border-gray-200'
                  }`}
                >
                  {plan.popular && (
                    <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-full text-sm font-medium">
                      Most Popular
                    </div>
                  )}
                  
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">{plan.name}</h3>
                  <p className="text-gray-500 text-xs mb-4">{plan.description}</p>
                  
                  <div className="mb-4">
                    <span className="text-3xl font-bold text-gray-900">${plan.price}</span>
                    <span className="text-gray-500 text-sm">{plan.period}</span>
                  </div>

                  <ul className="space-y-2 mb-6">
                    {plan.features.map((feature, fidx) => (
                      <li key={fidx} className="flex items-center gap-2 text-xs">
                        <CheckCircle className="w-4 h-4 flex-shrink-0 text-blue-500" />
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <button 
                    onClick={goToLogin}
                    className={`w-full rounded-full py-3 text-sm font-medium cursor-pointer transition-all ${
                      plan.popular 
                        ? 'bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white border-0' 
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-900 border-0'
                    }`}
                  >
                    {plan.cta}
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Full Service Plans */}
          {pricingTab === 'full' && (
            <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
              {fullServicePlans.map((plan, idx) => (
                <div 
                  key={idx}
                  className={`relative bg-white border rounded-2xl p-6 ${
                    plan.popular 
                      ? 'border-teal-500 shadow-lg shadow-teal-500/10' 
                      : 'border-gray-200'
                  }`}
                >
                  {plan.popular && (
                    <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-full text-sm font-medium">
                      Best Value
                    </div>
                  )}
                  
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">{plan.name}</h3>
                  <p className="text-gray-500 text-xs mb-4">{plan.description}</p>
                  
                  <div className="mb-4">
                    <span className="text-3xl font-bold text-gray-900">${plan.price}</span>
                    <span className="text-gray-500 text-sm">{plan.period}</span>
                  </div>

                  <ul className="space-y-2 mb-6">
                    {plan.features.map((feature, fidx) => (
                      <li key={fidx} className="flex items-center gap-2 text-xs">
                        <CheckCircle className="w-4 h-4 flex-shrink-0 text-teal-500" />
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <button 
                    onClick={goToLogin}
                    className={`w-full rounded-full py-3 text-sm font-medium cursor-pointer transition-all ${
                      plan.popular 
                        ? 'bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white border-0' 
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-900 border-0'
                    }`}
                  >
                    {plan.cta}
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Inbound Plans */}
          {pricingTab === 'inbound' && (
            <>
              <div className="text-center mb-8">
                <p className="text-gray-600">Turn every incoming call into a booked appointment—24/7, even when you're busy.</p>
              </div>
              <div className="grid md:grid-cols-3 gap-6">
                {inboundPlans.map((plan, idx) => (
                  <div 
                    key={idx}
                    className={`bg-white rounded-2xl p-8 border-2 transition-all ${
                      plan.popular 
                        ? 'border-purple-500 shadow-xl shadow-purple-100 scale-105' 
                        : 'border-gray-100 hover:border-purple-200'
                    }`}
                  >
                    {plan.popular && (
                      <span className="inline-block bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold px-3 py-1 rounded-full mb-4">
                        MOST POPULAR
                      </span>
                    )}
                    <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                    <p className="text-gray-500 text-sm mb-4">{plan.description}</p>
                    <div className="flex items-baseline gap-1 mb-6">
                      <span className="text-4xl font-bold text-gray-900">${plan.price}</span>
                      <span className="text-gray-500">{plan.period}</span>
                    </div>
                    <ul className="space-y-3 mb-8">
                      {plan.features.map((feature, fidx) => (
                        <li key={fidx} className="flex items-center gap-3 text-sm text-gray-600">
                          <CheckCircle className="w-5 h-5 text-purple-500 flex-shrink-0" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                    <button 
                      onClick={goToCalendly}
                      className={`w-full py-3 rounded-lg font-medium transition-all ${
                        plan.popular
                          ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:from-purple-600 hover:to-pink-600'
                          : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                      }`}
                    >
                      {plan.cta}
                    </button>
                  </div>
                ))}
              </div>
            </>
          )}

          {pricingTab !== 'inbound' && (
            <p className="text-center text-gray-500 text-sm mt-8">
              Start with Test Drive for $49. No long-term commitment required.
            </p>
          )}
          {pricingTab === 'inbound' && (
            <p className="text-center text-gray-500 text-sm mt-8">
              Start with Inbound Lite for $99/mo. Never miss a customer call again.
            </p>
          )}
          <p className="text-center text-gray-400 text-sm mt-3">
            Need more capacity? <span className="text-cyan-600 font-medium">Upgrade anytime</span> from your dashboard.
          </p>
        </div>
      </section>

      {/* FAQ - Light Gray */}
      <section id="faq" className="bg-gray-50 py-24 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Frequently asked questions</h2>
            <p className="text-gray-600 text-lg">Everything you need to know</p>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, idx) => (
              <div 
                key={idx}
                className="bg-white rounded-xl overflow-hidden shadow-sm"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full flex items-center justify-between p-6 text-left hover:bg-gray-50 transition-colors"
                >
                  <span className="font-medium text-gray-900 pr-8">{faq.question}</span>
                  <ChevronDown className={`w-5 h-5 text-gray-400 flex-shrink-0 transition-transform ${openFaq === idx ? 'rotate-180' : ''}`} />
                </button>
                {openFaq === idx && (
                  <div className="px-6 pb-6 text-gray-600 leading-relaxed">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA - Dark */}
      <section className="bg-[#0B1628] py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Ready to automate your outbound?</h2>
          <p className="text-gray-400 text-lg mb-8 max-w-xl mx-auto">
            Experience the AI voice yourself or book a personalized walkthrough with our team.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button 
              onClick={() => document.getElementById('demo').scrollIntoView({ behavior: 'smooth' })}
              className="bg-white hover:bg-gray-100 text-gray-900 rounded-full px-8 py-6 font-medium border-0 flex items-center gap-2"
            >
              <Phone className="w-5 h-5" />
              Try the AI Voice
            </Button>
            <a 
              href="https://calendly.com/dialgenix" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white rounded-full px-8 py-4 font-medium"
            >
              <Calendar className="w-5 h-5" />
              Book a Live Demo
            </a>
          </div>

          <p className="text-gray-500 text-sm mt-6">
            Book a free demo today
          </p>
        </div>
      </section>

      {/* Support/Contact Section */}
      <section className="bg-gradient-to-b from-[#0f1c32] to-[#0B1628] py-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Need Help? We're Here.
          </h2>
          <p className="text-gray-400 mb-8 max-w-2xl mx-auto">
            Questions about DialGenix? Want to see a live demo? Our team is ready to help you get started.
          </p>
          
          <div className="grid md:grid-cols-3 gap-6">
            {/* Email Support */}
            <a 
              href="mailto:support@dialgenix.ai" 
              className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all group"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Mail className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-white font-semibold mb-2">Email Us</h3>
              <p className="text-cyan-400 group-hover:text-cyan-300 transition-colors">support@dialgenix.ai</p>
            </a>
            
            {/* Phone */}
            <a 
              href="tel:+18885131913" 
              className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all group"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Phone className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-white font-semibold mb-2">Call Us</h3>
              <p className="text-cyan-400 group-hover:text-cyan-300 transition-colors">(888) 513-1913</p>
            </a>
            
            {/* Book a Demo */}
            <button 
              onClick={goToCalendly}
              className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all group cursor-pointer text-left"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Calendar className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-white font-semibold mb-2 text-center">Book a Demo</h3>
              <p className="text-cyan-400 group-hover:text-cyan-300 transition-colors text-center">Free 15-min consultation</p>
            </button>
          </div>
        </div>
      </section>

      {/* Footer - Dark */}
      <footer className="bg-[#0B1628] py-12 px-6 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-teal-500 rounded-lg flex items-center justify-center">
                <Phone className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold text-white">DialGenix.ai</span>
            </div>

            <div className="flex items-center gap-8 text-sm text-gray-400">
              <Link to="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
              <Link to="/terms" className="hover:text-white transition-colors">Terms of Service</Link>
              <a href="tel:+18885131913" className="hover:text-white transition-colors flex items-center gap-1">
                <Phone className="w-3 h-3" />
                (888) 513-1913
              </a>
              <a href="mailto:support@dialgenix.ai" className="hover:text-white transition-colors">Contact</a>
            </div>

            <p className="text-sm text-gray-500">© 2025 DialGenix.ai. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
