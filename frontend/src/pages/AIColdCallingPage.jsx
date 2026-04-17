import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { 
  Phone, Zap, Calendar, CheckCircle, ArrowRight, 
  Bot, Target, Clock, Shield, BarChart3, Users,
  PhoneForwarded, Mic, Brain, Headphones
} from "lucide-react";

const CALENDLY_LINK = "https://calendly.com/intentbrain/15-30min";

const AIColdCallingPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "AI Cold Calling Software | Automate B2B Sales Calls | IntentBrain.ai";
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', 'AI cold calling software that makes 1000s of calls daily. Automated lead qualification, DISC personality detection, live transfers & Calendly booking. Start free trial.');
    }
  }, []);

  const features = [
    {
      icon: Bot,
      title: "AI-Powered Conversations",
      description: "Natural language AI handles objections, qualifies prospects, and books meetings—like your best sales rep, working 24/7."
    },
    {
      icon: Brain,
      title: "DISC Personality Detection",
      description: "AI analyzes buyer personality in real-time and adapts communication style to increase close rates by 40%."
    },
    {
      icon: PhoneForwarded,
      title: "Live Call Transfers",
      description: "Hot leads get instantly connected to your team. AI whispers the buyer's personality type before transfer."
    },
    {
      icon: Calendar,
      title: "Auto Calendly Booking",
      description: "Qualified leads book directly into your team's calendar. No manual follow-up required."
    },
    {
      icon: Mic,
      title: "Voice Cloning & Tuning",
      description: "Clone your voice or choose from 50+ AI voices. Adjust stability, clarity, and expressiveness."
    },
    {
      icon: BarChart3,
      title: "Call Analytics & Recordings",
      description: "Review every conversation with full transcripts, qualification scores, and call recordings."
    }
  ];

  const useCases = [
    {
      title: "Credit Card Processing Sales",
      description: "AI cold calls business owners about payment processing fees and books demos with decision makers."
    },
    {
      title: "B2B SaaS Demos",
      description: "Qualify prospects, identify budget and timeline, and book product demo calls automatically."
    },
    {
      title: "Home Services Lead Gen",
      description: "Call homeowners for HVAC, roofing, plumbing services and schedule in-home consultations."
    },
    {
      title: "Insurance Appointments",
      description: "Qualify insurance leads, verify coverage needs, and book appointments with licensed agents."
    }
  ];

  return (
    <div className="min-h-screen bg-[#0B1628]">
      {/* Navigation */}
      <nav className="bg-[#0B1628] sticky top-0 z-50 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-9 h-9 bg-gradient-to-br from-purple-400 to-cyan-500 rounded-lg flex items-center justify-center">
                <Phone className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold text-white">IntentBrain.ai</span>
            </Link>
            <div className="flex items-center gap-3">
              <button 
                onClick={() => navigate('/login')}
                className="rounded-full border border-gray-600 text-white hover:bg-white/10 bg-transparent px-4 py-2 text-sm"
              >
                Log in
              </button>
              <button 
                onClick={() => window.open(CALENDLY_LINK, '_blank')}
                className="rounded-full bg-gradient-to-r from-purple-500 to-cyan-500 hover:from-purple-600 hover:to-cyan-600 text-white px-4 py-2 text-sm"
              >
                Get Demo
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-20 pb-24 px-6 relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-gradient-to-r from-purple-500/20 via-cyan-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-5xl mx-auto text-center relative">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-full text-cyan-400 text-sm font-medium mb-6">
            <Phone className="w-4 h-4" />
            AI Cold Calling Software
          </span>
          
          <h1 className="text-5xl md:text-6xl font-bold leading-tight tracking-tight mb-6">
            <span className="text-white">AI Cold Calling That </span>
            <span className="bg-gradient-to-r from-purple-400 via-cyan-400 to-teal-400 bg-clip-text text-transparent">Closes More Deals</span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-3xl mx-auto leading-relaxed mb-8">
            Automate your outbound sales calls with AI that sounds human, detects buyer personality, 
            and books meetings directly on your calendar. Make 1000s of calls per day without hiring more reps.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Button 
              onClick={() => window.open(CALENDLY_LINK, '_blank')}
              className="rounded-full bg-gradient-to-r from-purple-500 to-cyan-500 hover:from-purple-600 hover:to-cyan-600 text-white px-10 py-7 text-lg font-semibold"
            >
              Start Free Trial
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Link to="/">
              <Button variant="outline" className="rounded-full border-gray-600 text-gray-300 hover:bg-white/10 bg-transparent px-8 py-6 text-base">
                <Headphones className="w-4 h-4 mr-2" />
                Listen to Demo Call
              </Button>
            </Link>
          </div>

          {/* Trust Badges */}
          <div className="flex items-center justify-center gap-6 flex-wrap">
            <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-4 py-2 rounded-full text-sm font-medium">
              <Shield className="w-4 h-4" />
              TCPA Compliant
            </div>
            <div className="flex items-center gap-2 bg-blue-500/10 border border-blue-500/30 text-blue-400 px-4 py-2 rounded-full text-sm font-medium">
              <CheckCircle className="w-4 h-4" />
              DNC List Verified
            </div>
            <div className="flex items-center gap-2 bg-purple-500/10 border border-purple-500/30 text-purple-400 px-4 py-2 rounded-full text-sm font-medium">
              <Clock className="w-4 h-4" />
              24/7 Automated
            </div>
          </div>
        </div>
      </section>

      {/* What is AI Cold Calling Section */}
      <section className="py-24 px-6 bg-gradient-to-b from-[#0B1628] to-[#0a0f1a]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              What is AI Cold Calling?
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              AI cold calling uses artificial intelligence to make sales calls automatically. 
              The AI sounds natural, handles objections, qualifies leads, and books meetings—all without human intervention.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="p-6 bg-white/5 border border-white/10 rounded-xl hover:border-cyan-500/30 transition-colors"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-24 px-6 bg-[#0a0f1a]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              AI Cold Calling Use Cases
            </h2>
            <p className="text-xl text-gray-400">
              Industries using IntentBrain to automate their sales outreach
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {useCases.map((useCase, index) => (
              <div 
                key={index}
                className="p-8 bg-gradient-to-br from-purple-500/10 to-cyan-500/10 border border-purple-500/20 rounded-2xl"
              >
                <h3 className="text-2xl font-semibold text-white mb-3">{useCase.title}</h3>
                <p className="text-gray-400 text-lg">{useCase.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 bg-gradient-to-r from-purple-600/20 to-cyan-600/20">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Automate Your Cold Calling?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Join hundreds of businesses using AI to scale their outbound sales without hiring more reps.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button 
              onClick={() => window.open(CALENDLY_LINK, '_blank')}
              className="rounded-full bg-gradient-to-r from-purple-500 to-cyan-500 hover:from-purple-600 hover:to-cyan-600 text-white px-10 py-7 text-lg font-semibold"
            >
              Book a Demo
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Link to="/">
              <Button variant="outline" className="rounded-full border-gray-600 text-gray-300 hover:bg-white/10 bg-transparent px-8 py-6 text-base">
                Back to Homepage
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#0B1628] border-t border-gray-800 py-12 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="w-9 h-9 bg-gradient-to-br from-purple-400 to-cyan-500 rounded-lg flex items-center justify-center">
              <Phone className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-white">IntentBrain.ai</span>
          </div>
          <p className="text-gray-500 mb-6">AI-powered cold calling that closes more deals</p>
          <div className="flex items-center justify-center gap-6 text-sm text-gray-400">
            <Link to="/terms" className="hover:text-white">Terms of Service</Link>
            <Link to="/privacy" className="hover:text-white">Privacy Policy</Link>
            <Link to="/help" className="hover:text-white">Help Center</Link>
          </div>
          <p className="text-gray-600 text-sm mt-6">© 2025 IntentBrain.ai. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default AIColdCallingPage;
