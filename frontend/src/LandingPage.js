import { useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Phone, Zap, Calendar, CheckCircle, ArrowRight, Play, 
  Users, Clock, Shield, Headphones, BarChart3,
  ChevronDown, Bot, Target, Menu, X, Upload, Volume2, Pause, Loader2,
  Search, MessageSquare, PhoneCall, Mail, Settings, PhoneForwarded, Mic, Brain, TrendingUp, Star
} from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL + "/api";
const CALENDLY_LINK = "https://calendly.com/dialgenix/15-30min";

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

  const goToPlan = (planId) => {
    localStorage.setItem('selected_plan', planId);
    navigate('/login');
  };

  const scrollToPricing = () => {
    document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' });
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
    {
      number: "04",
      title: "Live Transfers",
      description: "Hot leads get instantly connected to your team. AI detects buying signals and transfers the call in real-time.",
      icon: PhoneForwarded,
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
      id: "byl_starter",
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
      id: "byl_pro",
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
      id: "byl_scale",
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
      id: "discovery_starter",
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
      id: "discovery_pro",
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
      id: "discovery_elite",
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

  // Inbound AI Receptionist Plans - Minutes-based with overage
  const inboundPlans = [
    {
      id: "receptionist_lite",
      name: "Receptionist Lite",
      price: "49",
      period: "/month",
      description: "Solo practices",
      features: [
        "100 minutes included",
        "$0.35/min overage",
        "24/7 AI answering",
        "Calendar booking",
        "Call recordings",
        "SMS confirmations",
        "1 phone number",
      ],
      cta: "Get Started",
      popular: false,
      minutes: 100,
      overage: 0.35,
    },
    {
      id: "receptionist_pro",
      name: "Receptionist Pro",
      price: "99",
      period: "/month",
      description: "Small offices",
      features: [
        "300 minutes included",
        "$0.25/min overage",
        "24/7 AI answering",
        "Calendar booking",
        "Call transcripts",
        "Custom greetings",
        "Appointment reminders",
        "2 phone numbers",
        "+$49/mo: Auto Review Requests",
      ],
      cta: "Get Started",
      popular: true,
      minutes: 300,
      overage: 0.25,
    },
    {
      id: "receptionist_plus",
      name: "Receptionist Plus",
      price: "199",
      period: "/month",
      description: "Busy practices",
      features: [
        "750 minutes included",
        "$0.18/min overage",
        "24/7 AI answering",
        "Calendar booking",
        "Call transcripts",
        "Custom FAQ handling",
        "Priority support",
        "5 phone numbers",
        "+$49/mo: Auto Review Requests",
      ],
      cta: "Get Started",
      popular: false,
      minutes: 750,
      overage: 0.18,
    },
  ];

  const faqs = [
    {
      question: "Is DialGenix.ai compliant for cold calling?",
      answer: "Yes. DialGenix.ai is built to align with TCPA regulations and industry standards. It includes features such as DNC list management, call time restrictions, and proper disclosure protocols. For specific requirements, we recommend consulting your compliance team.",
    },
    {
      question: "Will this sound robotic?",
      answer: "Not at all. We use ElevenLabs' most advanced voice synthesis combined with GPT-5.2 for natural conversations. Plus, our Voice Tuning feature lets you adjust stability, expressiveness, and clarity to sound exactly how you want. Most prospects can't tell they're talking to AI.",
    },
    {
      question: "How accurate is personality detection?",
      answer: "Our DISC detection analyzes word choice, response patterns, and conversation style. In testing, we achieve 85%+ accuracy after just 2-3 exchanges. The AI adapts its communication style in real-time based on detection.",
    },
    {
      question: "Can I customize scripts?",
      answer: "Absolutely. You write the script, set qualification criteria, and define objection handling. The AI follows your playbook while adapting its tone to each buyer's personality type.",
    },
    {
      question: "How does the AI handle inbound calls?",
      answer: "When someone calls your business, our AI answers instantly—24/7. It greets them naturally, asks qualifying questions, answers FAQs about your services, and books appointments directly on your calendar. No hold music, no missed calls.",
    },
    {
      question: "What if someone asks to speak to a human?",
      answer: "The AI immediately offers to schedule a callback or can transfer to a live agent in real-time. During transfers, your team hears the buyer's personality type and sales tips.",
    },
    {
      question: "What if no one answers the transfer?",
      answer: "The AI gracefully handles it by offering to schedule a callback, send information via email, or book a meeting on your calendar. No lead is left hanging.",
    },
    {
      question: "How do I get started?",
      answer: "Book a free demo with our team. We'll show you how DialGenix works and help you set up your first campaign—usually takes about 15 minutes.",
    },
    {
      question: "Is there a free trial or demo available?",
      answer: "While we don't offer a free trial, we do offer live customized demos so you can see DialGenix.ai's platform in action and get all your questions answered based on your specific use case.",
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Announcement Bar */}
      <div className="bg-gradient-to-r from-purple-500 via-cyan-500 to-teal-500 py-2 px-4">
        <p className="text-center text-sm text-white font-medium">
          🧠 NEW: AI Personality Detection — Know your buyer before you speak →
        </p>
      </div>

      {/* Navigation */}
      <nav className="bg-[#0B1628] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-gradient-to-br from-purple-400 to-cyan-500 rounded-lg flex items-center justify-center">
                <Phone className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold text-white">DialGenix.ai</span>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <a href="#personality" className="text-sm text-gray-300 hover:text-white transition-colors">Personality AI</a>
              <a href="#proof" className="text-sm text-gray-300 hover:text-white transition-colors">Results</a>
              <a href="#how-it-works" className="text-sm text-gray-300 hover:text-white transition-colors">How It Works</a>
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
                onClick={scrollToPricing}
                className="rounded-full bg-gradient-to-r from-purple-500 to-cyan-500 hover:from-purple-600 hover:to-cyan-600 text-white px-4 py-2 text-sm cursor-pointer"
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
                    onClick={() => { setMobileMenuOpen(false); scrollToPricing(); }}
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
      <section className="bg-[#0B1628] pt-20 pb-24 px-6 relative overflow-hidden">
        {/* Gradient orb effect */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-gradient-to-r from-purple-500/20 via-cyan-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-5xl mx-auto text-center relative">
          <h1 className="text-5xl md:text-7xl font-bold leading-tight tracking-tight">
            <span className="text-white">Close More Deals with </span>
            <br />
            <span className="bg-gradient-to-r from-purple-400 via-cyan-400 to-teal-400 bg-clip-text text-transparent">AI That Adapts</span>
            <span className="text-white"> to Every Buyer</span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-400 mt-8 max-w-3xl mx-auto leading-relaxed">
            Instantly detect buyer personality and tailor every sales call to convert high-intent leads.
          </p>

          {/* Primary CTA */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10">
            <Button 
              onClick={scrollToPricing}
              className="rounded-full bg-gradient-to-r from-purple-500 to-cyan-500 hover:from-purple-600 hover:to-cyan-600 text-white px-10 py-7 text-lg font-semibold border-0 shadow-lg shadow-purple-500/25"
            >
              Get Started
            </Button>
            <a href="#voice-samples">
              <Button variant="outline" className="rounded-full border-purple-500/50 text-purple-400 hover:bg-purple-500/10 bg-transparent px-8 py-6 text-base">
                <Headphones className="w-4 h-4 mr-2" />
                Listen to a Live Call
              </Button>
            </a>
          </div>

          {/* Personality Animation Hint */}
          <div className="flex items-center justify-center gap-3 mt-10">
            <div className="flex items-center gap-2 px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-full">
              <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
              <span className="text-red-300 text-sm font-medium">D</span>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-500" />
            <div className="flex items-center gap-2 px-4 py-2 bg-yellow-500/20 border border-yellow-500/30 rounded-full">
              <span className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></span>
              <span className="text-yellow-300 text-sm font-medium">I</span>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-500" />
            <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-full">
              <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></span>
              <span className="text-green-300 text-sm font-medium">S</span>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-500" />
            <div className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 border border-blue-500/30 rounded-full">
              <span className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" style={{animationDelay: '0.6s'}}></span>
              <span className="text-blue-300 text-sm font-medium">C</span>
            </div>
          </div>
          <p className="text-gray-500 text-sm mt-3">AI detects personality → adapts in real-time</p>

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

      {/* Section 2: YOUR WEDGE - Why Most Sales Calls Fail - RIGHT AFTER HERO */}
      <section id="personality" className="bg-gradient-to-b from-[#0B1628] to-[#0a0f1a] py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold text-white mt-2 mb-4">
              Why Most Sales Calls Fail
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Your reps follow one script—but every buyer is different.
            </p>
          </div>
          
          <div className="grid lg:grid-cols-2 gap-12 items-start">
            {/* Left - DISC Types */}
            <div>
              <div className="mb-8 p-4 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 rounded-xl border border-emerald-500/30">
                <p className="text-emerald-300 text-lg font-semibold text-center">
                  DialGenix identifies each buyer's personality in real time and adapts your approach to close more deals.
                </p>
              </div>
              <h3 className="text-white text-xl font-semibold mb-6">The 4 Buyer Personalities (DISC)</h3>
              
              <div className="space-y-4">
                {/* Dominant */}
                <div className="p-5 bg-red-500/10 border border-red-500/30 rounded-xl">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 bg-red-500 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-lg">D</span>
                    </div>
                    <div>
                      <h4 className="text-white font-semibold">Dominant</h4>
                      <p className="text-red-300 text-sm">Decisive • Results-driven • Fast</p>
                    </div>
                  </div>
                  <p className="text-gray-400 text-sm mt-2">
                    <span className="text-red-400 font-medium">AI detects:</span> "What's the bottom line?" "ROI?" "Let's move fast"
                  </p>
                  <p className="text-gray-300 text-sm mt-1">
                    <span className="text-white">→ Your team's tip:</span> Be direct, focus on results, don't small talk
                  </p>
                </div>
                
                {/* Influencer */}
                <div className="p-5 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 bg-yellow-500 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-lg">I</span>
                    </div>
                    <div>
                      <h4 className="text-white font-semibold">Influencer</h4>
                      <p className="text-yellow-300 text-sm">Enthusiastic • Creative • Social</p>
                    </div>
                  </div>
                  <p className="text-gray-400 text-sm mt-2">
                    <span className="text-yellow-400 font-medium">AI detects:</span> "That sounds exciting!" "Love it!" "Tell me more"
                  </p>
                  <p className="text-gray-300 text-sm mt-1">
                    <span className="text-white">→ Your team's tip:</span> Be energetic, build rapport, share success stories
                  </p>
                </div>
                
                {/* Steady */}
                <div className="p-5 bg-green-500/10 border border-green-500/30 rounded-xl">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-lg">S</span>
                    </div>
                    <div>
                      <h4 className="text-white font-semibold">Steady</h4>
                      <p className="text-green-300 text-sm">Patient • Supportive • Trust-focused</p>
                    </div>
                  </div>
                  <p className="text-gray-400 text-sm mt-2">
                    <span className="text-green-400 font-medium">AI detects:</span> "Let me think about it" "Need to discuss with team" "Is it reliable?"
                  </p>
                  <p className="text-gray-300 text-sm mt-1">
                    <span className="text-white">→ Your team's tip:</span> Be patient, don't pressure, emphasize support
                  </p>
                </div>
                
                {/* Conscientious */}
                <div className="p-5 bg-blue-500/10 border border-blue-500/30 rounded-xl">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-lg">C</span>
                    </div>
                    <div>
                      <h4 className="text-white font-semibold">Conscientious</h4>
                      <p className="text-blue-300 text-sm">Analytical • Detail-oriented • Precise</p>
                    </div>
                  </div>
                  <p className="text-gray-400 text-sm mt-2">
                    <span className="text-blue-400 font-medium">AI detects:</span> "How exactly does it work?" "Show me the data" "What are the specifics?"
                  </p>
                  <p className="text-gray-300 text-sm mt-1">
                    <span className="text-white">→ Your team's tip:</span> Provide data, be thorough, don't exaggerate
                  </p>
                </div>
              </div>
            </div>
            
            {/* Right - How It Works */}
            <div>
              <div className="bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-8">
                <h3 className="text-white text-xl font-semibold mb-6 text-center">How It Works</h3>
                
                <div className="space-y-6">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold">1</span>
                    </div>
                    <div>
                      <h4 className="text-white font-semibold">AI Listens & Analyzes</h4>
                      <p className="text-gray-400 text-sm">During the first 2-3 exchanges, AI analyzes word choice, pace, and conversation style</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold">2</span>
                    </div>
                    <div>
                      <h4 className="text-white font-semibold">Detects Personality Type</h4>
                      <p className="text-gray-400 text-sm">AI identifies signals and classifies the buyer as D, I, S, or C</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold">3</span>
                    </div>
                    <div>
                      <h4 className="text-white font-semibold">Adapts in Real-Time</h4>
                      <p className="text-gray-400 text-sm">AI adjusts its communication style to match—building better rapport</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold">4</span>
                    </div>
                    <div>
                      <h4 className="text-white font-semibold">Shares Intel on Transfer</h4>
                      <p className="text-gray-400 text-sm">When transferring, your team hears the personality type + sales tips</p>
                    </div>
                  </div>
                </div>
                
                {/* Transfer Whisper Example */}
                <div className="mt-6 p-4 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-lg border border-purple-500/30">
                  <p className="text-purple-300 text-sm font-medium mb-2">📞 What your team hears on transfer:</p>
                  <p className="text-white text-sm italic">
                    "Incoming transfer: John Smith from Acme Corp. <span className="text-purple-300">Personality type: Dominant.</span> Tip: Be direct, focus on ROI, don't small talk."
                  </p>
                </div>
                
                {/* Call History Preview */}
                <div className="mt-6 p-4 bg-white/5 rounded-lg border border-white/10">
                  <p className="text-gray-400 text-sm font-medium mb-3">📊 See it in Call History:</p>
                  <div className="flex items-center gap-3 bg-[#0B1628] rounded-lg p-3">
                    <div className="px-3 py-1 bg-red-500/20 border border-red-500/30 rounded-full">
                      <span className="text-red-300 text-xs font-medium">D - Dominant</span>
                    </div>
                    <span className="text-gray-400 text-sm">Confidence: 85%</span>
                  </div>
                </div>
              </div>
              
              {/* Benefits */}
              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="p-4 bg-white/5 rounded-xl border border-white/10 text-center">
                  <p className="text-3xl font-bold text-purple-400">40%</p>
                  <p className="text-gray-400 text-sm">Higher close rate with personality-matched approach</p>
                </div>
                <div className="p-4 bg-white/5 rounded-xl border border-white/10 text-center">
                  <p className="text-3xl font-bold text-purple-400">2x</p>
                  <p className="text-gray-400 text-sm">Faster rapport building with the right style</p>
                </div>
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
              onClick={scrollToPricing}
              className="rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white px-10 py-6 text-lg font-medium border-0 inline-flex items-center cursor-pointer transition-all"
            >
              Get Started
              <ArrowRight className="w-5 h-5 ml-2" />
            </button>
            <p className="text-gray-500 mt-4">See our plans and start converting leads today.</p>
            <p className="text-cyan-400 text-sm mt-2 flex items-center justify-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Questions about setup? Chat with us anytime—we'll help you get live in minutes.
            </p>
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
              onClick={() => {
                document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' });
                setTimeout(() => setPricingTab('byol'), 300);
              }}
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
                Scale your outreach with AI that <span className="bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">calls, qualifies, books meetings, and seamlessly hands off to your team</span>
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

      {/* How It Works - Simple System */}
      <section id="how-it-works" className="bg-gray-50 py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-cyan-600 text-sm font-medium uppercase tracking-wide">Simple Process</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mt-2 mb-4">How It Works</h2>
            <p className="text-gray-600 text-lg max-w-2xl mx-auto">
              Four steps to automate your sales outreach
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div key={idx} className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                  <span className="text-sm font-bold text-cyan-600">{step.number}</span>
                  <h3 className="text-xl font-semibold text-gray-900 mt-1 mb-3">{step.title}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">{step.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* BENEFITS / OUTCOMES Section */}
      <section className="bg-white py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Why It's Better</h2>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="flex items-start gap-4 p-6 bg-emerald-50 rounded-2xl border border-emerald-100">
              <div className="w-12 h-12 bg-emerald-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <Calendar className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Book More Meetings Automatically</h3>
                <p className="text-gray-600">AI qualifies leads and books directly to your calendar—you just show up and close.</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4 p-6 bg-cyan-50 rounded-2xl border border-cyan-100">
              <div className="w-12 h-12 bg-cyan-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Respond to Every Lead Instantly</h3>
                <p className="text-gray-600">No more 5-minute delays. AI responds in seconds—when interest is at its peak.</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4 p-6 bg-purple-50 rounded-2xl border border-purple-100">
              <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Reduce Workload on Your Team</h3>
                <p className="text-gray-600">Let AI handle the grunt work. Your reps focus on high-value conversations only.</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4 p-6 bg-orange-50 rounded-2xl border border-orange-100">
              <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <Target className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Never Miss High-Intent Prospects</h3>
                <p className="text-gray-600">24/7 coverage means every lead gets immediate attention—even at 2am.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* VOICE SAMPLES Section - Moved Up */}
      <section id="voice-samples" className="bg-gradient-to-b from-[#0B1628] to-[#0f1c32] py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <span className="text-purple-400 text-sm font-medium uppercase tracking-wide">Voice Technology</span>
            <h2 className="text-3xl md:text-4xl font-bold text-white mt-2 mb-4">
              AI That Sounds Human—Not Robotic
            </h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Hear the difference. Our AI agents have natural energy, warmth, and conversation flow.
            </p>
          </div>
          
          {/* Call Yourself Demo - Prominent */}
          <div className="mb-12">
            <CallYourselfHero />
          </div>
          
          {/* Voice Tuning Highlight */}
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-2xl font-bold text-white mb-6">Fine-Tune Every Aspect</h3>
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Volume2 className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold">Stability Control</h4>
                    <p className="text-gray-400 text-sm">Lower = more expressive. Higher = more consistent.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Zap className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold">Expressiveness</h4>
                    <p className="text-gray-400 text-sm">Add emotion and energy for enthusiastic calls.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Mic className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold">Clone Your Voice</h4>
                    <p className="text-gray-400 text-sm">Upload samples to create AI that sounds like you.</p>
                  </div>
                </div>
              </div>
              
              {/* Quick Presets */}
              <div className="mt-8">
                <p className="text-gray-400 text-sm mb-3">One-Click Presets:</p>
                <div className="flex flex-wrap gap-2">
                  <span className="px-4 py-2 bg-purple-500/20 border border-purple-500/30 rounded-full text-purple-300 text-sm">🎭 Natural</span>
                  <span className="px-4 py-2 bg-white/10 border border-white/20 rounded-full text-gray-300 text-sm">💼 Professional</span>
                  <span className="px-4 py-2 bg-white/10 border border-white/20 rounded-full text-gray-300 text-sm">⚡ Energetic</span>
                  <span className="px-4 py-2 bg-white/10 border border-white/20 rounded-full text-gray-300 text-sm">🧘 Calm</span>
                </div>
              </div>
            </div>
            
            {/* Mock Voice Tuning UI */}
            <div className="bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-8">
              <h4 className="text-white text-lg font-semibold mb-6 text-center">Voice Tuning Controls</h4>
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-300 text-sm">Stability</span>
                    <span className="text-purple-400 text-sm">30%</span>
                  </div>
                  <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full w-[30%] bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Expressive</span>
                    <span>Consistent</span>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-300 text-sm">Clarity</span>
                    <span className="text-purple-400 text-sm">75%</span>
                  </div>
                  <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full w-[75%] bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-300 text-sm">Expressiveness</span>
                    <span className="text-purple-400 text-sm">50%</span>
                  </div>
                  <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full w-[50%] bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                  </div>
                </div>
              </div>
              <div className="mt-6 p-4 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-lg border border-purple-500/30">
                <p className="text-purple-300 text-sm text-center">
                  💡 Tip: Lower stability for more human-like conversations
                </p>
              </div>
            </div>
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
                  <p className="text-gray-400 mb-4">When a prospect shows interest or curiosity, DialGenix takes action in real time:</p>
                  
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-orange-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-orange-400 text-xs font-bold">1</span>
                      </div>
                      <p className="text-gray-300">Detects interest and curiosity automatically</p>
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
              
              {/* Setup Instructions */}
              <div className="mt-6 p-5 bg-white/5 rounded-lg border border-white/10">
                <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <Settings className="w-4 h-4 text-orange-400" />
                  Quick Setup
                </h4>
                <ol className="text-gray-400 text-sm space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-orange-400 font-bold">1.</span>
                    Go to <span className="text-white">Agents</span> page
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-400 font-bold">2.</span>
                    Edit your agent (or create new)
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-400 font-bold">3.</span>
                    Scroll to <span className="text-white">"Live Transfer"</span> section
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-400 font-bold">4.</span>
                    Toggle it <span className="text-green-400">ON</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-400 font-bold">5.</span>
                    Enter your transfer phone number
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-400 font-bold">6.</span>
                    Save — <span className="text-white">that's it!</span>
                  </li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Voicemail Drop Section */}
      <section className="bg-gradient-to-b from-[#0B1628] to-[#0a0f1a] py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1 bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-8">
              <h3 className="text-white text-xl font-semibold mb-6 text-center">Why VM Drop Matters</h3>
              
              <div className="space-y-4">
                <div className="flex items-center gap-4 p-4 bg-violet-500/10 rounded-lg border border-violet-500/20">
                  <div className="w-12 h-12 bg-violet-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-violet-400 font-bold text-lg">80%</span>
                  </div>
                  <p className="text-white">of sales calls go to <span className="text-violet-400 font-semibold">voicemail</span></p>
                </div>
                
                <div className="flex items-center gap-4 p-4 bg-violet-500/10 rounded-lg border border-violet-500/20">
                  <Clock className="w-8 h-8 text-violet-400 flex-shrink-0" />
                  <p className="text-white">Save <span className="text-violet-400 font-semibold">hours daily</span> vs manual messages</p>
                </div>
                
                <div className="flex items-center gap-4 p-4 bg-violet-500/10 rounded-lg border border-violet-500/20">
                  <Mic className="w-8 h-8 text-violet-400 flex-shrink-0" />
                  <p className="text-white">Perfect, <span className="text-violet-400 font-semibold">consistent delivery</span> every time</p>
                </div>
                
                <div className="flex items-center gap-4 p-4 bg-violet-500/10 rounded-lg border border-violet-500/20">
                  <TrendingUp className="w-8 h-8 text-violet-400 flex-shrink-0" />
                  <p className="text-white">Increase <span className="text-violet-400 font-semibold">callback rates by 22%</span></p>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-gradient-to-r from-violet-500/20 to-purple-500/20 rounded-lg border border-violet-500/30">
                <p className="text-violet-300 text-sm text-center font-medium">
                  📬 The Result: Every voicemail gets a professional, compelling message—automatically.
                </p>
              </div>
            </div>
            
            <div className="order-1 lg:order-2">
              <span className="text-violet-400 text-sm font-medium uppercase tracking-wide">Voicemail Drop</span>
              <h2 className="text-3xl md:text-4xl font-bold text-white mt-2 mb-6" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                Never Waste Another Voicemail
              </h2>
              <p className="text-gray-400 text-lg mb-8">
                80% of calls go to voicemail. Make every single one count with AI-powered voicemail drops.
              </p>
              
              <div className="space-y-6">
                <div>
                  <h4 className="text-white font-semibold text-lg mb-3">How It Works</h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-violet-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-violet-400 text-xs font-bold">1</span>
                      </div>
                      <p className="text-gray-300">AI detects voicemail pickup (beep detection)</p>
                    </div>
                    
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-violet-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-violet-400 text-xs font-bold">2</span>
                      </div>
                      <p className="text-gray-300">Instantly drops your pre-recorded or AI-generated message</p>
                    </div>
                    
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-violet-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-violet-400 text-xs font-bold">3</span>
                      </div>
                      <p className="text-gray-300">Moves to next call immediately—<span className="text-white font-medium">zero wait time</span></p>
                    </div>
                    
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-violet-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-violet-400 text-xs font-bold">4</span>
                      </div>
                      <p className="text-gray-300">Prospect calls back → AI handles inbound instantly</p>
                    </div>
                  </div>
                </div>
                
                <div className="p-5 bg-white/5 rounded-lg border border-white/10">
                  <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-violet-400" />
                    VM Drop Options
                  </h4>
                  <ul className="text-gray-400 text-sm space-y-2">
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
                      <span><span className="text-white">Pre-recorded:</span> Upload your own voice message</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
                      <span><span className="text-white">AI-generated:</span> Dynamic messages with prospect's name</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
                      <span><span className="text-white">Cloned voice:</span> Use your voice clone for personalization</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SMS Review Requests Section - For Any Business */}
      <section className="bg-gradient-to-b from-[#0a0f1a] to-[#0d1321] py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Content */}
            <div>
              <span className="inline-flex items-center gap-2 text-amber-400 text-sm font-medium uppercase tracking-wide mb-4">
                <Star className="w-4 h-4" />
                Reputation Management
              </span>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                Turn Happy Customers Into
                <span className="text-amber-400"> 5-Star Reviews</span>
              </h2>
              <p className="text-gray-400 text-lg mb-8">
                After every successful interaction, automatically send personalized SMS or email review requests. 
                Build your online reputation while you focus on growing your business.
              </p>
              
              <div className="space-y-4 mb-8">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-amber-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <MessageSquare className="w-4 h-4 text-amber-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold">Automated Follow-Up Messages</h4>
                    <p className="text-gray-400 text-sm">Send review requests via SMS or email after calls, meetings, or purchases</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-emerald-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Star className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold">Direct Review Links</h4>
                    <p className="text-gray-400 text-sm">One-tap Google, Yelp, or custom review links make it effortless for customers</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-cyan-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Users className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold">Bulk Outreach to Past Customers</h4>
                    <p className="text-gray-400 text-sm">Upload a CSV and request reviews from your entire customer base in minutes</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
                <p className="text-amber-200 text-sm">
                  <span className="font-semibold">💡 Pro Tip:</span> Businesses with 50+ Google reviews see 
                  <span className="text-amber-400 font-semibold"> 35% more clicks</span> than competitors. 
                  Start building your reviews today.
                </p>
              </div>
            </div>
            
            {/* Right: Mock SMS Preview */}
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-amber-500/20 to-emerald-500/20 blur-3xl opacity-30"></div>
              <div className="relative bg-[#1a1f2e] rounded-2xl border border-white/10 p-6 max-w-sm mx-auto">
                {/* Phone Frame */}
                <div className="bg-gray-900 rounded-xl p-4 shadow-2xl">
                  <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-700">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs font-bold">AB</span>
                      </div>
                      <div>
                        <p className="text-white text-sm font-medium">Acme Business</p>
                        <p className="text-gray-500 text-xs">SMS • Just now</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="bg-blue-600 text-white text-sm p-3 rounded-2xl rounded-tl-sm max-w-[85%]">
                      <p>Hi John! 👋</p>
                      <p className="mt-1">Thanks for choosing Acme Business! We hope everything went great today.</p>
                    </div>
                    
                    <div className="bg-blue-600 text-white text-sm p-3 rounded-2xl rounded-tl-sm max-w-[85%]">
                      <p>Would you take 30 seconds to share your experience? Your feedback helps others find us!</p>
                      <p className="mt-2 text-blue-200 underline">→ Leave a Review</p>
                    </div>
                    
                    <div className="bg-gray-700 text-white text-sm p-3 rounded-2xl rounded-tr-sm max-w-[85%] ml-auto">
                      <p>Absolutely! Great service as always. Done! ⭐⭐⭐⭐⭐</p>
                    </div>
                  </div>
                </div>
                
                {/* Stats Badge */}
                <div className="absolute -bottom-4 -right-4 bg-gradient-to-r from-amber-500 to-orange-500 text-white px-4 py-2 rounded-full text-sm font-semibold shadow-lg">
                  +47 reviews this month
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 3: PROOF - Make It Real */}
      <section id="proof" className="bg-[#0a0f1a] py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-emerald-400 text-sm font-medium uppercase tracking-wide">Results</span>
            <h2 className="text-3xl md:text-4xl font-bold text-white mt-2 mb-4">
              Real Results, Real Numbers
            </h2>
          </div>
          
          {/* Metrics */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="text-center p-8 bg-gradient-to-b from-emerald-500/10 to-transparent border border-emerald-500/20 rounded-2xl">
              <p className="text-5xl font-bold text-emerald-400 mb-2">+32%</p>
              <p className="text-white font-semibold mb-1">Booked Calls</p>
              <p className="text-gray-400 text-sm">More meetings on your calendar</p>
            </div>
            <div className="text-center p-8 bg-gradient-to-b from-purple-500/10 to-transparent border border-purple-500/20 rounded-2xl">
              <p className="text-5xl font-bold text-purple-400 mb-2">+21%</p>
              <p className="text-white font-semibold mb-1">Conversion Rate</p>
              <p className="text-gray-400 text-sm">With personality-matched approach</p>
            </div>
            <div className="text-center p-8 bg-gradient-to-b from-cyan-500/10 to-transparent border border-cyan-500/20 rounded-2xl">
              <p className="text-5xl font-bold text-cyan-400 mb-2">0</p>
              <p className="text-white font-semibold mb-1">Missed Inbound Leads</p>
              <p className="text-gray-400 text-sm">24/7 AI answering</p>
            </div>
          </div>
          
          {/* Voice Demo */}
          <div className="mb-16">
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-white mb-2">Hear the Difference</h3>
              <p className="text-gray-400">Before vs After personality adaptation</p>
            </div>
            <CallYourselfHero />
          </div>
          
          {/* Testimonials */}
          <div className="grid md:grid-cols-2 gap-8">
            <div className="p-6 bg-white/5 border border-white/10 rounded-2xl">
              <p className="text-gray-300 text-lg mb-4 italic">
                "We closed deals we would've missed. The personality detection is a game-changer—our team knows exactly how to approach each prospect before they even pick up."
              </p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold">S</span>
                </div>
                <div>
                  <p className="text-white font-semibold">Sales Director</p>
                  <p className="text-gray-400 text-sm">B2B SaaS Company</p>
                </div>
              </div>
            </div>
            <div className="p-6 bg-white/5 border border-white/10 rounded-2xl">
              <p className="text-gray-300 text-lg mb-4 italic">
                "Finally, an AI that doesn't sound robotic. The voice tuning and live transfers have transformed our inbound lead response. We're booking 40% more demos."
              </p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold">V</span>
                </div>
                <div>
                  <p className="text-white font-semibold">VP of Growth</p>
                  <p className="text-gray-400 text-sm">Lead Generation Agency</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 4: HOW IT WORKS - Simplified */}
      <section id="how-it-works" className="bg-white py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-gray-600 text-lg">Stupid simple. Seriously.</p>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Phone className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Answers or Calls</h3>
              <p className="text-gray-600 text-sm">Inbound or outbound—your AI is ready</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Detects Personality</h3>
              <p className="text-gray-600 text-sm">D, I, S, or C—identified in seconds</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Zap className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Adapts Tone + Script</h3>
              <p className="text-gray-600 text-sm">Communication style shifts in real-time</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Calendar className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Books / Closes / Transfers</h3>
              <p className="text-gray-600 text-sm">Your outcome, automatically</p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 5: USE CASES - Grouped by Outcomes */}
      <section className="bg-gray-50 py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Built For</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Sales Teams */}
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
              <div className="w-14 h-14 bg-purple-100 rounded-2xl flex items-center justify-center mb-6">
                <BarChart3 className="w-7 h-7 text-purple-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">For Sales Teams</h3>
              <ul className="space-y-3 text-gray-600">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  Increase close rates with personality insights
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  Better call handoffs with buyer intel
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  Never miss a hot lead transfer
                </li>
              </ul>
            </div>
            
            {/* Agencies */}
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
              <div className="w-14 h-14 bg-cyan-100 rounded-2xl flex items-center justify-center mb-6">
                <Users className="w-7 h-7 text-cyan-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">For Agencies</h3>
              <ul className="space-y-3 text-gray-600">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  Scale outbound without hiring
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  White-label AI agents for clients
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  Consistent quality across campaigns
                </li>
              </ul>
            </div>
            
            {/* Local Businesses */}
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
              <div className="w-14 h-14 bg-orange-100 rounded-2xl flex items-center justify-center mb-6">
                <Headphones className="w-7 h-7 text-orange-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">For Local Businesses</h3>
              <ul className="space-y-3 text-gray-600">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  Capture missed calls automatically
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  24/7 booking without staff
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  Professional voice for your brand
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Section 6: PRODUCT LAYER - Features as Outcomes */}
      <section className="bg-white py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">What You Can Do</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="flex items-start gap-4 p-6 bg-gray-50 rounded-2xl">
              <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-1">Build high-converting call flows</h3>
                <p className="text-gray-600 text-sm">Custom scripts, objection handling, and personality-adapted responses</p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-6 bg-gray-50 rounded-2xl">
              <div className="w-12 h-12 bg-cyan-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <Target className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-1">Run outbound campaigns at scale</h3>
                <p className="text-gray-600 text-sm">Hundreds of calls daily with consistent quality</p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-6 bg-gray-50 rounded-2xl">
              <div className="w-12 h-12 bg-emerald-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-1">Track what actually closes</h3>
                <p className="text-gray-600 text-sm">Call analytics, personality insights, and conversion data</p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-6 bg-gray-50 rounded-2xl">
              <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center flex-shrink-0">
                <PhoneForwarded className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-1">Transfer hot leads instantly</h3>
                <p className="text-gray-600 text-sm">Live transfers with personality intel for your team</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 7: TRUST LAYER */}
      <section className="bg-gray-50 py-16 px-6 border-t border-gray-200">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-gray-500 text-sm uppercase tracking-wide">Trusted & Integrated</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <p className="text-gray-400 text-sm mb-3">Integrations</p>
              <div className="flex justify-center gap-4 flex-wrap">
                <span className="px-3 py-1 bg-white rounded-full text-gray-600 text-sm border">Calendly</span>
                <span className="px-3 py-1 bg-white rounded-full text-gray-600 text-sm border">Twilio</span>
                <span className="px-3 py-1 bg-white rounded-full text-gray-600 text-sm border">Stripe</span>
              </div>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-3">Powered By</p>
              <div className="flex justify-center gap-4 flex-wrap">
                <span className="px-3 py-1 bg-white rounded-full text-gray-600 text-sm border">GPT-5.2</span>
                <span className="px-3 py-1 bg-white rounded-full text-gray-600 text-sm border">ElevenLabs</span>
              </div>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-3">Security</p>
              <div className="flex justify-center gap-4 flex-wrap">
                <span className="px-3 py-1 bg-white rounded-full text-gray-600 text-sm border">SOC 2</span>
                <span className="px-3 py-1 bg-white rounded-full text-gray-600 text-sm border">GDPR</span>
                <span className="px-3 py-1 bg-white rounded-full text-gray-600 text-sm border">Encrypted</span>
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
                📞 AI Receptionist
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

          {/* Entry Plans (shown on outbound tabs only) */}
          {(pricingTab === 'byol' || pricingTab === 'full') && (
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
                  onClick={() => plan.isPayg ? goToLogin() : goToPlan(plan.id || plan.name)}
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
          )}

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
                    onClick={() => goToPlan(plan.id)}
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
                    onClick={() => goToPlan(plan.id)}
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
                <p className="text-gray-600">Perfect for dentists, clinics, salons & service businesses. Never miss a call—AI answers 24/7.</p>
                <p className="text-purple-600 text-sm mt-2 font-medium">Pay only for what you use. Unused minutes roll over.</p>
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
                      onClick={() => goToPlan(plan.id)}
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
              Start with Receptionist Lite for $49/mo. Never miss a patient or customer call again.
            </p>
          )}
          <p className="text-center text-gray-400 text-sm mt-3">
            Need more capacity? <span className="text-cyan-600 font-medium">Upgrade anytime</span> from your dashboard.
          </p>
          <p className="text-center text-cyan-600 text-sm mt-4 flex items-center justify-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Questions about setup? Chat with us anytime—we'll help you get live in minutes.
          </p>
        </div>
      </section>

      {/* SETUP + EASE Section */}
      <section className="bg-gradient-to-b from-gray-50 to-white py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <span className="text-emerald-600 text-sm font-medium uppercase tracking-wide">Easy Onboarding</span>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mt-2 mb-4">
            Get Started in Minutes
          </h2>
          <p className="text-gray-600 text-lg mb-12 max-w-2xl mx-auto">
            No technical setup required. We guide you every step of the way.
          </p>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
              <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-7 h-7 text-emerald-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Technical Setup</h3>
              <p className="text-gray-600 text-sm">Connect in a few clicks. No coding, no developers needed.</p>
            </div>
            
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
              <div className="w-14 h-14 bg-cyan-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Users className="w-7 h-7 text-cyan-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Fully Guided Onboarding</h3>
              <p className="text-gray-600 text-sm">Our team walks you through setup and optimization.</p>
            </div>
            
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
              <div className="w-14 h-14 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="w-7 h-7 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Chat Support Anytime</h3>
              <p className="text-gray-600 text-sm">Questions? Our team responds in minutes, not days.</p>
            </div>
          </div>
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

      {/* Section 8: FINAL CTA with Urgency */}
      <section className="bg-[#0B1628] py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">
            Start Converting More Calls This Week
          </h2>
          <p className="text-gray-400 text-lg mb-8 max-w-xl mx-auto">
            Join the teams already closing more deals with personality-matched AI.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button 
              onClick={scrollToPricing}
              className="bg-gradient-to-r from-purple-500 to-cyan-500 hover:from-purple-600 hover:to-cyan-600 text-white rounded-full px-10 py-7 text-lg font-semibold border-0 flex items-center gap-2 shadow-lg shadow-purple-500/25"
            >
              View Plans
            </Button>
            <Button 
              onClick={() => window.open(CALENDLY_LINK, '_blank')}
              variant="outline"
              className="border-white/30 text-white hover:bg-white/10 rounded-full px-8 py-6 font-medium flex items-center gap-2 bg-transparent"
            >
              <Calendar className="w-5 h-5" />
              Book Demo
            </Button>
          </div>

          <p className="text-emerald-400 text-sm mt-8 font-medium">
            ⚡ Start converting more calls this week
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

            <div className="flex items-center gap-6 text-sm text-gray-400 flex-wrap justify-center">
              <Link to="/ai-cold-calling" className="hover:text-white transition-colors">AI Cold Calling</Link>
              <Link to="/voice-ai-sales" className="hover:text-white transition-colors">Voice AI Sales</Link>
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
