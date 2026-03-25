import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { 
  X, ChevronRight, ChevronLeft, CheckCircle, Circle, Phone, Calendar, 
  Shield, Users, Megaphone, Rocket, ExternalLink, Lock, Unlock, Sparkles,
  AlertTriangle, ArrowRight
} from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const SetupWizard = ({ user, onComplete, onNavigate }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(true);
  const [isMinimized, setIsMinimized] = useState(false);
  const [setupStatus, setSetupStatus] = useState(null);
  const navigate = useNavigate();

  const fetchSetupStatus = useCallback(async () => {
    try {
      const token = localStorage.getItem("session_token");
      const response = await axios.get(`${API}/setup/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSetupStatus(response.data);
    } catch (error) {
      console.error("Failed to fetch setup status:", error);
    }
  }, []);

  useEffect(() => {
    fetchSetupStatus();
  }, [fetchSetupStatus]);

  const steps = [
    {
      id: "welcome",
      title: "Welcome to DialGenix.ai!",
      description: "Let's get your AI cold calling system set up. This wizard will guide you through connecting the required services.",
      icon: Sparkles,
      color: "from-amber-400 to-orange-500",
      isSetupStep: false,
      tips: [
        "This takes about 10-15 minutes to complete",
        "You'll need accounts with Twilio and Calendly",
        "All steps can be revisited from the 'Getting Started' page"
      ]
    },
    {
      id: "twilio",
      title: "Step 1: Connect Twilio Voice",
      description: "Twilio powers the real phone calls. You need Account SID, Auth Token, and a phone number.",
      icon: Phone,
      color: "from-red-400 to-rose-500",
      isSetupStep: true,
      path: "/app/settings",
      externalUrl: "https://console.twilio.com",
      tips: [
        "Create a free Twilio account at twilio.com",
        "Copy your Account SID and Auth Token from the dashboard",
        "Buy a phone number with Voice capability (~$1/month)"
      ]
    },
    {
      id: "calendly",
      title: "Step 2: Set Up Calendly",
      description: "Calendly lets the AI book meetings directly into your calendar when leads are qualified.",
      icon: Calendar,
      color: "from-blue-400 to-indigo-500",
      isSetupStep: true,
      path: "/app/agents",
      externalUrl: "https://calendly.com",
      tips: [
        "Create a free Calendly account",
        "Set up an event type (e.g., '30 Min Discovery Call')",
        "You'll add the booking link when creating an Agent"
      ]
    },
    {
      id: "compliance",
      title: "Step 3: Complete Compliance",
      description: "Acknowledge TCPA regulations and choose between B2B (free) or B2C calling mode.",
      icon: Shield,
      color: "from-amber-400 to-yellow-500",
      isSetupStep: true,
      path: "/app/compliance",
      externalUrl: null,
      tips: [
        "B2B calling is recommended - $0 compliance cost",
        "B2C requires FTC registration and DNC data purchase",
        "Review calling hour restrictions (8am-9pm local time)"
      ]
    },
    {
      id: "agent",
      title: "Step 4: Create an Agent",
      description: "Agents are your human salespeople who receive qualified leads and take meetings.",
      icon: Users,
      color: "from-purple-400 to-violet-500",
      isSetupStep: true,
      path: "/app/agents",
      externalUrl: null,
      tips: [
        "Enter the agent's name, email, and Calendly link",
        "They'll receive email notifications for qualified leads",
        "AI books meetings directly into their Calendly"
      ]
    },
    {
      id: "campaign",
      title: "Step 5: Create a Campaign",
      description: "Set up your AI calling script - introduction, qualifying questions, and objection handling.",
      icon: Megaphone,
      color: "from-emerald-400 to-teal-500",
      isSetupStep: true,
      path: "/app/campaigns",
      externalUrl: null,
      tips: [
        "Write a natural-sounding script",
        "Include qualifying questions to identify decision makers",
        "Set ICP criteria to score leads before calling"
      ]
    },
    {
      id: "complete",
      title: "You're All Set!",
      description: "Your AI cold calling system is ready. Start discovering leads and launching campaigns!",
      icon: Rocket,
      color: "from-green-400 to-emerald-500",
      isSetupStep: false,
      tips: [
        "Go to Lead Discovery to find high-intent prospects",
        "Assign leads to your campaign and start calling",
        "Monitor results in Call History and Bookings"
      ]
    }
  ];

  const handleComplete = async () => {
    try {
      const token = localStorage.getItem("session_token");
      await axios.post(
        `${API}/user/setup-wizard-complete`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (error) {
      console.error("Failed to save wizard status:", error);
    }
    setIsVisible(false);
    onComplete?.();
  };

  const handleSkip = () => {
    // Skip wizard but don't mark as complete
    setIsVisible(false);
    onComplete?.();
    toast.info("Setup wizard skipped. You can access it from 'Getting Started' in the menu.");
  };

  const handleGoTo = (path) => {
    setIsMinimized(true);
    if (onNavigate) {
      onNavigate(path);
    } else {
      navigate(path);
    }
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

  const getStepStatus = (stepId) => {
    if (!setupStatus?.steps) return "pending";
    const step = setupStatus.steps.find(s => s.id === stepId);
    return step?.completed ? "completed" : "pending";
  };

  if (!isVisible) return null;

  const step = steps[currentStep];
  const Icon = step.icon;
  const isStepComplete = step.isSetupStep && getStepStatus(step.id) === "completed";

  // Calculate progress
  const setupSteps = steps.filter(s => s.isSetupStep);
  const completedSteps = setupSteps.filter(s => getStepStatus(s.id) === "completed").length;
  const progressPercent = Math.round((completedSteps / setupSteps.length) * 100);

  if (isMinimized) {
    return (
      <button
        onClick={() => setIsMinimized(false)}
        className="fixed bottom-24 left-6 z-40 px-4 py-3 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-full shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
        data-testid="setup-wizard-minimized"
      >
        <Rocket className="w-5 h-5" />
        <span className="text-sm font-medium">Continue Setup ({completedSteps}/{setupSteps.length})</span>
      </button>
    );
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      data-testid="setup-wizard-overlay"
    >
      <div className="relative w-full max-w-xl mx-4 bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Progress Bar */}
        <div className="h-1.5 bg-gray-100">
          <div 
            className="h-full bg-gradient-to-r from-cyan-500 to-teal-500 transition-all duration-500"
            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          />
        </div>

        {/* Header */}
        <div className={`bg-gradient-to-r ${step.color} p-6 text-white`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                <Icon className="w-7 h-7" />
              </div>
              <div>
                <p className="text-white/80 text-sm font-medium">
                  {step.isSetupStep ? `Step ${currentStep} of ${steps.length - 2}` : currentStep === 0 ? "Getting Started" : "Complete!"}
                </p>
                <h2 className="text-2xl font-bold">{step.title}</h2>
              </div>
            </div>
            <button
              onClick={handleSkip}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors text-white/80 hover:text-white"
              title="Skip for now"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* Step status indicator for setup steps */}
          {step.isSetupStep && (
            <div className="mt-4 flex items-center gap-2">
              <Badge 
                className={isStepComplete 
                  ? "bg-white/30 text-white border-white/50" 
                  : "bg-white/20 text-white/90 border-white/30"}
              >
                {isStepComplete ? (
                  <><CheckCircle className="w-3 h-3 mr-1" /> Completed</>
                ) : (
                  <><Circle className="w-3 h-3 mr-1" /> Pending</>
                )}
              </Badge>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-600 text-lg mb-4">{step.description}</p>
          
          {/* Tips Box */}
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 mb-6">
            <h4 className="font-medium text-gray-800 mb-2 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              {step.isSetupStep ? "Quick Tips" : "What's Next"}
            </h4>
            <ul className="space-y-2">
              {step.tips.map((tip, idx) => (
                <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-cyan-500 shrink-0 mt-0.5" />
                  {tip}
                </li>
              ))}
            </ul>
          </div>

          {/* Action Buttons for setup steps */}
          {step.isSetupStep && (
            <div className="flex gap-3 mb-4">
              <Button
                onClick={() => handleGoTo(step.path)}
                className={`flex-1 ${isStepComplete ? "bg-green-500 hover:bg-green-600" : "bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600"}`}
                data-testid="setup-wizard-action"
              >
                {isStepComplete ? (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Review Settings
                  </>
                ) : (
                  <>
                    <ArrowRight className="w-4 h-4 mr-2" />
                    Go to Setup
                  </>
                )}
              </Button>
              {step.externalUrl && (
                <Button variant="outline" asChild>
                  <a href={step.externalUrl} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Open
                  </a>
                </Button>
              )}
            </div>
          )}

          {/* Completion action */}
          {currentStep === steps.length - 1 && (
            <Button
              onClick={() => handleGoTo("/app/leads")}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
              data-testid="setup-wizard-start-calling"
            >
              <Rocket className="w-4 h-4 mr-2" />
              Start Discovering Leads
            </Button>
          )}
        </div>

        {/* Setup Progress Overview (shown on non-setup steps) */}
        {!step.isSetupStep && setupStatus && (
          <div className="px-6 pb-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-blue-800">Setup Progress</span>
                <span className="text-sm font-bold text-blue-900">{progressPercent}%</span>
              </div>
              <Progress value={progressPercent} className="h-2" />
              <p className="text-xs text-blue-600 mt-2">
                {completedSteps}/{setupSteps.length} steps complete
              </p>
            </div>
          </div>
        )}

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

          <div className="flex gap-1.5">
            {steps.map((_, idx) => (
              <div
                key={idx}
                className={`w-2.5 h-2.5 rounded-full transition-all ${
                  idx === currentStep 
                    ? "bg-cyan-500 scale-125" 
                    : idx < currentStep 
                      ? "bg-cyan-300" 
                      : "bg-gray-200"
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
                <CheckCircle className="w-4 h-4 mr-1" />
                Done
              </>
            ) : (
              <>
                {step.isSetupStep && !isStepComplete ? "Skip for Now" : "Next"}
                <ChevronRight className="w-4 h-4 ml-1" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SetupWizard;
