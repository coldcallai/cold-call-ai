import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { 
  Phone, Zap, Calendar, CheckCircle, ArrowRight, 
  Bot, Target, Clock, Shield, BarChart3, Users,
  PhoneForwarded, Mic, Brain, Headphones, Repeat, Settings
} from "lucide-react";

const CALENDLY_LINK = "https://calendly.com/dialgenix/15-30min";

const AutomatedColdCallingPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Automated Cold Calling Software | AI-Powered Outbound Calls | DialGenix.ai";
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', 'Automated cold calling software that runs 24/7. AI makes calls, qualifies leads, handles objections & books meetings automatically. No human intervention needed.');
    }
  }, []);

  const automationFeatures = [
    {
      icon: Repeat,
      title: "Fully Automated Outreach",
      description: "Set it and forget it. AI calls your leads 24/7 without any human intervention required."
    },
    {
      icon: Bot,
      title: "AI Handles Everything",
      description: "From initial greeting to objection handling to booking—AI manages the entire conversation."
    },
    {
      icon: Target,
      title: "Smart Lead Qualification",
      description: "AI asks qualifying questions, scores leads, and only passes hot prospects to your team."
    },
    {
      icon: Brain,
      title: "Learns & Improves",
      description: "AI analyzes successful calls and continuously improves its scripts and approach."
    },
    {
      icon: Calendar,
      title: "Automated Scheduling",
      description: "Qualified leads book directly into your Calendly. Wake up to meetings on your calendar."
    },
    {
      icon: Shield,
      title: "Compliance Built-In",
      description: "Automatic DNC list checking, calling hours compliance, and consent management."
    }
  ];

  const workflowSteps = [
    { 
      step: "1", 
      title: "Upload Your Leads", 
      desc: "Import CSV or let AI discover high-intent prospects" 
    },
    { 
      step: "2", 
      title: "Set Your Script", 
      desc: "Customize what AI says or use proven templates" 
    },
    { 
      step: "3", 
      title: "AI Calls 24/7", 
      desc: "Automated calls run continuously without supervision" 
    },
    { 
      step: "4", 
      title: "Get Booked Meetings", 
      desc: "Qualified leads appear on your calendar automatically" 
    },
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
              <span className="text-xl font-semibold text-white">DialGenix.ai</span>
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
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-gradient-to-r from-emerald-500/20 via-cyan-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-5xl mx-auto text-center relative">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-emerald-400 text-sm font-medium mb-6">
            <Repeat className="w-4 h-4" />
            Automated Cold Calling
          </span>
          
          <h1 className="text-5xl md:text-6xl font-bold leading-tight tracking-tight mb-6">
            <span className="text-white">Cold Calling on </span>
            <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-purple-400 bg-clip-text text-transparent">Complete Autopilot</span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-3xl mx-auto leading-relaxed mb-8">
            Set up once, let AI handle everything. Automated cold calling that runs 24/7, 
            qualifies leads, handles objections, and books meetings—all without human intervention.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Button 
              onClick={() => window.open(CALENDLY_LINK, '_blank')}
              className="rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white px-10 py-7 text-lg font-semibold"
            >
              Start Automating
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Link to="/">
              <Button variant="outline" className="rounded-full border-gray-600 text-gray-300 hover:bg-white/10 bg-transparent px-8 py-6 text-base">
                <Headphones className="w-4 h-4 mr-2" />
                Hear Sample Calls
              </Button>
            </Link>
          </div>

          {/* Trust Badges */}
          <div className="flex items-center justify-center gap-6 flex-wrap">
            <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-4 py-2 rounded-full text-sm font-medium">
              <Clock className="w-4 h-4" />
              Runs 24/7
            </div>
            <div className="flex items-center gap-2 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 px-4 py-2 rounded-full text-sm font-medium">
              <Shield className="w-4 h-4" />
              TCPA Compliant
            </div>
            <div className="flex items-center gap-2 bg-purple-500/10 border border-purple-500/30 text-purple-400 px-4 py-2 rounded-full text-sm font-medium">
              <CheckCircle className="w-4 h-4" />
              No Supervision Needed
            </div>
          </div>
        </div>
      </section>

      {/* How Automation Works */}
      <section className="py-24 px-6 bg-gradient-to-b from-[#0B1628] to-[#0a0f1a]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              How Automated Cold Calling Works
            </h2>
            <p className="text-xl text-gray-400">
              Set up in minutes, run forever
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            {workflowSteps.map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-14 h-14 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold text-xl">{item.step}</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-gray-400 text-sm">{item.desc}</p>
                {index < 3 && (
                  <ArrowRight className="w-6 h-6 text-gray-600 mx-auto mt-4 hidden md:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6 bg-[#0a0f1a]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              True Automation Features
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Not just auto-dialing—complete end-to-end automation
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {automationFeatures.map((feature, index) => (
              <div 
                key={index}
                className="p-6 bg-white/5 border border-white/10 rounded-xl hover:border-emerald-500/30 transition-colors"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Results Section */}
      <section className="py-24 px-6 bg-gradient-to-b from-[#0a0f1a] to-[#0B1628]">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              What Automation Delivers
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20 rounded-2xl p-8 text-center">
              <div className="text-4xl font-bold text-emerald-400 mb-2">90%</div>
              <p className="text-gray-400">Less time spent dialing</p>
            </div>
            <div className="bg-gradient-to-br from-cyan-500/10 to-purple-500/10 border border-cyan-500/20 rounded-2xl p-8 text-center">
              <div className="text-4xl font-bold text-cyan-400 mb-2">5x</div>
              <p className="text-gray-400">More qualified meetings</p>
            </div>
            <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-2xl p-8 text-center">
              <div className="text-4xl font-bold text-purple-400 mb-2">24/7</div>
              <p className="text-gray-400">Continuous prospecting</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 bg-gradient-to-r from-emerald-600/20 to-cyan-600/20">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Automate Your Cold Calling?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Stop manually dialing. Let AI do the heavy lifting while you close deals.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button 
              onClick={() => window.open(CALENDLY_LINK, '_blank')}
              className="rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white px-10 py-7 text-lg font-semibold"
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
            <span className="text-xl font-semibold text-white">DialGenix.ai</span>
          </div>
          <p className="text-gray-500 mb-6">Automated cold calling on complete autopilot</p>
          <div className="flex items-center justify-center gap-6 text-sm text-gray-400 flex-wrap">
            <Link to="/terms" className="hover:text-white">Terms</Link>
            <Link to="/privacy" className="hover:text-white">Privacy</Link>
            <Link to="/ai-cold-calling" className="hover:text-white">AI Cold Calling</Link>
            <Link to="/voice-ai-sales" className="hover:text-white">Voice AI</Link>
            <Link to="/ai-sales-dialer" className="hover:text-white">AI Sales Dialer</Link>
          </div>
          <p className="text-gray-600 text-sm mt-6">© 2025 DialGenix.ai. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default AutomatedColdCallingPage;
