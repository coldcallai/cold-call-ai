import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Phone, Zap, Calendar, CheckCircle, ArrowRight, Play, 
  Users, Clock, Shield, Headphones, BarChart3,
  ChevronDown, Bot, Target, Menu, X
} from "lucide-react";

const LandingPage = () => {
  const [email, setEmail] = useState("");
  const [openFaq, setOpenFaq] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "SOC2 compliant. Your data is encrypted and never shared.",
    },
  ];

  const pricingPlans = [
    {
      name: "Discovery",
      price: "299",
      period: "/month",
      description: "Just the high-intent leads list",
      features: [
        "500 intent leads/month",
        "GPT-powered search",
        "Export to CSV",
        "Intent signals included",
        "1 user",
      ],
      cta: "Start Free Trial",
      popular: false,
    },
    {
      name: "Full Service",
      price: "499",
      period: "/month", 
      description: "Discovery + AI calling + booking",
      features: [
        "500 intent leads/month",
        "500 AI calls/month",
        "Auto calendar booking",
        "Call transcripts",
        "Email notifications",
        "5 users",
      ],
      cta: "Start Free Trial",
      popular: true,
    },
    {
      name: "Bring Your List",
      price: "399",
      period: "/month",
      description: "Upload your leads, we call them",
      features: [
        "Unlimited CSV uploads",
        "1,000 AI calls/month",
        "Custom scripts",
        "Auto calendar booking",
        "Call transcripts",
        "3 users",
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
      answer: "Yes! Every plan includes a 14-day free trial with 50 AI calls so you can see results before committing.",
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
              <span className="text-xl font-semibold text-white">ColdCall.ai</span>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <a href="#how-it-works" className="text-sm text-gray-300 hover:text-white transition-colors">How It Works</a>
              <a href="#features" className="text-sm text-gray-300 hover:text-white transition-colors">Features</a>
              <a href="#pricing" className="text-sm text-gray-300 hover:text-white transition-colors">Pricing</a>
              <a href="#faq" className="text-sm text-gray-300 hover:text-white transition-colors">FAQ</a>
            </div>

            <div className="hidden md:flex items-center gap-3">
              <Link to="/app">
                <Button variant="outline" className="rounded-full border-gray-600 text-white hover:bg-white/10 bg-transparent">
                  Log in
                </Button>
              </Link>
              <Button className="rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white border-0">
                Get a demo
              </Button>
            </div>

            <button 
              className="md:hidden p-2 text-white"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
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
            Break free from manual dialing. Discover leads, qualify them with AI-powered phone calls, 
            and book meetings automatically — with AI Agents doing the heavy lifting.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10">
            <Button className="rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white px-8 py-6 text-base font-medium border-0">
              <Play className="w-4 h-4 mr-2" />
              Get a demo
            </Button>
            <Button variant="outline" className="rounded-full border-gray-600 text-white hover:bg-white/10 bg-transparent px-8 py-6 text-base">
              Learn more about ColdCall.ai
            </Button>
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
              With ColdCall.ai, the orchestration of tasks for both AI Agents and human reps happens in a single workflow.
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
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">ColdCall.ai vs. Hiring SDRs</h2>
            <p className="text-gray-600 text-lg">See why AI-powered calling makes sense</p>
          </div>

          <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
            <div className="grid grid-cols-3 text-center border-b border-gray-100">
              <div className="p-6"></div>
              <div className="p-6 bg-gradient-to-b from-cyan-50 to-white">
                <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl flex items-center justify-center mx-auto mb-2">
                  <Phone className="w-5 h-5 text-white" />
                </div>
                <p className="font-semibold text-gray-900">ColdCall.ai</p>
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

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {pricingPlans.map((plan, idx) => (
              <div 
                key={idx}
                className={`relative bg-white border rounded-2xl p-8 ${
                  plan.popular 
                    ? 'border-teal-500 shadow-lg shadow-teal-500/10' 
                    : 'border-gray-200'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-full text-sm font-medium">
                    Most Popular
                  </div>
                )}
                
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{plan.name}</h3>
                <p className="text-gray-500 text-sm mb-6">{plan.description}</p>
                
                <div className="mb-6">
                  <span className="text-4xl font-bold text-gray-900">{plan.price === "Custom" ? "" : "$"}{plan.price}</span>
                  <span className="text-gray-500">{plan.period}</span>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, fidx) => (
                    <li key={fidx} className="flex items-center gap-3 text-sm">
                      <CheckCircle className="w-5 h-5 text-teal-500 flex-shrink-0" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button 
                  className={`w-full rounded-full py-6 ${
                    plan.popular 
                      ? 'bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white border-0' 
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-900 border-0'
                  }`}
                >
                  {plan.cta}
                </Button>
              </div>
            ))}
          </div>

          <p className="text-center text-gray-500 text-sm mt-8">
            All plans include 14-day free trial with 50 AI calls. No credit card required.
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
            Ready to automate your outbound? Get a personalized demo and see ColdCall.ai in action.
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
            14-day free trial • No credit card required
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
              <span className="font-semibold text-white">ColdCall.ai</span>
            </div>

            <div className="flex items-center gap-8 text-sm text-gray-400">
              <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
            </div>

            <p className="text-sm text-gray-500">© 2025 ColdCall.ai. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
