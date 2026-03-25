import { useState, useEffect } from "react";
import { 
  X, ChevronRight, ChevronLeft, Check, Search, 
  Megaphone, Users, Phone, Sparkles, Target, Rocket
} from "lucide-react";
import { Button } from "./ui/button";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const OnboardingGuide = ({ user, onComplete, onNavigate }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(true);
  const [isMinimized, setIsMinimized] = useState(false);

  const steps = [
    {
      id: "welcome",
      title: "Welcome to DialGenix.ai!",
      description: "Let's get you set up to find high-intent leads and book meetings with AI-powered calls.",
      icon: Sparkles,
      color: "from-amber-400 to-orange-500",
      action: null,
      tip: "This quick guide will show you the basics. You can always ask the AI assistant for help!"
    },
    {
      id: "keywords",
      title: "Step 1: Set Your Intent Keywords",
      description: "Add keywords that indicate buying intent in YOUR industry. These help AI find businesses actively searching for solutions like yours.",
      icon: Search,
      color: "from-cyan-400 to-teal-500",
      action: { label: "Go to Lead Discovery", path: "/app/leads" },
      tip: "Examples: 'Salesforce alternative', 'best CRM for small business', 'switching from [competitor]'"
    },
    {
      id: "preview",
      title: "Step 2: Preview Example Leads",
      description: "Before using credits, click 'Preview Examples (Free)' to see what kind of leads your keywords will find.",
      icon: Target,
      color: "from-purple-400 to-pink-500",
      action: { label: "Go to Lead Discovery", path: "/app/leads" },
      tip: "This is FREE - use it to test different keyword combinations!"
    },
    {
      id: "discover",
      title: "Step 3: Discover Real Leads",
      description: "Happy with the preview? Click 'Discover High-Intent Leads' to find and save real prospects to your CRM.",
      icon: Search,
      color: "from-green-400 to-emerald-500",
      action: { label: "Go to Lead Discovery", path: "/app/leads" },
      tip: "Start with 10-20 leads to test your campaign before scaling up."
    },
    {
      id: "campaign",
      title: "Step 4: Create Your Campaign",
      description: "Set up an AI calling campaign with your script. Include: introduction, qualifying questions, objection handling, and meeting booking.",
      icon: Megaphone,
      color: "from-blue-400 to-indigo-500",
      action: { label: "Go to Campaigns", path: "/app/campaigns" },
      tip: "Good scripts sound natural and focus on understanding the prospect's pain points."
    },
    {
      id: "agents",
      title: "Step 5: Add Your Agents",
      description: "Add human agents who will receive qualified leads. Each agent needs their Calendly link for AI to book meetings.",
      icon: Users,
      color: "from-violet-400 to-purple-500",
      action: { label: "Go to Agents", path: "/app/agents" },
      tip: "AI qualifies leads first, then routes hot prospects to your human agents."
    },
    {
      id: "launch",
      title: "Step 6: Launch & Monitor",
      description: "Assign leads to your campaign, start it, and watch the AI make calls. Monitor results in Call History.",
      icon: Rocket,
      color: "from-rose-400 to-red-500",
      action: { label: "Go to Call History", path: "/app/calls" },
      tip: "Review call recordings and transcripts to improve your script over time."
    },
    {
      id: "complete",
      title: "You're All Set!",
      description: "You now know the basics. Remember: the AI assistant is always here to help if you get stuck.",
      icon: Check,
      color: "from-green-400 to-emerald-500",
      action: null,
      tip: "Pro tip: Start small, test your keywords and script, then scale up once you see results!"
    }
  ];

  const handleComplete = async () => {
    try {
      const token = localStorage.getItem("session_token");
      await axios.post(
        `${API}/user/onboarding-complete`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (error) {
      console.error("Failed to save onboarding status:", error);
    }
    setIsVisible(false);
    onComplete?.();
  };

  const handleAction = (path) => {
    onNavigate?.(path);
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  if (!isVisible) return null;

  const step = steps[currentStep];
  const Icon = step.icon;

  if (isMinimized) {
    return (
      <button
        onClick={() => setIsMinimized(false)}
        className="fixed bottom-6 left-6 z-40 px-4 py-2 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-full shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
        data-testid="onboarding-minimized"
      >
        <Sparkles className="w-4 h-4" />
        <span className="text-sm font-medium">Continue Setup ({currentStep + 1}/{steps.length})</span>
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      data-testid="onboarding-overlay">
      <div className="relative w-full max-w-lg mx-4 bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Progress Bar */}
        <div className="h-1 bg-gray-100">
          <div 
            className="h-full bg-gradient-to-r from-cyan-500 to-teal-500 transition-all duration-300"
            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          />
        </div>

        {/* Header */}
        <div className={`bg-gradient-to-r ${step.color} p-6 text-white`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                <Icon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-white/80 text-sm">
                  {currentStep === 0 ? "Getting Started" : `Step ${currentStep} of ${steps.length - 2}`}
                </p>
                <h2 className="text-xl font-bold">{step.title}</h2>
              </div>
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => setIsMinimized(true)}
                className="p-1 hover:bg-white/20 rounded transition-colors text-white/80 hover:text-white"
                title="Minimize"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={handleComplete}
                className="p-1 hover:bg-white/20 rounded transition-colors text-white/80 hover:text-white"
                title="Skip tutorial"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-600 mb-4">{step.description}</p>
          
          {/* Tip Box */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-6">
            <p className="text-sm text-amber-800">
              <span className="font-semibold">💡 Tip:</span> {step.tip}
            </p>
          </div>

          {/* Action Button */}
          {step.action && (
            <Button
              onClick={() => handleAction(step.action.path)}
              className="w-full mb-4 bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600"
              data-testid="onboarding-action"
            >
              {step.action.label}
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="px-6 pb-6 flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={prevStep}
            disabled={currentStep === 0}
            className="text-gray-500"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Back
          </Button>

          <div className="flex gap-1">
            {steps.map((_, idx) => (
              <div
                key={idx}
                className={`w-2 h-2 rounded-full transition-colors ${
                  idx === currentStep ? "bg-cyan-500" : idx < currentStep ? "bg-cyan-200" : "bg-gray-200"
                }`}
              />
            ))}
          </div>

          <Button
            onClick={nextStep}
            className={currentStep === steps.length - 1 
              ? "bg-green-500 hover:bg-green-600" 
              : "bg-cyan-500 hover:bg-cyan-600"
            }
          >
            {currentStep === steps.length - 1 ? (
              <>
                <Check className="w-4 h-4 mr-1" />
                Done
              </>
            ) : (
              <>
                Next
                <ChevronRight className="w-4 h-4 ml-1" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default OnboardingGuide;
