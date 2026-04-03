import { useState } from "react";
import { Link } from "react-router-dom";
import { 
  HelpCircle, Play, BookOpen, MessageSquare, Mail, Phone,
  ChevronRight, ChevronDown, Search, Zap, Users, Settings, Target,
  Mic, Volume2, Calendar, CreditCard, Shield, ArrowLeft,
  CheckCircle, AlertTriangle, Lightbulb, ArrowRight, Rocket,
  FileText, Headphones, BarChart3
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

// Step-by-Step Guides Data
const STEP_BY_STEP_GUIDES = [
  {
    id: "quickstart",
    title: "Quick Start Guide",
    description: "Get your first AI call running in 10 minutes",
    icon: Rocket,
    color: "blue",
    estimatedTime: "10 min",
    steps: [
      {
        title: "Create Your Account",
        content: "Sign up at dialgenix.ai using your email or Google account. Verify your phone number to unlock your free trial minutes.",
        tip: "Use a phone number you have access to — you'll receive a verification code via SMS."
      },
      {
        title: "Connect Twilio (Required for Real Calls)",
        content: "Go to Settings → Integrations → Twilio. Enter your Twilio Account SID, Auth Token, and a Twilio phone number. This enables real outbound calls.",
        tip: "Don't have Twilio? Sign up at twilio.com — they offer free trial credits to get started."
      },
      {
        title: "Create Your First AI Agent",
        content: "Navigate to Agents → Click 'Add Agent'. Give your agent a name (e.g., 'Sales Agent'). Choose a preset voice or clone your own. Write a simple opening script.",
        tip: "Start simple! A good opener: 'Hi, this is [Name] from [Company]. Did I catch you at a good time?'"
      },
      {
        title: "Set Up Voice Settings",
        content: "Click the gear icon on your agent. Choose a Quick Preset (Professional, Conversational, or Energetic) or fine-tune the sliders manually. Always click 'Preview Voice' before saving.",
        tip: "For B2B sales, start with the 'Professional' preset — it's calm and trustworthy."
      },
      {
        title: "Add Your First Leads",
        content: "Go to Lead Discovery → Click 'Add Leads'. Either upload a CSV file with company names and phone numbers, or use AI Discovery to find leads automatically.",
        tip: "CSV format: company_name, phone_number, contact_name (optional), email (optional)"
      },
      {
        title: "Create a Campaign",
        content: "Go to Campaigns → Click 'New Campaign'. Name it, select your agent, add your leads, set calls per day (start with 50), and configure calling hours.",
        tip: "Respect business hours! Set calling times between 9 AM - 5 PM in your target timezone."
      },
      {
        title: "Launch and Monitor",
        content: "Click 'Start Campaign'. Watch calls happen in real-time from Call History. Listen to recordings, review outcomes, and refine your script based on results.",
        tip: "Check your first 10 calls carefully — small script tweaks can dramatically improve results."
      }
    ]
  },
  {
    id: "agent-setup",
    title: "Agent Setup Guide",
    description: "Create the perfect AI sales agent",
    icon: Users,
    color: "purple",
    estimatedTime: "5 min",
    steps: [
      {
        title: "Name Your Agent",
        content: "Go to Agents → Add Agent. Choose a descriptive name like 'SaaS Outreach Agent' or 'Restaurant Qualifier'. This helps you organize multiple agents for different campaigns.",
        tip: "Create separate agents for different industries or scripts — don't try to make one agent do everything."
      },
      {
        title: "Choose Voice Type",
        content: "Select 'Preset Voice' to use professional ElevenLabs voices, or 'Clone Voice' to create a custom voice from your own recordings. Preset voices work great for most use cases.",
        tip: "Rachel (female) and Josh (male) are the most popular choices for professional sales calls."
      },
      {
        title: "Write Your Script",
        content: "Enter your call script in the text area. Include: a hook (why you're calling), introduction (who you are), value proposition (what's in it for them), and call-to-action (book a meeting, transfer to sales, etc.).",
        tip: "Keep sentences short. Add '...' for natural pauses. Write how people talk, not how they write."
      },
      {
        title: "Configure Objection Handling",
        content: "Add common objections and how your agent should respond. Examples: 'I'm busy' → 'I understand, when would be a better time to chat for 2 minutes?' 'Not interested' → 'No problem! May I ask what solution you're currently using?'",
        tip: "The best agents acknowledge objections before responding — it sounds more human."
      },
      {
        title: "Test Your Agent",
        content: "Save your agent, then use the 'Call Yourself' feature to hear how it sounds. Make adjustments to the script or voice settings based on the test call.",
        tip: "Test at least 3 times. Listen for awkward pauses, unnatural phrasing, or unclear value props."
      }
    ]
  },
  {
    id: "voice-tuning",
    title: "Voice Tuning Guide",
    description: "Make your AI sound perfectly human",
    icon: Volume2,
    color: "green",
    estimatedTime: "3 min",
    steps: [
      {
        title: "Open Voice Settings",
        content: "Go to Agents → Find your agent → Click the gear (⚙️) icon. This opens the Voice Settings modal where you can customize how your AI sounds.",
        tip: "You can change voice settings anytime without creating a new agent."
      },
      {
        title: "Try Quick Presets First",
        content: "Click one of the three preset buttons: Professional (calm, B2B), Conversational (friendly, warm leads), or Energetic (upbeat, promotions). These are optimized starting points.",
        tip: "Professional works for 80% of B2B use cases. Start there unless you have a specific reason not to."
      },
      {
        title: "Fine-Tune with Sliders",
        content: "Stability (0.3-0.5 = expressive, 0.6-0.8 = consistent). Similarity (keep 0.7-0.8 for clarity). Style (0.2-0.4 = calm, 0.5+ = energetic). Adjust based on your brand voice.",
        tip: "Lower stability = more human variation but less predictable. Higher = robotic but consistent. Find your balance."
      },
      {
        title: "Preview and Save",
        content: "ALWAYS click 'Preview Voice' before saving. Listen to the sample. If it doesn't sound right, adjust and preview again. When satisfied, click 'Save Settings'.",
        tip: "Preview multiple times — the AI generates slightly different output each time due to the stability setting."
      }
    ]
  },
  {
    id: "campaign-launch",
    title: "Campaign Launch Guide",
    description: "Set up and launch successful calling campaigns",
    icon: Rocket,
    color: "orange",
    estimatedTime: "7 min",
    steps: [
      {
        title: "Create New Campaign",
        content: "Go to Campaigns → Click 'New Campaign'. Enter a descriptive name like 'Q1 SaaS Outreach' or 'NYC Restaurants'. Good naming helps you track performance across campaigns.",
        tip: "Include the target audience and timeframe in the name — you'll thank yourself later."
      },
      {
        title: "Select Your Agent",
        content: "Choose which AI agent will make these calls. Each agent has its own voice and script. Make sure the agent's script matches the campaign's target audience.",
        tip: "Create different agents for different industries — a restaurant script won't work for SaaS companies."
      },
      {
        title: "Add Leads to Campaign",
        content: "Click 'Add Leads' and either select from your existing leads or upload a new CSV. Review the leads to ensure phone numbers are formatted correctly (+1XXXXXXXXXX for US).",
        tip: "Quality over quantity! 100 well-targeted leads beat 1,000 random ones every time."
      },
      {
        title: "Configure Call Settings",
        content: "Set calls per day (start with 50-100). Choose calling hours (respect business hours!). Enable/disable voicemail. Set max call duration. Configure follow-up rules.",
        tip: "Start conservative with 50 calls/day. Increase once you've validated your script works."
      },
      {
        title: "Set Up Calendly (Optional)",
        content: "If you want the AI to book meetings, go to Settings → Integrations → Calendly. Connect your calendar. The AI will offer available slots to qualified leads.",
        tip: "Make sure your Calendly has enough availability — nothing worse than a hot lead with no slots!"
      },
      {
        title: "Launch Campaign",
        content: "Review all settings one final time. Click 'Start Campaign'. Your AI will begin calling according to your schedule. Monitor from the dashboard.",
        tip: "Watch your first 5-10 calls closely. Be ready to pause and adjust if something isn't working."
      }
    ]
  },
  {
    id: "lead-discovery",
    title: "Lead Discovery Guide",
    description: "Find high-intent prospects automatically",
    icon: Target,
    color: "cyan",
    estimatedTime: "5 min",
    steps: [
      {
        title: "Access Lead Discovery",
        content: "Go to Lead Discovery from the sidebar. This is where you'll find new prospects using AI-powered intent signals instead of buying stale lead lists.",
        tip: "AI-discovered leads have 3x higher conversion rates than purchased lists."
      },
      {
        title: "Set Your Filters",
        content: "Select target industry (SaaS, Restaurants, Healthcare, etc.). Choose company size (1-10, 11-50, 51-200, etc.). Set geographic targeting (city, state, or nationwide).",
        tip: "Narrower targeting = higher quality leads. Don't try to boil the ocean."
      },
      {
        title: "Configure Intent Signals",
        content: "Choose which buying signals matter most: Recent funding, Job postings, Tech stack changes, Expansion news, Social media activity. More signals = higher intent.",
        tip: "For B2B SaaS, 'Job postings for roles you solve' is the strongest signal."
      },
      {
        title: "Run Discovery",
        content: "Click 'Discover Leads'. The AI will scan the web and return matching businesses. Each lead shows an ICP score — higher is better. Review the list.",
        tip: "Focus on leads with ICP scores of 70+. Below 50 is usually not worth your time."
      },
      {
        title: "Add to Campaign",
        content: "Check the leads you want to pursue. Click 'Add to Campaign' and select your target campaign. The leads are now queued for your AI to call.",
        tip: "Run discovery weekly to keep your pipeline fresh with new high-intent leads."
      }
    ]
  },
  {
    id: "troubleshooting",
    title: "Troubleshooting Guide",
    description: "Fix common issues quickly",
    icon: Settings,
    color: "red",
    estimatedTime: "As needed",
    steps: [
      {
        title: "Calls Not Going Out",
        content: "Check: 1) Twilio credentials in Settings → Integrations. 2) Campaign is set to 'Active'. 3) You have call credits remaining. 4) Calling hours match current time. 5) Leads have valid phone numbers.",
        tip: "Most common issue: Twilio credentials are wrong or expired. Re-enter them."
      },
      {
        title: "AI Sounds Robotic",
        content: "Fix: 1) Lower the Stability slider to 0.4-0.5. 2) Add natural pauses ('...') to your script. 3) Shorten sentences. 4) Use contractions (don't, we're, you'll). 5) Try the 'Conversational' preset.",
        tip: "Read your script out loud — if it sounds stiff when YOU say it, the AI will too."
      },
      {
        title: "Low Answer Rates",
        content: "Improve: 1) Call during business hours (9-5 local time). 2) Use a local area code if possible. 3) Avoid calling on Mondays and Fridays. 4) Try different times of day.",
        tip: "Tuesday-Thursday, 10-11 AM and 2-4 PM are typically the best calling windows."
      },
      {
        title: "Poor Qualification Rates",
        content: "Fix: 1) Tighten your ICP criteria. 2) Improve your opening hook. 3) Add better objection handling. 4) Make your value proposition clearer. 5) Review call recordings for patterns.",
        tip: "Listen to your best calls — what did the AI say that worked? Double down on that."
      },
      {
        title: "Calendly Not Booking",
        content: "Check: 1) Calendly is connected in Settings. 2) You have available time slots. 3) The AI script includes a booking prompt. 4) Your Calendly link is active and public.",
        tip: "Test the booking flow yourself by calling your own number and asking to book."
      },
      {
        title: "Credits Running Out Fast",
        content: "Optimize: 1) Set max call duration limits. 2) Enable silence detection to end dead calls. 3) Use voicemail detection to skip machines. 4) Focus on higher-quality leads.",
        tip: "Enable 'Auto-hangup on silence' — it saves credits on calls where no one answers."
      }
    ]
  }
];

// FAQ Data
const FAQ_CATEGORIES = [
  {
    id: "getting-started",
    title: "Getting Started",
    icon: Zap,
    questions: [
      {
        q: "How do I set up my first AI agent?",
        a: "Go to Agents → Create Agent. Give it a name, choose a voice preset (or clone your own), write your script, and save. Your agent is ready to make calls!"
      },
      {
        q: "How many free minutes do I get?",
        a: "New accounts get 15 free minutes to test the platform. This is enough for approximately 5-10 demo calls. After that, choose a plan that fits your needs."
      },
      {
        q: "Can I test a call to myself?",
        a: "Yes! On the homepage, enter your phone number and click 'Call Yourself'. You'll receive a call from our demo AI agent within 30 seconds."
      }
    ]
  },
  {
    id: "voice-settings",
    title: "Voice & Audio",
    icon: Volume2,
    questions: [
      {
        q: "What do the voice sliders mean?",
        a: "Stability: Low = more expressive/emotional, High = consistent/robotic. Similarity: How close to the original voice. Style: Low = calm, High = energetic. For sales calls, try Stability 0.4-0.6, Similarity 0.75, Style 0.3-0.4."
      },
      {
        q: "Can I clone my own voice?",
        a: "Yes! Go to Agents → Clone Voice. Upload 1-5 audio samples (MP3/WAV) totaling at least 30 seconds of clear speech. Our AI will create a custom voice that sounds like you."
      },
      {
        q: "Why does my AI sound robotic?",
        a: "Try lowering the Stability slider to 0.4-0.5. This adds more natural variation. Also, make sure your script has natural pauses (use '...' or line breaks) and conversational language."
      },
      {
        q: "Which voice model is best?",
        a: "We use ElevenLabs' multilingual_v2 model — their most natural-sounding option. It handles multiple languages and has the best emotional range."
      }
    ]
  },
  {
    id: "campaigns",
    title: "Campaigns & Calls",
    icon: Phone,
    questions: [
      {
        q: "How many calls can I make per day?",
        a: "This depends on your plan. Starter: 500 calls/month, Growth: 2,000 calls/month, Scale: 10,000 calls/month. You can also set daily limits per campaign."
      },
      {
        q: "What happens if someone doesn't answer?",
        a: "If voicemail is enabled, your AI will leave a message. You can also enable auto-follow-up to retry the call after a set number of hours."
      },
      {
        q: "Can the AI book meetings?",
        a: "Yes! Connect your Calendly in Settings → Integrations. When a lead is qualified, the AI offers available times and books directly to your calendar."
      },
      {
        q: "How do I pause or stop a campaign?",
        a: "Go to Campaigns, find your active campaign, and click the Pause button. You can resume anytime. To stop completely, click the Stop button."
      }
    ]
  },
  {
    id: "leads",
    title: "Leads & Discovery",
    icon: Target,
    questions: [
      {
        q: "How does AI Lead Discovery work?",
        a: "Our AI scans the web for buying signals: job postings, tech stack changes, funding announcements, and more. It finds businesses actively looking for solutions like yours."
      },
      {
        q: "Can I upload my own leads?",
        a: "Yes! Go to Leads → Upload CSV. Your file should have columns for company name, phone number, and optionally: contact name, email, industry."
      },
      {
        q: "What's an ICP score?",
        a: "Ideal Customer Profile score. Higher scores mean the lead matches your target criteria better. Focus your AI's time on leads with scores of 70+."
      }
    ]
  },
  {
    id: "billing",
    title: "Billing & Plans",
    icon: CreditCard,
    questions: [
      {
        q: "How does billing work?",
        a: "We bill monthly based on your plan. Calls are deducted from your monthly allowance. If you exceed your limit, you can upgrade or wait for the next billing cycle."
      },
      {
        q: "Can I cancel anytime?",
        a: "Yes, cancel anytime from Settings → Billing. You'll keep access until the end of your current billing period. No long-term contracts."
      },
      {
        q: "Do unused minutes roll over?",
        a: "No, minutes reset each billing cycle. We recommend right-sizing your plan based on actual usage after the first month."
      }
    ]
  },
  {
    id: "compliance",
    title: "Compliance & Legal",
    icon: Shield,
    questions: [
      {
        q: "Is AI cold calling legal?",
        a: "Yes, when done compliantly. We help you follow TCPA, DNC, and state regulations. Always check local laws and use our compliance tools."
      },
      {
        q: "Does the AI disclose it's an AI?",
        a: "We recommend including disclosure in your script. Many jurisdictions require it. A simple 'I should mention, I'm an AI assistant' works well."
      },
      {
        q: "How do I handle Do Not Call requests?",
        a: "When someone says 'don't call me again', our AI automatically adds them to your DNC list. You can also manage your DNC list in Settings → Compliance."
      }
    ]
  }
];

// Video tutorials with placeholder
const VIDEO_GUIDES = [
  {
    id: "quickstart",
    title: "5-Minute Quickstart",
    description: "Everything you need to make your first AI call",
    duration: "5:00",
    thumbnail: "https://placehold.co/400x225/1e40af/ffffff?text=Quickstart+Guide"
  },
  {
    id: "voice-mastery",
    title: "Voice Tuning Masterclass",
    description: "Make your AI sound perfectly human",
    duration: "8:30",
    thumbnail: "https://placehold.co/400x225/7c3aed/ffffff?text=Voice+Mastery"
  },
  {
    id: "campaigns",
    title: "Campaign Strategy Guide",
    description: "Maximize your conversion rates",
    duration: "12:00",
    thumbnail: "https://placehold.co/400x225/059669/ffffff?text=Campaign+Strategy"
  },
  {
    id: "scripts",
    title: "Writing Winning Scripts",
    description: "AI script templates that convert",
    duration: "10:15",
    thumbnail: "https://placehold.co/400x225/dc2626/ffffff?text=Script+Writing"
  }
];

// Color mapping for guide cards
const colorMap = {
  blue: { bg: "bg-blue-50", border: "border-blue-200", icon: "text-blue-600", badge: "bg-blue-100 text-blue-700" },
  purple: { bg: "bg-purple-50", border: "border-purple-200", icon: "text-purple-600", badge: "bg-purple-100 text-purple-700" },
  green: { bg: "bg-green-50", border: "border-green-200", icon: "text-green-600", badge: "bg-green-100 text-green-700" },
  orange: { bg: "bg-orange-50", border: "border-orange-200", icon: "text-orange-600", badge: "bg-orange-100 text-orange-700" },
  cyan: { bg: "bg-cyan-50", border: "border-cyan-200", icon: "text-cyan-600", badge: "bg-cyan-100 text-cyan-700" },
  red: { bg: "bg-red-50", border: "border-red-200", icon: "text-red-600", badge: "bg-red-100 text-red-700" }
};

// Step-by-Step Guide Component
const GuideCard = ({ guide, isExpanded, onToggle }) => {
  const colors = colorMap[guide.color] || colorMap.blue;
  
  return (
    <Card className={`overflow-hidden border-2 ${isExpanded ? colors.border : 'border-gray-200'} transition-all`}>
      <button
        onClick={onToggle}
        className={`w-full p-6 flex items-center justify-between text-left ${isExpanded ? colors.bg : 'hover:bg-gray-50'}`}
      >
        <div className="flex items-center gap-4">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colors.bg}`}>
            <guide.icon className={`w-6 h-6 ${colors.icon}`} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{guide.title}</h3>
            <p className="text-sm text-gray-500">{guide.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${colors.badge}`}>
            {guide.estimatedTime}
          </span>
          <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
        </div>
      </button>
      
      {isExpanded && (
        <CardContent className="pt-0 pb-6">
          <div className="space-y-4 mt-4">
            {guide.steps.map((step, index) => (
              <div key={index} className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm ${colors.bg} ${colors.icon}`}>
                    {index + 1}
                  </div>
                </div>
                <div className="flex-1 pb-4 border-b border-gray-100 last:border-0">
                  <h4 className="font-medium text-gray-900 mb-2">{step.title}</h4>
                  <p className="text-gray-600 text-sm mb-3">{step.content}</p>
                  {step.tip && (
                    <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3">
                      <Lightbulb className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-amber-800"><strong>Pro tip:</strong> {step.tip}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  );
};

const HelpCenterPage = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedFaq, setExpandedFaq] = useState(null);
  const [expandedGuide, setExpandedGuide] = useState(null);
  const [activeTab, setActiveTab] = useState("guides"); // guides, faq, videos

  // Filter FAQs based on search
  const filteredCategories = FAQ_CATEGORIES.map(cat => ({
    ...cat,
    questions: cat.questions.filter(
      faq => 
        faq.q.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.a.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(cat => cat.questions.length > 0);

  // Filter guides based on search
  const filteredGuides = STEP_BY_STEP_GUIDES.filter(guide =>
    guide.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    guide.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    guide.steps.some(step => 
      step.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      step.content.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 text-white">
        <div className="max-w-6xl mx-auto px-4 py-12">
          <Link to="/app" className="inline-flex items-center gap-2 text-blue-200 hover:text-white mb-6 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
          <h1 className="text-4xl font-bold mb-4">Help Center</h1>
          <p className="text-blue-100 text-lg mb-8">
            Everything you need to master DialGenix AI
          </p>
          
          {/* Search */}
          <div className="relative max-w-xl">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Search guides, FAQs, and more..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 py-6 text-lg bg-white text-gray-900 border-0 rounded-xl shadow-lg"
            />
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Tab Navigation */}
        {!searchQuery && (
          <div className="flex gap-2 mb-8 border-b">
            <button
              onClick={() => setActiveTab("guides")}
              className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                activeTab === "guides" 
                  ? "border-blue-600 text-blue-600" 
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <FileText className="w-4 h-4 inline mr-2" />
              Step-by-Step Guides
            </button>
            <button
              onClick={() => setActiveTab("faq")}
              className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                activeTab === "faq" 
                  ? "border-blue-600 text-blue-600" 
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <HelpCircle className="w-4 h-4 inline mr-2" />
              FAQ
            </button>
            <button
              onClick={() => setActiveTab("videos")}
              className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                activeTab === "videos" 
                  ? "border-blue-600 text-blue-600" 
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <Play className="w-4 h-4 inline mr-2" />
              Video Tutorials
            </button>
          </div>
        )}

        {/* Search Results or Tab Content */}
        {searchQuery ? (
          <div className="space-y-8">
            <h2 className="text-xl font-semibold text-gray-900">
              Search results for "{searchQuery}"
            </h2>
            
            {/* Matching Guides */}
            {filteredGuides.length > 0 && (
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-4">Guides</h3>
                <div className="space-y-4">
                  {filteredGuides.map(guide => (
                    <GuideCard
                      key={guide.id}
                      guide={guide}
                      isExpanded={expandedGuide === guide.id}
                      onToggle={() => setExpandedGuide(expandedGuide === guide.id ? null : guide.id)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Matching FAQs */}
            {filteredCategories.length > 0 && (
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-4">FAQ</h3>
                <div className="space-y-4">
                  {filteredCategories.map(category => (
                    <Card key={category.id}>
                      <CardHeader className="bg-gray-50 border-b py-3">
                        <div className="flex items-center gap-2">
                          <category.icon className="w-5 h-5 text-blue-600" />
                          <CardTitle className="text-base">{category.title}</CardTitle>
                        </div>
                      </CardHeader>
                      <CardContent className="p-0">
                        {category.questions.map((faq, idx) => (
                          <div key={idx} className="border-b last:border-0">
                            <button
                              onClick={() => setExpandedFaq(expandedFaq === `${category.id}-${idx}` ? null : `${category.id}-${idx}`)}
                              className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50"
                            >
                              <span className="font-medium text-gray-900 pr-4">{faq.q}</span>
                              <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${expandedFaq === `${category.id}-${idx}` ? 'rotate-90' : ''}`} />
                            </button>
                            {expandedFaq === `${category.id}-${idx}` && (
                              <div className="px-4 pb-4 text-gray-600 bg-blue-50/50 border-l-4 border-blue-500 ml-4 mr-4 mb-4 rounded-r-lg">
                                <p className="py-3">{faq.a}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {filteredGuides.length === 0 && filteredCategories.length === 0 && (
              <Card className="p-8 text-center">
                <HelpCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
                <p className="text-gray-500 mb-4">Try different search terms</p>
                <Button onClick={() => setSearchQuery("")} variant="outline">
                  Clear Search
                </Button>
              </Card>
            )}
          </div>
        ) : (
          <>
            {/* Step-by-Step Guides Tab */}
            {activeTab === "guides" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">Step-by-Step Guides</h2>
                    <p className="text-gray-500">Detailed walkthroughs for every feature</p>
                  </div>
                </div>
                
                {STEP_BY_STEP_GUIDES.map(guide => (
                  <GuideCard
                    key={guide.id}
                    guide={guide}
                    isExpanded={expandedGuide === guide.id}
                    onToggle={() => setExpandedGuide(expandedGuide === guide.id ? null : guide.id)}
                  />
                ))}
              </div>
            )}

            {/* FAQ Tab */}
            {activeTab === "faq" && (
              <div className="space-y-6">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Frequently Asked Questions</h2>
                  <p className="text-gray-500">Quick answers to common questions</p>
                </div>

                {FAQ_CATEGORIES.map(category => (
                  <Card key={category.id} className="overflow-hidden">
                    <CardHeader className="bg-gray-50 border-b">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                          <category.icon className="w-5 h-5 text-blue-600" />
                        </div>
                        <CardTitle className="text-lg">{category.title}</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent className="p-0">
                      {category.questions.map((faq, idx) => (
                        <div key={idx} className="border-b last:border-0">
                          <button
                            onClick={() => setExpandedFaq(expandedFaq === `${category.id}-${idx}` ? null : `${category.id}-${idx}`)}
                            className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
                          >
                            <span className="font-medium text-gray-900 pr-4">{faq.q}</span>
                            <ChevronRight 
                              className={`w-5 h-5 text-gray-400 flex-shrink-0 transition-transform ${
                                expandedFaq === `${category.id}-${idx}` ? 'rotate-90' : ''
                              }`} 
                            />
                          </button>
                          {expandedFaq === `${category.id}-${idx}` && (
                            <div className="px-4 pb-4 text-gray-600 bg-blue-50/50 border-l-4 border-blue-500 ml-4 mr-4 mb-4 rounded-r-lg">
                              <p className="py-3">{faq.a}</p>
                            </div>
                          )}
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Videos Tab */}
            {activeTab === "videos" && (
              <div>
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Video Tutorials</h2>
                  <p className="text-gray-500">Watch and learn at your own pace</p>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                  {VIDEO_GUIDES.map(video => (
                    <Card key={video.id} className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer group">
                      <div className="relative aspect-video bg-gray-200">
                        <img 
                          src={video.thumbnail} 
                          alt={video.title}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                          <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center">
                            <Play className="w-6 h-6 text-gray-900 ml-1" />
                          </div>
                        </div>
                        <span className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                          {video.duration}
                        </span>
                      </div>
                      <CardContent className="p-4">
                        <h3 className="font-semibold text-gray-900 mb-1">{video.title}</h3>
                        <p className="text-sm text-gray-500">{video.description}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
                  <Headphones className="w-10 h-10 text-amber-600 mx-auto mb-3" />
                  <h3 className="font-semibold text-amber-900 mb-2">Video Tutorials Coming Soon!</h3>
                  <p className="text-amber-700 text-sm">
                    We're recording professional video guides. In the meantime, use our detailed step-by-step text guides above.
                  </p>
                </div>
              </div>
            )}
          </>
        )}

        {/* Contact Section */}
        <div className="mt-12 bg-gradient-to-r from-gray-900 to-gray-800 rounded-2xl p-8 text-white">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-2xl font-bold mb-4">Still need help?</h2>
            <p className="text-gray-300 mb-6">
              Our team is here to help you succeed. Reach out anytime.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button className="bg-white text-gray-900 hover:bg-gray-100">
                <Mail className="w-4 h-4 mr-2" />
                Email Support
              </Button>
              <Button variant="outline" className="border-white text-white hover:bg-white/10">
                <Phone className="w-4 h-4 mr-2" />
                Schedule a Call
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpCenterPage;
