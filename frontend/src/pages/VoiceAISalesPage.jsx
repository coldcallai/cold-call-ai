import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { 
  Phone, Zap, Calendar, CheckCircle, ArrowRight, 
  Bot, Target, Clock, Shield, BarChart3, Users,
  PhoneForwarded, Mic, Brain, Headphones, Volume2, Settings
} from "lucide-react";

const CALENDLY_LINK = "https://calendly.com/dialgenix/15-30min";

const VoiceAISalesPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Voice AI for Sales | AI Sales Agent & Dialer | DialGenix.ai";
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', 'Voice AI sales agent that makes natural-sounding calls. DISC personality detection, voice cloning, live transfers & auto-booking. Powered by GPT-5.2 & ElevenLabs.');
    }
  }, []);

  const voiceFeatures = [
    {
      icon: Volume2,
      title: "Human-Like Voice AI",
      description: "Powered by ElevenLabs and GPT-5.2 for the most natural-sounding AI sales calls. Prospects can't tell they're talking to AI."
    },
    {
      icon: Mic,
      title: "Voice Cloning",
      description: "Clone your own voice or your top sales rep's voice. Upload 1-5 minutes of audio to create a custom AI voice."
    },
    {
      icon: Settings,
      title: "Voice Tuning Controls",
      description: "Fine-tune stability, clarity, and expressiveness. Create the perfect voice for your brand and audience."
    },
    {
      icon: Brain,
      title: "Real-Time Personality Detection",
      description: "AI analyzes buyer personality (DISC) during the call and adapts communication style automatically."
    },
    {
      icon: PhoneForwarded,
      title: "Smart Live Transfers",
      description: "When the AI detects high buying intent, it transfers instantly. Your team hears personality insights before connecting."
    },
    {
      icon: Calendar,
      title: "Automated Meeting Booking",
      description: "Voice AI checks availability and books meetings directly into Calendly. No manual follow-up needed."
    }
  ];

  const comparisonData = [
    { feature: "Natural Conversations", dialgenix: true, traditional: false },
    { feature: "24/7 Availability", dialgenix: true, traditional: false },
    { feature: "Personality Detection", dialgenix: true, traditional: false },
    { feature: "Instant Scalability", dialgenix: true, traditional: false },
    { feature: "Voice Customization", dialgenix: true, traditional: false },
    { feature: "Auto Meeting Booking", dialgenix: true, traditional: false },
    { feature: "Call Recordings", dialgenix: true, traditional: true },
    { feature: "Cost per Call", dialgenix: "$0.50", traditional: "$15+" },
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
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-gradient-to-r from-cyan-500/20 via-purple-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-5xl mx-auto text-center relative">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/10 border border-purple-500/30 rounded-full text-purple-400 text-sm font-medium mb-6">
            <Volume2 className="w-4 h-4" />
            Voice AI Sales Technology
          </span>
          
          <h1 className="text-5xl md:text-6xl font-bold leading-tight tracking-tight mb-6">
            <span className="text-white">Voice AI That </span>
            <span className="bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">Sells Like a Human</span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-3xl mx-auto leading-relaxed mb-8">
            The most advanced voice AI for sales. Natural conversations powered by GPT-5.2 and ElevenLabs, 
            with real-time personality detection and automatic meeting booking.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Button 
              onClick={() => window.open(CALENDLY_LINK, '_blank')}
              className="rounded-full bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 text-white px-10 py-7 text-lg font-semibold"
            >
              Try Voice AI Demo
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Link to="/">
              <Button variant="outline" className="rounded-full border-gray-600 text-gray-300 hover:bg-white/10 bg-transparent px-8 py-6 text-base">
                <Headphones className="w-4 h-4 mr-2" />
                Hear Sample Calls
              </Button>
            </Link>
          </div>

          {/* Tech Stack */}
          <div className="flex items-center justify-center gap-8 flex-wrap">
            <div className="flex items-center gap-2 bg-gray-800/50 px-4 py-2 rounded-lg">
              <span className="text-emerald-400 font-semibold">GPT-5.2</span>
              <span className="text-gray-500 text-sm">Conversations</span>
            </div>
            <div className="flex items-center gap-2 bg-gray-800/50 px-4 py-2 rounded-lg">
              <span className="text-purple-400 font-semibold">ElevenLabs</span>
              <span className="text-gray-500 text-sm">Voice Synthesis</span>
            </div>
            <div className="flex items-center gap-2 bg-gray-800/50 px-4 py-2 rounded-lg">
              <span className="text-red-400 font-semibold">Twilio</span>
              <span className="text-gray-500 text-sm">Calling Infrastructure</span>
            </div>
          </div>
        </div>
      </section>

      {/* Voice Features Section */}
      <section className="py-24 px-6 bg-gradient-to-b from-[#0B1628] to-[#0a0f1a]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Voice AI Sales Features
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Everything you need to automate sales calls with the most natural-sounding AI voice technology
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {voiceFeatures.map((feature, index) => (
              <div 
                key={index}
                className="p-6 bg-white/5 border border-white/10 rounded-xl hover:border-purple-500/30 transition-colors"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-purple-500 rounded-lg flex items-center justify-center mb-4">
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
              Voice AI vs Traditional Sales Calls
            </h2>
            <p className="text-xl text-gray-400">
              See why businesses are switching to AI-powered sales calling
            </p>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left text-gray-400 py-4 px-6 font-medium">Feature</th>
                  <th className="text-center text-purple-400 py-4 px-6 font-semibold">DialGenix Voice AI</th>
                  <th className="text-center text-gray-500 py-4 px-6 font-medium">Traditional Dialers</th>
                </tr>
              </thead>
              <tbody>
                {comparisonData.map((row, index) => (
                  <tr key={index} className="border-b border-white/5">
                    <td className="text-white py-4 px-6">{row.feature}</td>
                    <td className="text-center py-4 px-6">
                      {typeof row.dialgenix === 'boolean' ? (
                        row.dialgenix ? (
                          <CheckCircle className="w-5 h-5 text-emerald-400 mx-auto" />
                        ) : (
                          <span className="text-gray-600">—</span>
                        )
                      ) : (
                        <span className="text-emerald-400 font-semibold">{row.dialgenix}</span>
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
                        <span className="text-red-400">{row.traditional}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* How Voice AI Works */}
      <section className="py-24 px-6 bg-gradient-to-b from-[#0a0f1a] to-[#0B1628]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              How Voice AI Sales Works
            </h2>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: "1", title: "Upload Leads", desc: "Import your lead list or let AI discover high-intent prospects" },
              { step: "2", title: "AI Calls", desc: "Voice AI makes natural calls, handles objections, qualifies leads" },
              { step: "3", title: "Personality Detection", desc: "AI detects DISC type and adapts communication style" },
              { step: "4", title: "Book or Transfer", desc: "Qualified leads book meetings or transfer to your team live" },
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold text-lg">{item.step}</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-gray-400 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 bg-gradient-to-r from-cyan-600/20 to-purple-600/20">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Try Voice AI for Sales?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Experience the future of sales calling. Book a demo to hear how natural our AI voice sounds.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button 
              onClick={() => window.open(CALENDLY_LINK, '_blank')}
              className="rounded-full bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 text-white px-10 py-7 text-lg font-semibold"
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
          <p className="text-gray-500 mb-6">Voice AI that sells like a human</p>
          <div className="flex items-center justify-center gap-6 text-sm text-gray-400">
            <Link to="/terms" className="hover:text-white">Terms of Service</Link>
            <Link to="/privacy" className="hover:text-white">Privacy Policy</Link>
            <Link to="/help" className="hover:text-white">Help Center</Link>
            <Link to="/ai-cold-calling" className="hover:text-white">AI Cold Calling</Link>
          </div>
          <p className="text-gray-600 text-sm mt-6">© 2025 DialGenix.ai. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default VoiceAISalesPage;
