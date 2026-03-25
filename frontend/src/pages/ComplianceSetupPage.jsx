import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { 
  Shield, CheckCircle, Circle, AlertTriangle, ExternalLink, 
  Phone, Clock, Users, FileText, ChevronRight, Building2, User,
  HelpCircle, Lock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Separator } from "@/components/ui/separator";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ComplianceSetupPage = () => {
  const [setupGuide, setSetupGuide] = useState(null);
  const [acknowledgmentStatus, setAcknowledgmentStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  
  // Form state
  const [callingMode, setCallingMode] = useState("b2b");
  const [ftcSan, setFtcSan] = useState("");
  const [acknowledgments, setAcknowledgments] = useState({
    dnc_responsibility: false,
    tcpa_rules: false,
    calling_hours: false,
    litigator_risk: false
  });

  const fetchData = useCallback(async () => {
    try {
      const [guideRes, ackRes] = await Promise.all([
        axios.get(`${API}/compliance/setup-guide`),
        axios.get(`${API}/compliance/acknowledgment`)
      ]);
      setSetupGuide(guideRes.data);
      setAcknowledgmentStatus(ackRes.data);
      setCallingMode(guideRes.data.calling_mode || "b2b");
      
      // If already acknowledged, pre-fill checkboxes
      if (ackRes.data.acknowledged) {
        setAcknowledgments({
          dnc_responsibility: true,
          tcpa_rules: true,
          calling_hours: true,
          litigator_risk: true
        });
        setFtcSan(ackRes.data.ftc_san || "");
      }
    } catch (error) {
      console.error("Failed to fetch compliance data:", error);
      toast.error("Failed to load compliance setup");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSubmit = async () => {
    // Validate all acknowledgments
    if (!Object.values(acknowledgments).every(v => v)) {
      toast.error("Please acknowledge all compliance requirements");
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API}/compliance/acknowledge`, {
        calling_mode: callingMode,
        ftc_san: callingMode === "b2c" ? ftcSan : null,
        acknowledge_dnc_responsibility: acknowledgments.dnc_responsibility,
        acknowledge_tcpa_rules: acknowledgments.tcpa_rules,
        acknowledge_calling_hours: acknowledgments.calling_hours,
        acknowledge_litigator_risk: acknowledgments.litigator_risk
      });
      
      toast.success("Compliance acknowledgment recorded. You can now make calls!");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit acknowledgment");
    } finally {
      setSubmitting(false);
    }
  };

  const allAcknowledged = Object.values(acknowledgments).every(v => v);

  if (loading) {
    return (
      <div className="p-6 md:p-8 space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-40" />
        <Skeleton className="h-60" />
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-4xl mx-auto" data-testid="compliance-setup-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
          <Shield className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Compliance Setup
          </h1>
          <p className="text-gray-500">Complete these steps before making outbound calls</p>
        </div>
      </div>

      {/* Progress */}
      {setupGuide && (
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-blue-900">Setup Progress</span>
              <Badge className={setupGuide.completion_percentage === 100 ? "bg-green-100 text-green-800" : "bg-blue-100 text-blue-800"}>
                {setupGuide.completion_percentage}% Complete
              </Badge>
            </div>
            <Progress value={setupGuide.completion_percentage} className="h-2" />
          </CardContent>
        </Card>
      )}

      {/* Already Acknowledged Banner */}
      {acknowledgmentStatus?.acknowledged && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <AlertTitle className="text-green-800">Compliance Acknowledged</AlertTitle>
          <AlertDescription className="text-green-700">
            You acknowledged compliance on {new Date(acknowledgmentStatus.acknowledged_at).toLocaleDateString()}.
            You're ready to make calls in <strong>{acknowledgmentStatus.calling_mode.toUpperCase()}</strong> mode.
          </AlertDescription>
        </Alert>
      )}

      {/* Calling Mode Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone className="w-5 h-5" />
            Step 1: Select Your Calling Mode
          </CardTitle>
          <CardDescription>
            Choose based on who you're calling
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RadioGroup 
            value={callingMode} 
            onValueChange={setCallingMode}
            disabled={acknowledgmentStatus?.acknowledged}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* B2B Option */}
              <label 
                className={`relative flex flex-col p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  callingMode === "b2b" 
                    ? "border-blue-500 bg-blue-50" 
                    : "border-gray-200 hover:border-gray-300"
                } ${acknowledgmentStatus?.acknowledged ? "opacity-75 cursor-not-allowed" : ""}`}
              >
                <RadioGroupItem value="b2b" className="absolute top-4 right-4" />
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-semibold">B2B Calling</p>
                    <Badge variant="outline" className="text-xs">Recommended</Badge>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  Call business phone numbers (landlines). Exempt from National DNC Registry.
                </p>
                <div className="space-y-1 text-xs text-gray-500">
                  <p className="flex items-center gap-1"><CheckCircle className="w-3 h-3 text-green-500" /> No FTC registration required</p>
                  <p className="flex items-center gap-1"><CheckCircle className="w-3 h-3 text-green-500" /> No DNC data purchase needed</p>
                  <p className="flex items-center gap-1"><CheckCircle className="w-3 h-3 text-green-500" /> $0 compliance cost</p>
                </div>
              </label>

              {/* B2C Option */}
              <label 
                className={`relative flex flex-col p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  callingMode === "b2c" 
                    ? "border-orange-500 bg-orange-50" 
                    : "border-gray-200 hover:border-gray-300"
                } ${acknowledgmentStatus?.acknowledged ? "opacity-75 cursor-not-allowed" : ""}`}
              >
                <RadioGroupItem value="b2c" className="absolute top-4 right-4" />
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                    <User className="w-5 h-5 text-orange-600" />
                  </div>
                  <div>
                    <p className="font-semibold">B2C Calling</p>
                    <Badge variant="outline" className="text-xs text-orange-600 border-orange-300">Advanced</Badge>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  Call consumers/cell phones. Full TCPA/DNC compliance required.
                </p>
                <div className="space-y-1 text-xs text-gray-500">
                  <p className="flex items-center gap-1"><AlertTriangle className="w-3 h-3 text-orange-500" /> FTC registration required</p>
                  <p className="flex items-center gap-1"><AlertTriangle className="w-3 h-3 text-orange-500" /> Must purchase DNC data ($82-$22k/year)</p>
                  <p className="flex items-center gap-1"><AlertTriangle className="w-3 h-3 text-orange-500" /> 31-day refresh required</p>
                </div>
              </label>
            </div>
          </RadioGroup>

          {/* B2C Additional Fields */}
          {callingMode === "b2c" && (
            <div className="mt-6 p-4 bg-orange-50 rounded-lg border border-orange-200">
              <h4 className="font-medium text-orange-900 mb-3">B2C Requirements</h4>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="ftc-san">FTC Subscription Account Number (SAN)</Label>
                  <Input
                    id="ftc-san"
                    placeholder="Enter your SAN from telemarketing.donotcall.gov"
                    value={ftcSan}
                    onChange={(e) => setFtcSan(e.target.value)}
                    disabled={acknowledgmentStatus?.acknowledged}
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Get your SAN at{" "}
                    <a href="https://telemarketing.donotcall.gov" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      telemarketing.donotcall.gov
                    </a>
                  </p>
                </div>
                <Alert className="bg-orange-100 border-orange-300">
                  <AlertTriangle className="h-4 w-4 text-orange-600" />
                  <AlertDescription className="text-orange-800 text-sm">
                    You must also upload FTC DNC data in the <a href="/app/dnc" className="font-medium underline">DNC Management</a> page.
                  </AlertDescription>
                </Alert>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Compliance Acknowledgments */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Step 2: Acknowledge Compliance Responsibility
          </CardTitle>
          <CardDescription>
            By checking these boxes, you confirm you understand and accept responsibility
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Acknowledgment 1: DNC Responsibility */}
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
            <Checkbox
              id="ack-dnc"
              checked={acknowledgments.dnc_responsibility}
              onCheckedChange={(checked) => 
                setAcknowledgments(prev => ({ ...prev, dnc_responsibility: checked }))
              }
              disabled={acknowledgmentStatus?.acknowledged}
            />
            <div>
              <Label htmlFor="ack-dnc" className="font-medium cursor-pointer">
                I am responsible for Do Not Call compliance
              </Label>
              <p className="text-sm text-gray-500 mt-1">
                I understand that ColdCall.ai provides compliance tools, but I am solely responsible for 
                maintaining my own DNC lists and scrubbing call lists against the National DNC Registry 
                if required for my calling activities.
              </p>
            </div>
          </div>

          {/* Acknowledgment 2: TCPA Rules */}
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
            <Checkbox
              id="ack-tcpa"
              checked={acknowledgments.tcpa_rules}
              onCheckedChange={(checked) => 
                setAcknowledgments(prev => ({ ...prev, tcpa_rules: checked }))
              }
              disabled={acknowledgmentStatus?.acknowledged}
            />
            <div>
              <Label htmlFor="ack-tcpa" className="font-medium cursor-pointer">
                I understand TCPA rules and potential penalties
              </Label>
              <p className="text-sm text-gray-500 mt-1">
                I understand that TCPA violations can result in penalties of $500-$1,500 per call, 
                and that I must obtain proper consent before calling cell phones with automated systems.
              </p>
            </div>
          </div>

          {/* Acknowledgment 3: Calling Hours */}
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
            <Checkbox
              id="ack-hours"
              checked={acknowledgments.calling_hours}
              onCheckedChange={(checked) => 
                setAcknowledgments(prev => ({ ...prev, calling_hours: checked }))
              }
              disabled={acknowledgmentStatus?.acknowledged}
            />
            <div>
              <Label htmlFor="ack-hours" className="font-medium cursor-pointer">
                I will only call during legal hours (8am-9pm local time)
              </Label>
              <p className="text-sm text-gray-500 mt-1">
                I understand that ColdCall.ai enforces calling hour restrictions, and I will not attempt 
                to circumvent these protections. Some states have stricter hours (e.g., Texas 9am-9pm).
              </p>
            </div>
          </div>

          {/* Acknowledgment 4: Litigator Risk */}
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
            <Checkbox
              id="ack-litigator"
              checked={acknowledgments.litigator_risk}
              onCheckedChange={(checked) => 
                setAcknowledgments(prev => ({ ...prev, litigator_risk: checked }))
              }
              disabled={acknowledgmentStatus?.acknowledged}
            />
            <div>
              <Label htmlFor="ack-litigator" className="font-medium cursor-pointer">
                I understand TCPA litigation risks
              </Label>
              <p className="text-sm text-gray-500 mt-1">
                I understand that professional TCPA plaintiffs actively seek violations to file lawsuits, 
                and I will use the litigator blocking feature to protect my business.
              </p>
            </div>
          </div>

          <Separator />

          {/* Submit Button */}
          {!acknowledgmentStatus?.acknowledged && (
            <Button
              className="w-full bg-blue-600 hover:bg-blue-700"
              size="lg"
              onClick={handleSubmit}
              disabled={!allAcknowledged || submitting}
              data-testid="submit-compliance"
            >
              {submitting ? (
                "Submitting..."
              ) : (
                <>
                  <Lock className="w-4 h-4 mr-2" />
                  I Agree - Enable Calling
                </>
              )}
            </Button>
          )}

          {acknowledgmentStatus?.acknowledged && (
            <div className="text-center text-sm text-gray-500">
              <CheckCircle className="w-5 h-5 inline mr-2 text-green-500" />
              Acknowledged on {new Date(acknowledgmentStatus.acknowledged_at).toLocaleDateString()}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Setup Checklist */}
      {setupGuide?.checklist && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5" />
              Compliance Checklist
            </CardTitle>
            <CardDescription>
              {callingMode === "b2b" ? "B2B Calling Requirements" : "B2C Calling Requirements"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {setupGuide.checklist.map((item) => (
                <div 
                  key={item.id}
                  className={`flex items-center gap-3 p-3 rounded-lg ${
                    item.completed ? "bg-green-50" : "bg-gray-50"
                  }`}
                >
                  {item.completed ? (
                    <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />
                  ) : (
                    <Circle className="w-5 h-5 text-gray-300 shrink-0" />
                  )}
                  <div className="flex-1">
                    <p className={`font-medium ${item.completed ? "text-green-800" : "text-gray-700"}`}>
                      {item.title}
                      {item.required && <span className="text-red-500 ml-1">*</span>}
                    </p>
                    <p className="text-sm text-gray-500">{item.description}</p>
                  </div>
                  {item.action === "upload_dnc" && !item.completed && (
                    <Button variant="outline" size="sm" asChild>
                      <a href="/app/dnc">Upload</a>
                    </Button>
                  )}
                  {item.action === "upload_litigators" && !item.completed && (
                    <Button variant="outline" size="sm" asChild>
                      <a href="/app/dnc">Add</a>
                    </Button>
                  )}
                  {item.action === "ftc_register" && !item.completed && (
                    <Button variant="outline" size="sm" asChild>
                      <a href="https://telemarketing.donotcall.gov" target="_blank" rel="noopener noreferrer">
                        Register <ExternalLink className="w-3 h-3 ml-1" />
                      </a>
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Resources */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5" />
            Compliance Resources
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="b2b">
              <AccordionTrigger>What is B2B vs B2C calling?</AccordionTrigger>
              <AccordionContent className="text-gray-600">
                <p className="mb-2"><strong>B2B (Business-to-Business):</strong> Calls made to business phone numbers with the intent to sell to that business. These calls are exempt from National DNC Registry requirements.</p>
                <p><strong>B2C (Business-to-Consumer):</strong> Calls made to individuals/consumers. These require full TCPA compliance including DNC scrubbing, consent for cell phones, and FTC registration.</p>
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="dnc">
              <AccordionTrigger>Do I need to pay for DNC data?</AccordionTrigger>
              <AccordionContent className="text-gray-600">
                <p><strong>For B2B:</strong> No. Business-to-business calls to business landlines are exempt from the National DNC Registry.</p>
                <p className="mt-2"><strong>For B2C:</strong> Yes. You must register with the FTC at telemarketing.donotcall.gov and pay for area code access ($82/area code, max ~$22,000 for nationwide). First 5 area codes are free.</p>
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="penalties">
              <AccordionTrigger>What are the penalties for violations?</AccordionTrigger>
              <AccordionContent className="text-gray-600">
                <ul className="list-disc pl-4 space-y-1">
                  <li><strong>TCPA:</strong> $500-$1,500 per call (treble damages for willful violations)</li>
                  <li><strong>FTC/TSR:</strong> Up to $50,120 per violation</li>
                  <li><strong>State laws:</strong> Vary by state, can add additional penalties</li>
                </ul>
                <p className="mt-2">Professional TCPA plaintiffs actively seek violations - use the litigator blocking feature!</p>
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="ai-disclosure">
              <AccordionTrigger>Is AI disclosure required?</AccordionTrigger>
              <AccordionContent className="text-gray-600">
                <p>Yes. FTC guidelines and many state laws require disclosure when using AI or automated voices. ColdCall.ai automatically includes AI disclosure at the start of every call.</p>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <Separator className="my-4" />

          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" asChild>
              <a href="https://telemarketing.donotcall.gov" target="_blank" rel="noopener noreferrer">
                FTC DNC Registry <ExternalLink className="w-3 h-3 ml-1" />
              </a>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a href="https://www.ftc.gov/business-guidance/resources/complying-telemarketing-sales-rule" target="_blank" rel="noopener noreferrer">
                FTC TSR Guide <ExternalLink className="w-3 h-3 ml-1" />
              </a>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a href="/app/dnc">
                DNC Management <ChevronRight className="w-3 h-3 ml-1" />
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ComplianceSetupPage;
