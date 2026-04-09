import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { 
  Phone, Zap, Calendar, CheckCircle, ArrowRight, 
  Bot, Target, Clock, Shield, BarChart3, Users,
  PhoneForwarded, Mic, Brain, Headphones, Settings, TrendingUp
} from "lucide-react";

const CALENDLY_LINK = "https://calendly.com/dialgenix/15-30min";

const AISalesDialerPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "AI Sales Dialer | Automated Outbound Calling Software | DialGenix.ai";
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', 'AI sales dialer that automates outbound calls. Power dialer with DISC personality detection, auto-booking, live transfers & call recording. Scale your sales team 10x.');
    }
  }, []);

  const dialerFeatures = [
    {
      icon: Zap,
      title: "10x Call Volume",
      description: "AI makes hundreds of calls per hour while your team focuses on closing. No more manual dialing or wasted time."
    },
    {
      icon: Brain,
      title: "Smart Lead Prioritization",
      description: "AI scores leads by buying intent and prioritizes the hottest prospects automatically."
    },
    {
      icon: Bot,
      title: "Conversational AI",
      description: "Natural-sounding AI handles initial conversations, qualifies leads, and overcomes objections."
    },
    {
      icon: PhoneForwarded,
      title: "Instant Live Transfers",
      description: "When AI detects buying signals, it transfers the call to your sales rep instantly."
    },
    {
      icon: Calendar,
      title: "Auto-Book Meetings",
      description: "AI checks your calendar availability and books qualified meetings automatically."
    },
    {
      icon: BarChart3,
      title: "Real-Time Analytics",
      description: "Track connect rates, qualification rates, and conversion metrics in real-time."
    }
  ];

  const comparisonData = [
    { feature: "Calls per hour", ai: "100+", traditional: "15-20" },
    { feature: "Cost per call", ai: "$0.50", traditional: "$15+" },
    { feature: "24/7 availability", ai: true, traditional: false },
    { feature: "Personality detection", ai: true, traditional: false },
    { feature: "Auto meeting booking", ai: true, traditional: false },
    { feature: "Call recording", ai: true, traditional: true },
    { feature: "CRM integration", ai: true, traditional: true },
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
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-gradient-to-r from-orange-500/20 via-purple-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-5xl mx-auto text-center relative">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-orange-500/10 border border-orange-500/30 rounded-full text-orange-400 text-sm font-medium mb-6">
            <Zap className="w-4 h-4" />
            AI Sales Dialer
          </span>
          
          <h1 className="text-5xl md:text-6xl font-bold leading-tight tracking-tight mb-6">
            <span className="text-white">AI Sales Dialer That </span>
            <span className="bg-gradient-to-r from-orange-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">10x Your Outbound</span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-3xl mx-auto leading-relaxed mb-8">
            Stop wasting time on manual dialing. Our AI sales dialer makes hundreds of calls per hour, 
            qualifies leads automatically, and transfers hot prospects to your team in real-time.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Button 
              onClick={() => window.open(CALENDLY_LINK, '_blank')}
              className="rounded-full bg-gradient-to-r from-orange-500 to-purple-500 hover:from-orange-600 hover:to-purple-600 text-white px-10 py-7 text-lg font-semibold"
            >
              Start Free Trial
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Link to="/">
              <Button variant="outline" className="rounded-full border-gray-600 text-gray-300 hover:bg-white/10 bg-transparent px-8 py-6 text-base">
                <Headphones className="w-4 h-4 mr-2" />
                Hear AI Calls
              </Button>
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-6 max-w-2xl mx-auto">
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-400">100+</div>
              <div className="text-gray-500 text-sm">Calls/hour</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-400">$0.50</div>
              <div className="text-gray-500 text-sm">Per call</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-cyan-400">24/7</div>
              <div className="text-gray-500 text-sm">Availability</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6 bg-gradient-to-b from-[#0B1628] to-[#0a0f1a]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              AI Sales Dialer Features
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Everything you need to automate outbound sales and close more deals
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {dialerFeatures.map((feature, index) => (
              <div 
                key={index}
                className="p-6 bg-white/5 border border-white/10 rounded-xl hover:border-orange-500/30 transition-colors"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-purple-500 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Section */}
      <section className="py-24 px-6 bg-[#0a0f1a]">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              AI Dialer vs Traditional Power Dialers
            </h2>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left text-gray-400 py-4 px-6 font-medium">Metric</th>
                  <th className="text-center text-orange-400 py-4 px-6 font-semibold">AI Sales Dialer</th>
                  <th className="text-center text-gray-500 py-4 px-6 font-medium">Power Dialer</th>
                </tr>
              </thead>
              <tbody>
                {comparisonData.map((row, index) => (
                  <tr key={index} className="border-b border-white/5">
                    <td className="text-white py-4 px-6">{row.feature}</td>
                    <td className="text-center py-4 px-6">
                      {typeof row.ai === 'boolean' ? (
                        row.ai ? (
                          <CheckCircle className="w-5 h-5 text-emerald-400 mx-auto" />
                        ) : (
                          <span className="text-gray-600">—</span>
                        )
                      ) : (
                        <span className="text-emerald-400 font-semibold">{row.ai}</span>
                      )}
                    </td>
                    <td className="text-center py-4 px-6">
                      {typeof row.traditional === 'boolean' ? (
                        row.traditional ? (
                          <CheckCircle className="w-5 h-5 text-gray-500 mx-auto" />
                        ) : (
                          <span className="text-gray-600">—</span>
                        )
                      ) : (
                        <span className="text-gray-400">{row.traditional}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 bg-gradient-to-r from-orange-600/20 to-purple-600/20">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to 10x Your Sales Calls?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            See how AI can transform your outbound sales process.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button 
              onClick={() => window.open(CALENDLY_LINK, '_blank')}
              className="rounded-full bg-gradient-to-r from-orange-500 to-purple-500 hover:from-orange-600 hover:to-purple-600 text-white px-10 py-7 text-lg font-semibold"
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
          <p className="text-gray-500 mb-6">AI sales dialer that 10x your outbound</p>
          <div className="flex items-center justify-center gap-6 text-sm text-gray-400 flex-wrap">
            <Link to="/terms" className="hover:text-white">Terms</Link>
            <Link to="/privacy" className="hover:text-white">Privacy</Link>
            <Link to="/ai-cold-calling" className="hover:text-white">AI Cold Calling</Link>
            <Link to="/voice-ai-sales" className="hover:text-white">Voice AI</Link>
            <Link to="/automated-cold-calling" className="hover:text-white">Automated Calling</Link>
          </div>
          <p className="text-gray-600 text-sm mt-6">© 2025 DialGenix.ai. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default AISalesDialerPage;
