import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { 
  Phone, Zap, Calendar, CheckCircle, ArrowRight, 
  Bot, Target, Clock, Shield, BarChart3, Users,
  PhoneForwarded, Mic, Brain, Headphones, CalendarCheck, Building2
} from "lucide-react";

const CALENDLY_LINK = "https://calendly.com/intentbrain/15-30min";

const AIAppointmentSetterPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "AI Appointment Setter | Automated Meeting Booking | IntentBrain.ai";
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', 'AI appointment setter that books meetings automatically. AI calls leads, qualifies them, checks calendar availability & schedules appointments. Works with Calendly.');
    }
  }, []);

  const appointmentFeatures = [
    {
      icon: CalendarCheck,
      title: "Auto-Book Meetings",
      description: "AI checks your real-time calendar availability and books qualified leads directly into open slots."
    },
    {
      icon: Bot,
      title: "AI Qualification",
      description: "AI asks your qualifying questions and only books meetings with leads that match your criteria."
    },
    {
      icon: Calendar,
      title: "Calendly Integration",
      description: "Seamless integration with Calendly. Meetings appear on your calendar automatically."
    },
    {
      icon: PhoneForwarded,
      title: "Smart Rescheduling",
      description: "AI handles reschedule requests and cancellations, keeping your calendar optimized."
    },
    {
      icon: Users,
      title: "Round-Robin Booking",
      description: "Distribute meetings across your sales team based on availability and workload."
    },
    {
      icon: Zap,
      title: "Instant Confirmations",
      description: "Leads receive instant email confirmations with meeting details and calendar invites."
    }
  ];

  const industries = [
    {
      icon: Building2,
      title: "B2B Sales Teams",
      description: "Book demos and discovery calls with qualified prospects automatically."
    },
    {
      icon: Users,
      title: "Service Businesses",
      description: "Schedule consultations, estimates, and service appointments 24/7."
    },
    {
      icon: BarChart3,
      title: "Financial Services",
      description: "Book advisory sessions and client meetings with pre-qualified leads."
    },
    {
      icon: Shield,
      title: "Insurance Agencies",
      description: "Schedule policy reviews and new client consultations on autopilot."
    },
  ];

  return (
    <div className="min-h-screen bg-[#0B1628]">
      {/* Navigation */}
      <nav className="bg-[#0B1628] sticky top-0 z-50 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3">
              <img src="/intentbrain-logo.png" alt="IntentBrain.ai" className="w-9 h-9 rounded-lg" />
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
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-gradient-to-r from-blue-500/20 via-purple-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-5xl mx-auto text-center relative">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-full text-blue-400 text-sm font-medium mb-6">
            <CalendarCheck className="w-4 h-4" />
            AI Appointment Setter
          </span>
          
          <h1 className="text-5xl md:text-6xl font-bold leading-tight tracking-tight mb-6">
            <span className="text-white">AI That </span>
            <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">Books Meetings For You</span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-3xl mx-auto leading-relaxed mb-8">
            Stop chasing leads for meetings. AI calls prospects, qualifies them, checks your calendar, 
            and books appointments automatically. Wake up to a full calendar.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Button 
              onClick={() => window.open(CALENDLY_LINK, '_blank')}
              className="rounded-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white px-10 py-7 text-lg font-semibold"
            >
              Start Booking Automatically
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Link to="/">
              <Button variant="outline" className="rounded-full border-gray-600 text-gray-300 hover:bg-white/10 bg-transparent px-8 py-6 text-base">
                <Headphones className="w-4 h-4 mr-2" />
                Hear AI Book a Meeting
              </Button>
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-6 max-w-2xl mx-auto">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">5x</div>
              <div className="text-gray-500 text-sm">More meetings booked</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-400">0</div>
              <div className="text-gray-500 text-sm">Manual scheduling</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-cyan-400">24/7</div>
              <div className="text-gray-500 text-sm">Booking availability</div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-6 bg-gradient-to-b from-[#0B1628] to-[#0a0f1a]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              How AI Appointment Setting Works
            </h2>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: "1", title: "AI Calls Lead", desc: "Natural conversation to build rapport" },
              { step: "2", title: "Qualifies Interest", desc: "Asks your qualifying questions" },
              { step: "3", title: "Checks Calendar", desc: "Finds available slots in real-time" },
              { step: "4", title: "Books & Confirms", desc: "Schedules meeting, sends invite" },
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold text-xl">{item.step}</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-gray-400 text-sm">{item.desc}</p>
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
              Appointment Setting Features
            </h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {appointmentFeatures.map((feature, index) => (
              <div 
                key={index}
                className="p-6 bg-white/5 border border-white/10 rounded-xl hover:border-blue-500/30 transition-colors"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Industries Section */}
      <section className="py-24 px-6 bg-gradient-to-b from-[#0a0f1a] to-[#0B1628]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Who Uses AI Appointment Setters
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {industries.map((industry, index) => (
              <div 
                key={index}
                className="p-8 bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-2xl"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center mb-4">
                  <industry.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-2xl font-semibold text-white mb-3">{industry.title}</h3>
                <p className="text-gray-400 text-lg">{industry.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 bg-gradient-to-r from-blue-600/20 to-purple-600/20">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Fill Your Calendar Automatically?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Let AI handle appointment setting while you focus on closing deals.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button 
              onClick={() => window.open(CALENDLY_LINK, '_blank')}
              className="rounded-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white px-10 py-7 text-lg font-semibold"
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
            <img src="/intentbrain-logo.png" alt="IntentBrain.ai" className="w-9 h-9 rounded-lg" />
            <span className="text-xl font-semibold text-white">IntentBrain.ai</span>
          </div>
          <p className="text-gray-500 mb-6">AI appointment setter that fills your calendar</p>
          <div className="flex items-center justify-center gap-6 text-sm text-gray-400 flex-wrap">
            <Link to="/terms" className="hover:text-white">Terms</Link>
            <Link to="/privacy" className="hover:text-white">Privacy</Link>
            <Link to="/ai-cold-calling" className="hover:text-white">AI Cold Calling</Link>
            <Link to="/voice-ai-sales" className="hover:text-white">Voice AI</Link>
            <Link to="/ai-sales-dialer" className="hover:text-white">Sales Dialer</Link>
            <Link to="/automated-cold-calling" className="hover:text-white">Automated Calling</Link>
          </div>
          <p className="text-gray-600 text-sm mt-6">© 2025 IntentBrain.ai. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default AIAppointmentSetterPage;
