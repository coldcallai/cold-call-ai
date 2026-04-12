import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { 
  Phone, Mic, Bot, CheckCircle, ArrowRight, ArrowLeft, 
  ExternalLink, Eye, EyeOff, Loader2,
  DollarSign, AlertTriangle, Bell
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;

const SetupWizard = ({ user, onComplete, onNavigate }) => {
  const routerNavigate = useNavigate();
  const navigate = onNavigate || routerNavigate;
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [showTokens, setShowTokens] = useState({});
  
  // Form data
  const [twilioData, setTwilioData] = useState({
    account_sid: "",
    auth_token: "",
    phone_number: ""
  });
  
  const [elevenLabsData, setElevenLabsData] = useState({
    api_key: ""
  });
  
  // Validation states
  const [twilioVerified, setTwilioVerified] = useState(false);
  const [elevenLabsVerified, setElevenLabsVerified] = useState(false);
  
  // Balance info
  const [twilioBalance, setTwilioBalance] = useState(null);
  const [elevenLabsCredits, setElevenLabsCredits] = useState(null);

  const totalSteps = 4;

  // Pre-load integration status on mount
  useEffect(() => {
    const loadStatus = async () => {
      try {
        const token = localStorage.getItem("session_token");
        if (!token) return;
        const { data } = await axios.get(`${API}/api/settings/integrations/status`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (data.twilio_connected) {
          setTwilioVerified(true);
          if (data.twilio_phone_number) {
            setTwilioData(prev => ({ ...prev, phone_number: data.twilio_phone_number }));
          }
        }
        if (data.elevenlabs_connected) setElevenLabsVerified(true);
      } catch { /* ignore */ }
    };
    loadStatus();
  }, []);

  const verifyTwilio = async () => {
    if (!twilioData.account_sid || !twilioData.auth_token) {
      toast.error("Please enter both Account SID and Auth Token");
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/api/settings/verify-twilio`, twilioData, {
        headers: { Authorization: `Bearer ${localStorage.getItem("session_token")}` }
      });
      
      if (response.data.valid) {
        setTwilioVerified(true);
        setTwilioBalance(response.data.balance);
        toast.success("Twilio connected successfully!");
      } else {
        toast.error(response.data.message || "Invalid Twilio credentials");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to verify Twilio credentials");
    } finally {
      setLoading(false);
    }
  };

  const verifyElevenLabs = async () => {
    if (!elevenLabsData.api_key) {
      toast.error("Please enter your ElevenLabs API key");
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/api/settings/verify-elevenlabs`, elevenLabsData, {
        headers: { Authorization: `Bearer ${localStorage.getItem("session_token")}` }
      });
      
      if (response.data.valid) {
        setElevenLabsVerified(true);
        setElevenLabsCredits(response.data.credits);
        toast.success("ElevenLabs connected successfully!");
      } else {
        toast.error(response.data.message || "Invalid ElevenLabs API key");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to verify ElevenLabs credentials");
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/api/settings/integrations`, {
        twilio: twilioData,
        elevenlabs: elevenLabsData
      }, {
        headers: { Authorization: `Bearer ${localStorage.getItem("session_token")}` }
      });
      
      toast.success("Settings saved!");
      if (onComplete) onComplete();
      navigate("/app/agents");
    } catch (error) {
      toast.error("Failed to save settings");
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Bot className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Welcome to DialGenix!</h2>
              <p className="text-gray-600 mt-2">Let's get your AI sales agent up and running in about 10 minutes.</p>
            </div>

            {/* Why BYOK is better */}
            <div className="bg-gradient-to-r from-emerald-50 to-cyan-50 border border-emerald-200 rounded-xl p-5">
              <h3 className="font-semibold text-emerald-800 flex items-center gap-2 mb-3">
                <DollarSign className="w-5 h-5" />
                Why You Pay Less With Us
              </h3>
              <div className="space-y-2 text-sm text-emerald-700">
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span><strong>No markup on voice/calls</strong> — Pay Twilio & ElevenLabs directly at their rates</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span><strong>Full transparency</strong> — See exactly what you're paying, no hidden fees</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span><strong>You control costs</strong> — Scale up or down anytime</span>
                </div>
              </div>
            </div>

            {/* Cost comparison */}
            <div className="bg-gray-50 rounded-xl p-5">
              <h3 className="font-semibold text-gray-800 mb-3">Typical Monthly Cost</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white rounded-lg p-4 border-2 border-emerald-200">
                  <p className="text-sm text-gray-500">DialGenix</p>
                  <p className="text-2xl font-bold text-emerald-600">$130-250</p>
                  <p className="text-xs text-emerald-600">No hidden fees</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-gray-200 opacity-60">
                  <p className="text-sm text-gray-500">Competitors</p>
                  <p className="text-2xl font-bold text-gray-400">$200-400</p>
                  <p className="text-xs text-gray-400">Hidden markups</p>
                </div>
              </div>
            </div>

            {/* Steps overview */}
            <div className="space-y-3">
              <p className="text-sm font-medium text-gray-700">Quick setup (10 min):</p>
              <div className="space-y-2">
                {[
                  { icon: Phone, label: "Connect Twilio (phone calls)", time: "3 min" },
                  { icon: Mic, label: "Connect ElevenLabs (AI voice)", time: "2 min" },
                  { icon: Bot, label: "Create your AI agent", time: "5 min" }
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-100">
                    <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                      <item.icon className="w-4 h-4 text-gray-600" />
                    </div>
                    <span className="flex-1 text-sm text-gray-700">{item.label}</span>
                    <span className="text-xs text-gray-400">{item.time}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-red-500 to-pink-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Phone className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Connect Twilio</h2>
              <p className="text-gray-600 mt-2">Twilio handles phone calls. ~$0.02/min, billed directly to you.</p>
            </div>

            {/* Don't have Twilio? */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <p className="text-sm text-blue-800 font-medium">Don't have Twilio?</p>
              <p className="text-sm text-blue-600 mt-1">Create an account in 2 min. Get $15 free credit.</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3 text-blue-700 border-blue-300 hover:bg-blue-100"
                onClick={() => window.open("https://www.twilio.com/try-twilio", "_blank")}
              >
                Create Twilio Account <ExternalLink className="w-3 h-3 ml-2" />
              </Button>
            </div>

            {/* Input fields */}
            <div className="space-y-4">
              <div>
                <Label>Account SID</Label>
                <Input
                  value={twilioData.account_sid}
                  onChange={(e) => setTwilioData({ ...twilioData, account_sid: e.target.value })}
                  placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                  className="mt-1 font-mono text-sm"
                />
              </div>

              <div>
                <Label>Auth Token</Label>
                <div className="relative mt-1">
                  <Input
                    type={showTokens.twilio ? "text" : "password"}
                    value={twilioData.auth_token}
                    onChange={(e) => setTwilioData({ ...twilioData, auth_token: e.target.value })}
                    placeholder="Your auth token"
                    className="pr-10 font-mono text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowTokens({ ...showTokens, twilio: !showTokens.twilio })}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showTokens.twilio ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <Label>Twilio Phone Number <span className="text-gray-400 font-normal">(optional)</span></Label>
                <Input
                  value={twilioData.phone_number}
                  onChange={(e) => setTwilioData({ ...twilioData, phone_number: e.target.value })}
                  placeholder="+1234567890"
                  className="mt-1 font-mono text-sm"
                />
              </div>
            </div>

            {/* Where to find */}
            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Where to find these:</p>
              <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                <li>Go to <a href="https://console.twilio.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">console.twilio.com</a></li>
                <li>Account SID and Auth Token are on the dashboard</li>
              </ol>
            </div>

            {/* Verify button or success state */}
            {twilioVerified ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 p-4 bg-emerald-50 text-emerald-700 rounded-xl">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-medium">Twilio connected!</span>
                </div>
                {twilioBalance !== null && (
                  <div className={`flex items-center gap-2 p-3 rounded-lg ${twilioBalance < 10 ? 'bg-amber-50 text-amber-700' : 'bg-gray-50 text-gray-600'}`}>
                    {twilioBalance < 10 ? <AlertTriangle className="w-4 h-4" /> : <DollarSign className="w-4 h-4" />}
                    <span className="text-sm">
                      Twilio Balance: <strong>${twilioBalance?.toFixed(2)}</strong>
                      {twilioBalance < 10 && <span className="ml-2">(Consider adding funds)</span>}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <Button
                onClick={verifyTwilio}
                disabled={loading || !twilioData.account_sid || !twilioData.auth_token}
                className="w-full"
              >
                {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                Verify Connection
              </Button>
            )}
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Mic className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Connect ElevenLabs</h2>
              <p className="text-gray-600 mt-2">ElevenLabs powers your AI's natural voice.</p>
            </div>

            {/* Plan recommendation */}
            <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
              <p className="text-sm font-medium text-purple-800 mb-2">Which plan do you need?</p>
              <div className="space-y-2 text-sm text-purple-700">
                <div className="flex justify-between">
                  <span>Starter ($5/mo)</span>
                  <span>~250 mins</span>
                </div>
                <div className="flex justify-between font-semibold bg-purple-100 -mx-2 px-2 py-1 rounded">
                  <span>Creator ($22/mo) ⭐</span>
                  <span>~800 mins</span>
                </div>
                <div className="flex justify-between">
                  <span>Pro ($99/mo)</span>
                  <span>~4,000 mins</span>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-3 text-purple-700 border-purple-300 hover:bg-purple-100"
                onClick={() => window.open("https://elevenlabs.io", "_blank")}
              >
                Get ElevenLabs Account <ExternalLink className="w-3 h-3 ml-2" />
              </Button>
            </div>

            {/* API Key input */}
            <div>
              <Label>ElevenLabs API Key</Label>
              <div className="relative mt-1">
                <Input
                  type={showTokens.elevenlabs ? "text" : "password"}
                  value={elevenLabsData.api_key}
                  onChange={(e) => setElevenLabsData({ ...elevenLabsData, api_key: e.target.value })}
                  placeholder="sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                  className="pr-10 font-mono text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowTokens({ ...showTokens, elevenlabs: !showTokens.elevenlabs })}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showTokens.elevenlabs ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Where to find */}
            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Where to find your API key:</p>
              <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                <li>Go to <a href="https://elevenlabs.io" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">elevenlabs.io</a></li>
                <li>Click profile → "Profile + API key"</li>
              </ol>
            </div>

            {/* Verify button or success state */}
            {elevenLabsVerified ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 p-4 bg-emerald-50 text-emerald-700 rounded-xl">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-medium">ElevenLabs connected!</span>
                </div>
                {elevenLabsCredits !== null && (
                  <div className={`flex items-center gap-2 p-3 rounded-lg ${elevenLabsCredits.remaining_percent < 20 ? 'bg-amber-50 text-amber-700' : 'bg-gray-50 text-gray-600'}`}>
                    {elevenLabsCredits.remaining_percent < 20 ? <AlertTriangle className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                    <span className="text-sm">
                      Credits: <strong>{elevenLabsCredits.remaining_percent}%</strong> remaining
                      {elevenLabsCredits.remaining_percent < 20 && <span className="ml-2">(Running low!)</span>}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <Button
                onClick={verifyElevenLabs}
                disabled={loading || !elevenLabsData.api_key}
                className="w-full"
              >
                {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                Verify Connection
              </Button>
            )}
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">You're All Set!</h2>
              <p className="text-gray-600 mt-2">Everything is connected. Let's create your AI agent.</p>
            </div>

            {/* Summary */}
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-4 bg-emerald-50 rounded-xl">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                <div className="flex-1">
                  <p className="font-medium text-emerald-800">Twilio Connected</p>
                  {twilioBalance !== null && (
                    <p className="text-sm text-emerald-600">Balance: ${twilioBalance?.toFixed(2)}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 bg-emerald-50 rounded-xl">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                <div className="flex-1">
                  <p className="font-medium text-emerald-800">ElevenLabs Connected</p>
                  {elevenLabsCredits !== null && (
                    <p className="text-sm text-emerald-600">Credits: {elevenLabsCredits.remaining_percent}% remaining</p>
                  )}
                </div>
              </div>
            </div>

            {/* Low balance warnings */}
            {((twilioBalance !== null && twilioBalance < 10) || (elevenLabsCredits !== null && elevenLabsCredits.remaining_percent < 20)) && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                <div className="flex items-start gap-2">
                  <Bell className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-amber-800">Credit Alert Setup</p>
                    <p className="text-sm text-amber-700 mt-1">
                      We'll notify you when your Twilio or ElevenLabs credits run low so you're never caught off guard.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Cost estimate */}
            <div className="bg-gray-50 rounded-xl p-5">
              <h3 className="font-semibold text-gray-800 mb-3">Your Estimated Monthly Cost</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">DialGenix Platform</span>
                  <span className="font-medium">$99/mo</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Twilio (~500 mins)</span>
                  <span className="font-medium">~$10/mo</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">ElevenLabs (Creator)</span>
                  <span className="font-medium">$22/mo</span>
                </div>
                <div className="border-t border-gray-200 pt-2 mt-2 flex justify-between">
                  <span className="font-semibold text-gray-800">Total</span>
                  <span className="font-bold text-emerald-600">~$131/mo</span>
                </div>
              </div>
              <p className="text-xs text-gray-400 mt-3">You only pay for what you use. No hidden fees.</p>
            </div>

            <Button onClick={saveSettings} disabled={loading} className="w-full" size="lg">
              {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Bot className="w-4 h-4 mr-2" />}
              Create Your First AI Agent
            </Button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white py-12 px-4" data-testid="setup-wizard">
      <div className="max-w-lg mx-auto">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Step {step} of {totalSteps}</span>
            <span className="text-sm text-gray-400">{Math.round((step / totalSteps) * 100)}%</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 transition-all duration-300"
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Card */}
        <Card className="shadow-xl border-0">
          <CardContent className="p-8">
            {renderStep()}

            {/* Navigation */}
            <div className="flex justify-between mt-8 pt-6 border-t border-gray-100">
              {step > 1 ? (
                <Button variant="ghost" onClick={() => setStep(step - 1)}>
                  <ArrowLeft className="w-4 h-4 mr-2" /> Back
                </Button>
              ) : (
                <div />
              )}
              
              {step < totalSteps && (
                <Button 
                  onClick={() => setStep(step + 1)}
                  disabled={
                    (step === 2 && !twilioVerified) ||
                    (step === 3 && !elevenLabsVerified)
                  }
                >
                  Continue <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Skip option */}
        {step > 1 && step < 4 && (
          <p className="text-center mt-4">
            <button 
              onClick={() => setStep(step + 1)} 
              className="text-sm text-gray-400 hover:text-gray-600"
            >
              Skip for now
            </button>
          </p>
        )}
      </div>
    </div>
  );
};

export default SetupWizard;
