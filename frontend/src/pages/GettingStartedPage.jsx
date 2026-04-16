import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { 
  CheckCircle, Circle, ChevronRight, Phone, Calendar, Shield, Users,
  Settings, Database, AlertTriangle, Rocket, ExternalLink, Lock, Unlock,
  Sparkles, Target, Search, Megaphone, HelpCircle, RefreshCw, Play, PhoneCall, Mic
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Call Yourself Demo Component
const CallYourselfDemo = () => {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [demoInfo, setDemoInfo] = useState(null);

  useEffect(() => {
    const fetchDemoInfo = async () => {
      try {
        const token = localStorage.getItem("session_token");
        const response = await axios.get(`${API}/demo/calls-remaining`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setDemoInfo(response.data);
      } catch (error) {
        console.error("Failed to fetch demo info:", error);
      }
    };
    fetchDemoInfo();
  }, []);

  const handleCallYourself = async () => {
    if (!phoneNumber.trim()) {
      toast.error("Please enter your phone number");
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem("session_token");
      const response = await axios.post(
        `${API}/demo/call-yourself`,
        { phone_number: phoneNumber },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(response.data.message);
      setDemoInfo(prev => ({
        ...prev,
        demo_calls_remaining: response.data.demo_calls_remaining
      }));
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to initiate demo call");
    } finally {
      setLoading(false);
    }
  };

  const remainingCalls = demoInfo?.demo_calls_remaining ?? 2;

  return (
    <Card className="bg-gradient-to-r from-purple-50 to-indigo-50 border-purple-200">
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
            <PhoneCall className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-bold text-gray-900">Experience the AI Voice</h3>
              <Badge className="bg-purple-100 text-purple-700">{remainingCalls} free calls</Badge>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Call your own phone to hear exactly what your prospects will experience. No leads required!
            </p>
            
            {remainingCalls > 0 ? (
              <div className="flex items-end gap-3">
                <div className="flex-1 max-w-xs">
                  <Label htmlFor="demo-phone" className="text-sm text-gray-700">Your Phone Number</Label>
                  <Input
                    id="demo-phone"
                    type="tel"
                    placeholder="+1 (555) 123-4567"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    className="mt-1"
                    data-testid="demo-phone-input"
                  />
                </div>
                <Button
                  onClick={handleCallYourself}
                  disabled={loading}
                  className="bg-purple-600 hover:bg-purple-700 text-white"
                  data-testid="call-yourself-btn"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Calling...
                    </>
                  ) : (
                    <>
                      <Phone className="w-4 h-4 mr-2" />
                      Call Me Now
                    </>
                  )}
                </Button>
              </div>
            ) : (
              <div className="bg-gray-100 rounded-lg p-4 text-center">
                <p className="text-gray-600 text-sm">
                  You've used your free demo calls. Subscribe to a plan to make more calls!
                </p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const GettingStartedPage = () => {
  const navigate = useNavigate();
  const [setupStatus, setSetupStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchSetupStatus = useCallback(async () => {
    try {
      const token = localStorage.getItem("session_token");
      const response = await axios.get(`${API}/setup/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSetupStatus(response.data);
      
      // If setup is complete and wizard was completed, redirect to Funnel
      if (response.data.all_required_complete && response.data.setup_wizard_completed) {
        navigate("/app", { replace: true });
      }
    } catch (error) {
      console.error("Failed to fetch setup status:", error);
      toast.error("Failed to load setup status");
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchSetupStatus();
  }, [fetchSetupStatus]);

  const setupSteps = [
    {
      id: "twilio",
      title: "Connect Twilio Voice",
      description: "Enable real outbound calls by connecting your Twilio account",
      icon: Phone,
      color: "bg-red-500",
      bgLight: "bg-red-50",
      borderColor: "border-red-200",
      required: true,
      path: "/app/settings",
      instructions: [
        "Go to twilio.com and create an account (or log in)",
        "Get your Account SID and Auth Token from the dashboard",
        "Purchase a phone number with voice capability",
        "Add your Twilio credentials in the Settings page below"
      ],
      externalLink: "https://console.twilio.com",
      externalLinkText: "Open Twilio Console"
    },
    {
      id: "elevenlabs",
      title: "Connect ElevenLabs Voice",
      description: "Enable natural AI voice for your calls",
      icon: Mic,
      color: "bg-violet-500",
      bgLight: "bg-violet-50",
      borderColor: "border-violet-200",
      required: true,
      path: "/app/settings",
      instructions: [
        "Go to elevenlabs.io and create an account",
        "Navigate to Profile + API Key section",
        "Copy your API key",
        "Add your ElevenLabs API key in the Settings page below"
      ],
      externalLink: "https://elevenlabs.io",
      externalLinkText: "Open ElevenLabs"
    },
    {
      id: "calendly",
      title: "Set Up Calendly Booking",
      description: "Allow AI to book meetings directly into your calendar",
      icon: Calendar,
      color: "bg-blue-500",
      bgLight: "bg-blue-50",
      borderColor: "border-blue-200",
      required: true,
      path: "/app/agents",
      instructions: [
        "Create a Calendly account at calendly.com (free tier works)",
        "Set up an event type for sales meetings (e.g., '30 Min Discovery Call')",
        "Copy your booking link",
        "Add the Calendly link when creating an Agent in DialGenix"
      ],
      externalLink: "https://calendly.com",
      externalLinkText: "Open Calendly"
    },
    {
      id: "compliance",
      title: "Complete Compliance Setup",
      description: "Acknowledge TCPA regulations and choose your calling mode",
      icon: Shield,
      color: "bg-amber-500",
      bgLight: "bg-amber-50",
      borderColor: "border-amber-200",
      required: true,
      path: "/app/compliance",
      instructions: [
        "Choose between B2B (business-only) or B2C (consumer) calling mode",
        "B2B is recommended - $0 compliance cost, no FTC registration needed",
        "Read and acknowledge all compliance requirements",
        "If B2C: Go to telemarketing.donotcall.gov and register your organization ($75/area code/year)",
        "If B2C: After registration, log into the FTC portal and download the Do Not Call list as a CSV file",
        "If B2C: In DialGenix, go to Compliance > DNC Management > click 'Upload DNC List' and upload the CSV you downloaded from FTC. This prevents your AI from calling numbers on the national Do Not Call registry."
      ],
      externalLink: null,
      externalLinkText: null
    },
    {
      id: "agent",
      title: "Create Your First Agent",
      description: "Add a sales agent who will receive qualified leads",
      icon: Users,
      color: "bg-purple-500",
      bgLight: "bg-purple-50",
      borderColor: "border-purple-200",
      required: true,
      path: "/app/agents",
      instructions: [
        "Go to the Agents page",
        "Click 'Create Agent'",
        "Enter agent name, email, and Calendly booking link",
        "The agent will receive notifications for qualified leads"
      ],
      externalLink: null,
      externalLinkText: null
    },
    {
      id: "campaign",
      title: "Create a Campaign",
      description: "Set up your AI calling script and qualification criteria",
      icon: Megaphone,
      color: "bg-emerald-500",
      bgLight: "bg-emerald-50",
      borderColor: "border-emerald-200",
      required: true,
      path: "/app/campaigns",
      instructions: [
        "Go to the Campaigns page",
        "Click 'Create Campaign'",
        "Write your AI calling script with introduction, questions, and objection handling",
        "Set ICP criteria to score leads"
      ],
      externalLink: null,
      externalLinkText: null
    },
    {
      id: "crm",
      title: "Connect CRM (Optional)",
      description: "Auto-sync qualified leads to GoHighLevel, Salesforce, or HubSpot",
      icon: Database,
      color: "bg-cyan-500",
      bgLight: "bg-cyan-50",
      borderColor: "border-cyan-200",
      required: false,
      path: "/app/integrations",
      instructions: [
        "Go to the CRM Integrations page",
        "Click 'Connect' on your preferred CRM",
        "Enter your CRM API key",
        "Qualified leads will automatically sync"
      ],
      externalLink: null,
      externalLinkText: null
    }
  ];

  const getStepStatus = (stepId) => {
    if (!setupStatus?.steps) return "pending";
    const step = setupStatus.steps.find(s => s.id === stepId);
    return step?.completed ? "completed" : "pending";
  };

  const completedCount = setupStatus?.steps?.filter(s => s.completed).length || 0;
  const requiredCount = setupSteps.filter(s => s.required).length;
  const requiredCompleted = setupStatus?.steps?.filter(s => {
    const stepDef = setupSteps.find(def => def.id === s.id);
    return stepDef?.required && s.completed;
  }).length || 0;
  const allRequiredComplete = requiredCompleted >= requiredCount;
  const progressPercent = setupStatus?.completion_percentage || 0;

  if (loading) {
    return (
      <div className="p-6 md:p-8 space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-24" />
        <div className="grid gap-4">
          {[1, 2, 3, 4, 5].map(i => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-4xl mx-auto" data-testid="getting-started-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="w-14 h-14 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-2xl flex items-center justify-center shadow-lg">
          <Rocket className="w-7 h-7 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Getting Started
          </h1>
          <p className="text-gray-500">Complete these steps to start making AI calls</p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          className="ml-auto"
          onClick={fetchSetupStatus}
          data-testid="refresh-setup-status"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Progress Card */}
      <Card className={`${allRequiredComplete ? "bg-gradient-to-r from-green-50 to-emerald-50 border-green-200" : "bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200"}`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Setup Progress</h2>
              <p className="text-sm text-gray-600">
                {allRequiredComplete 
                  ? "All required steps complete! You're ready to make calls."
                  : `${requiredCompleted} of ${requiredCount} required steps complete`}
              </p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-gray-900">{progressPercent}%</p>
              <Badge className={allRequiredComplete ? "bg-green-100 text-green-800" : "bg-blue-100 text-blue-800"}>
                {allRequiredComplete ? "Ready to Call" : "Setup Incomplete"}
              </Badge>
            </div>
          </div>
          <Progress value={progressPercent} className="h-3" />
        </CardContent>
      </Card>

      {/* Warning if not ready */}
      {!allRequiredComplete && (
        <Alert className="bg-amber-50 border-amber-200">
          <Lock className="h-5 w-5 text-amber-600" />
          <AlertTitle className="text-amber-800">Calling Features Locked</AlertTitle>
          <AlertDescription className="text-amber-700">
            Complete all required setup steps below to unlock AI calling features. 
            Steps marked with <span className="font-semibold text-red-600">*</span> are required.
          </AlertDescription>
        </Alert>
      )}

      {/* Success Banner */}
      {allRequiredComplete && (
        <Alert className="bg-green-50 border-green-200">
          <Unlock className="h-5 w-5 text-green-600" />
          <AlertTitle className="text-green-800">You're All Set!</AlertTitle>
          <AlertDescription className="text-green-700">
            All required setup steps are complete. You can now discover leads and start AI calling campaigns.
            <Button 
              className="ml-4 bg-green-600 hover:bg-green-700"
              size="sm"
              onClick={() => navigate("/app/leads")}
            >
              <Play className="w-4 h-4 mr-2" />
              Start Discovering Leads
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Call Yourself Demo */}
      <CallYourselfDemo />

      {/* Setup Steps */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Setup Steps</h3>
        
        {setupSteps.map((step, index) => {
          const status = getStepStatus(step.id);
          const isCompleted = status === "completed";
          const Icon = step.icon;

          return (
            <Card 
              key={step.id}
              className={`transition-all ${isCompleted ? "bg-green-50/50 border-green-200" : `${step.bgLight} ${step.borderColor}`}`}
              data-testid={`setup-step-${step.id}`}
            >
              <CardContent className="p-0">
                <Accordion type="single" collapsible>
                  <AccordionItem value={step.id} className="border-none">
                    <AccordionTrigger className="px-6 py-4 hover:no-underline">
                      <div className="flex items-center gap-4 flex-1 text-left">
                        <div className={`w-10 h-10 ${isCompleted ? "bg-green-500" : step.color} rounded-xl flex items-center justify-center text-white shadow-sm`}>
                          {isCompleted ? (
                            <CheckCircle className="w-5 h-5" />
                          ) : (
                            <Icon className="w-5 h-5" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold text-gray-900">
                              {index + 1}. {step.title}
                            </h4>
                            {step.required && !isCompleted && (
                              <span className="text-red-500 font-bold">*</span>
                            )}
                            {!step.required && (
                              <Badge variant="outline" className="text-xs">Optional</Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600">{step.description}</p>
                        </div>
                        <Badge 
                          className={isCompleted 
                            ? "bg-green-100 text-green-800" 
                            : "bg-gray-100 text-gray-600"}
                        >
                          {isCompleted ? (
                            <><CheckCircle className="w-3 h-3 mr-1" /> Complete</>
                          ) : (
                            <><Circle className="w-3 h-3 mr-1" /> Pending</>
                          )}
                        </Badge>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="px-6 pb-6">
                      <div className="ml-14 space-y-4">
                        {/* Instructions */}
                        <div className="bg-white rounded-lg border border-gray-200 p-4">
                          <h5 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                            <HelpCircle className="w-4 h-4 text-gray-500" />
                            How to complete this step:
                          </h5>
                          <ol className="space-y-2">
                            {step.instructions.map((instruction, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                                <span className="w-5 h-5 bg-gray-100 rounded-full flex items-center justify-center text-xs font-medium text-gray-700 shrink-0 mt-0.5">
                                  {idx + 1}
                                </span>
                                {instruction}
                              </li>
                            ))}
                          </ol>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-3">
                          <Button 
                            onClick={() => navigate(step.path)}
                            className={isCompleted ? "bg-gray-500 hover:bg-gray-600" : `${step.color} hover:opacity-90`}
                            data-testid={`goto-${step.id}`}
                          >
                            {isCompleted ? "Review" : "Go to Setup"}
                            <ChevronRight className="w-4 h-4 ml-2" />
                          </Button>
                          {step.externalLink && (
                            <Button variant="outline" asChild>
                              <a href={step.externalLink} target="_blank" rel="noopener noreferrer">
                                {step.externalLinkText}
                                <ExternalLink className="w-4 h-4 ml-2" />
                              </a>
                            </Button>
                          )}
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Help Section */}
      <Card className="bg-gradient-to-r from-gray-50 to-slate-50 border-gray-200">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-gray-600" />
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Need Help?</h4>
              <p className="text-sm text-gray-600 mt-1">
                Use the AI Help Chat in the bottom-right corner to ask questions anytime. 
                It can guide you through any setup step or explain features.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GettingStartedPage;
