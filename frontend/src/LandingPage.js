import { useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Phone, Zap, Calendar, CheckCircle, ArrowRight, Play, 
  Users, Clock, Shield, Headphones, BarChart3,
  ChevronDown, Bot, Target, Menu, X, Upload, Volume2, Pause, Loader2
} from "lucide-react";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

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
      const response = await axios.get(`${API}/demo/narration/${stepId}`);
      const { audio_url } = response.data;
      
      if (audioRef.current) {
        audioRef.current.src = audio_url;
        audioRef.current.play();
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
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  );
};

const LandingPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [openFaq, setOpenFaq] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const goToLogin = () => {
    navigate('/login');
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
      description: "Find businesses with buying intent through web search and social media monitoring.",
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
      name: "Starter",
      price: "199",
      period: "/month",
      description: "Perfect for getting started",
      features: [
        "250 leads/month",
        "250 AI calls/month",
        "7-day call recordings",
        "CSV export",
        "GPT-powered search",
        "1 user",
      ],
      cta: "Start Free Trial",
      popular: false,
    },
    {
      name: "Professional",
      price: "399",
      period: "/month", 
      description: "For growing sales teams",
      features: [
        "1,000 leads/month",
        "1,000 AI calls/month",
        "Call transcripts",
        "30-day recordings",
        "Auto calendar booking",
        "API access",
        "5 users",
      ],
      cta: "Start Free Trial",
      popular: true,
    },
    {
      name: "Unlimited",
      price: "699",
      period: "/month",
      description: "Scale without limits",
      features: [
        "5,000 leads/month",
        "Unlimited AI calls",
        "90-day recordings",
        "Priority support",
        "5 team seats",
        "Dedicated manager",
      ],
      cta: "Start Free Trial",
      popular: false,
    },
  ];

  const faqs = [
    {
      question: "How does the AI make phone calls?",
      answer: "Our AI uses advanced speech synthesis and natural language processing to have real conversations. It sounds natural, handles objections, and knows when to hand off to a human.",
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
      question: "Is there a free trial?",
      answer: "Yes! Start with 15 free minutes of AI calling — no credit card required. See results before committing.",
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Announcement Bar */}
      <div className="bg-gradient-to-r from-cyan-500 via-teal-500 to-emerald-500 py-2 px-4">
        <p className="text-center text-sm text-white font-medium">
          Early Access Now Open — Limited spots available for founding customers →
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
                onClick={goToLogin}
                className="rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white px-4 py-2 text-sm cursor-pointer"
              >
                Get started free
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
                    onClick={() => { setMobileMenuOpen(false); goToLogin(); }}
                    className="w-full rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white px-4 py-3 text-sm text-center cursor-pointer"
                  >
                    Get started free
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
            Stop wasting time on manual dialing. Let our AI agents find leads, have natural real human-like AI conversations to qualify them, and book meetings for you—on autopilot.
          </p>

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

          {/* Trust logos */}
          <div className="mt-20">
            <p className="text-sm text-gray-500 mb-6">Powered by enterprise-grade technology</p>
            <div className="flex items-center justify-center gap-12">
              <span className="text-gray-500 font-semibold text-lg">twilio</span>
              <span className="text-gray-500 font-semibold text-lg">OpenAI</span>
              <span className="text-gray-500 font-semibold text-lg">Calendly</span>
            </div>
          </div>
        </div>
      </section>

      {/* Product Demo Section */}
      <section id="demo" className="bg-gradient-to-b from-[#0B1628] to-[#0a0f1a] py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
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
                <div className="bg-gradient-to-br from-cyan-500/10 to-teal-500/10 rounded-2xl p-3 border border-cyan-500/20">
                  <img 
                    src="https://voice-dialer-staging.preview.emergentagent.com/demo-funnel.png" 
                    alt="Sales Funnel Dashboard"
                    className="rounded-xl shadow-2xl w-full"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.parentElement.innerHTML = '<div class="bg-gray-800 rounded-xl p-12 text-center"><p class="text-gray-400">Sales Funnel Preview</p><p class="text-gray-500 text-sm mt-2">Track leads through New → Contacted → Qualified → Booked</p></div>';
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Screenshot 2: Lead Discovery */}
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <div className="bg-gradient-to-br from-cyan-500/10 to-teal-500/10 rounded-2xl p-3 border border-cyan-500/20">
                  <img 
                    src="https://voice-dialer-staging.preview.emergentagent.com/demo-leads.png" 
                    alt="AI Lead Discovery"
                    className="rounded-xl shadow-2xl w-full"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.parentElement.innerHTML = '<div class="bg-gray-800 rounded-xl p-12 text-center"><p class="text-gray-400">Lead Discovery Preview</p><p class="text-gray-500 text-sm mt-2">AI finds businesses searching for your services</p></div>';
                    }}
                  />
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
                <div className="bg-gradient-to-br from-cyan-500/10 to-teal-500/10 rounded-2xl p-3 border border-cyan-500/20">
                  <img 
                    src="https://voice-dialer-staging.preview.emergentagent.com/demo-calls.png" 
                    alt="Call History & Recordings"
                    className="rounded-xl shadow-2xl w-full"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.parentElement.innerHTML = '<div class="bg-gray-800 rounded-xl p-12 text-center"><p class="text-gray-400">Call History Preview</p><p class="text-gray-500 text-sm mt-2">View recordings, transcripts, and qualification results</p></div>';
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* CTA after demo */}
          <div className="text-center mt-20">
            <button 
              onClick={goToLogin}
              className="rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white px-10 py-6 text-lg font-medium border-0 inline-flex items-center cursor-pointer transition-all"
            >
              Start Free Trial
              <ArrowRight className="w-5 h-5 ml-2" />
            </button>
            <p className="text-gray-500 mt-4">15 free minutes of AI calling. No credit card required.</p>
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
                  Upload your CSV with phone numbers and let our AI call them all. <span className="text-cyan-400 font-medium">Unlimited uploads</span> starting at $349/mo.
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
                    desc: "Connect to HubSpot, Salesforce, or your existing tools via API" 
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
              { metric: "Monthly Cost", ai: "$499-999", human: "$12,000+" },
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

      {/* Pricing - White */}
      <section id="pricing" className="bg-white py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Simple, transparent pricing</h2>
            <p className="text-gray-600 text-lg">Start free. Scale as you grow. Cancel anytime.</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
            {pricingPlans.map((plan, idx) => (
              <div 
                key={idx}
                className={`relative bg-white border rounded-2xl p-6 ${
                  plan.popular 
                    ? 'border-teal-500 shadow-lg shadow-teal-500/10' 
                    : plan.isPayg
                    ? 'border-purple-300 shadow-md shadow-purple-500/10'
                    : 'border-gray-200'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-full text-sm font-medium">
                    Most Popular
                  </div>
                )}
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
                      <span className="text-3xl font-bold text-gray-900">{plan.price === "Custom" ? "" : "$"}{plan.price}</span>
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
                  className={`w-full rounded-full py-5 text-sm font-medium cursor-pointer transition-all ${
                    plan.popular 
                      ? 'bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white border-0' 
                      : plan.isPayg
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-900 border-0'
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>

          <p className="text-center text-gray-500 text-sm mt-8">
            Start free with 15 minutes of AI calling. No credit card required.
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
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Need more help?</h2>
          <p className="text-gray-400 text-lg mb-8 max-w-xl mx-auto">
            Ready to automate your outbound? Get a personalized demo and see DialGenix.ai in action.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
            <Input
              type="email"
              placeholder="Enter your work email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="bg-white/10 border-white/20 text-white placeholder:text-gray-500 rounded-full px-6 py-6 flex-1 focus:ring-teal-500"
            />
            <Button type="submit" className="bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white rounded-full px-8 py-6 font-medium border-0">
              Get a demo
            </Button>
          </form>

          <p className="text-gray-500 text-sm mt-6">
            15 free minutes • No credit card required
          </p>
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
              <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
            </div>

            <p className="text-sm text-gray-500">© 2025 DialGenix.ai. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
