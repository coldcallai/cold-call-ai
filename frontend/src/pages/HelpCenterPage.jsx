import { useState } from "react";
import { Link } from "react-router-dom";
import { 
  HelpCircle, Play, BookOpen, MessageSquare, Mail, Phone,
  ChevronRight, Search, Zap, Users, Settings, Target,
  Mic, Volume2, Calendar, CreditCard, Shield, ArrowLeft
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

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

const HelpCenterPage = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedFaq, setExpandedFaq] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);

  // Filter FAQs based on search
  const filteredCategories = FAQ_CATEGORIES.map(cat => ({
    ...cat,
    questions: cat.questions.filter(
      faq => 
        faq.q.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.a.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(cat => cat.questions.length > 0);

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
              placeholder="Search for answers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 py-6 text-lg bg-white text-gray-900 border-0 rounded-xl shadow-lg"
            />
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Quick Links */}
        {!searchQuery && (
          <div className="grid md:grid-cols-3 gap-4 mb-12">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-blue-200">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Play className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Interactive Tours</h3>
                  <p className="text-sm text-gray-500">Step-by-step walkthroughs</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-purple-200">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                  <BookOpen className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Video Guides</h3>
                  <p className="text-sm text-gray-500">Watch & learn</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-green-200">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                  <MessageSquare className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Live Chat</h3>
                  <p className="text-sm text-gray-500">Talk to our team</p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Video Guides Section */}
        {!searchQuery && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Video Tutorials</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
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
            <p className="text-center text-gray-500 mt-4 text-sm">
              Video tutorials coming soon! Use interactive walkthroughs in the meantime.
            </p>
          </div>
        )}

        {/* FAQ Section */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            {searchQuery ? `Search Results for "${searchQuery}"` : "Frequently Asked Questions"}
          </h2>
          
          {filteredCategories.length === 0 ? (
            <Card className="p-8 text-center">
              <HelpCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
              <p className="text-gray-500 mb-4">Try a different search term or browse categories below</p>
              <Button onClick={() => setSearchQuery("")} variant="outline">
                Clear Search
              </Button>
            </Card>
          ) : (
            <div className="space-y-6">
              {filteredCategories.map(category => (
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
        </div>

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
