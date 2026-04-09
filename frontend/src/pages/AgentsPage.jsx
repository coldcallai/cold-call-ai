import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Slider } from "@/components/ui/slider";
import { VoiceCloneModal, VoiceSettingsModal } from "@/components/VoiceCloning";
import TrustLine from "@/components/TrustLine";
import {
  Users, Plus, Trash2, Edit3, Mic, Volume2, RefreshCw, Phone, Play, Pause, Mail, Zap, Settings, Calendar, Brain
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Supported languages for ElevenLabs multilingual_v2
const SUPPORTED_LANGUAGES = [
  { code: "en", name: "English", flag: "🇺🇸" },
  { code: "es", name: "Spanish", flag: "🇪🇸" },
  { code: "fr", name: "French", flag: "🇫🇷" },
  { code: "de", name: "German", flag: "🇩🇪" },
  { code: "it", name: "Italian", flag: "🇮🇹" },
  { code: "pt", name: "Portuguese", flag: "🇵🇹" },
  { code: "pl", name: "Polish", flag: "🇵🇱" },
  { code: "nl", name: "Dutch", flag: "🇳🇱" },
  { code: "sv", name: "Swedish", flag: "🇸🇪" },
  { code: "da", name: "Danish", flag: "🇩🇰" },
  { code: "fi", name: "Finnish", flag: "🇫🇮" },
  { code: "no", name: "Norwegian", flag: "🇳🇴" },
  { code: "ru", name: "Russian", flag: "🇷🇺" },
  { code: "uk", name: "Ukrainian", flag: "🇺🇦" },
  { code: "tr", name: "Turkish", flag: "🇹🇷" },
  { code: "ar", name: "Arabic", flag: "🇸🇦" },
  { code: "he", name: "Hebrew", flag: "🇮🇱" },
  { code: "hi", name: "Hindi", flag: "🇮🇳" },
  { code: "zh", name: "Chinese (Mandarin)", flag: "🇨🇳" },
  { code: "ja", name: "Japanese", flag: "🇯🇵" },
  { code: "ko", name: "Korean", flag: "🇰🇷" }
];

// Use case templates
const USE_CASE_TEMPLATES = {
  sales_cold_calling: {
    label: "Sales / Cold Calling",
    description: "Qualify leads and book meetings",
    tips: "Best for: General B2B sales. Customize the opening with your value proposition.",
    prompt: "You are a sales representative for {company}. Your name is {agent_name}. Keep responses SHORT (1-2 sentences max) - this is a phone call."
  },
  credit_card_processing: {
    label: "Credit Card Processing",
    description: "Merchant services & payment processing sales",
    tips: "Best for: Payment processors, merchant services.",
    prompt: "You are a merchant services consultant for {company}. Your name is {agent_name}. Keep responses SHORT (1-2 sentences) - this is a phone call."
  },
  appointment_setter: {
    label: "Appointment Setter",
    description: "Schedule appointments and manage bookings",
    tips: "Best for: Service businesses, consultants.",
    prompt: "You are a scheduling assistant for {company}. Your name is {agent_name}. Keep responses SHORT (1-2 sentences) - this is a phone call."
  },
  receptionist: {
    label: "Receptionist",
    description: "Answer calls and route to departments",
    tips: "Best for: Offices, clinics.",
    prompt: "You are the front desk receptionist for {company}. Your name is {agent_name}. Keep responses SHORT (1-2 sentences) - this is a phone call."
  },
  customer_service: {
    label: "Customer Service",
    description: "Handle support inquiries and issues",
    tips: "Best for: Support teams.",
    prompt: "You are a customer support agent for {company}. Your name is {agent_name}. Keep responses SHORT (1-2 sentences) - this is a phone call."
  }
};

const Agents = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showVoiceClone, setShowVoiceClone] = useState(false);
  const [showVoiceSettings, setShowVoiceSettings] = useState(null); // agent for voice settings
  const [previewingVoice, setPreviewingVoice] = useState(null); // agent id being previewed
  const [playingAudio, setPlayingAudio] = useState(null); // audio element reference
  const [editingAgent, setEditingAgent] = useState(null); // agent being edited

  const [newAgent, setNewAgent] = useState({
    name: "",
    company_name: "",
    email: "",
    phone: "",
    calendly_link: "",
    max_daily_calls: 50,
    use_case: "sales_cold_calling",
    system_prompt: USE_CASE_TEMPLATES.sales_cold_calling.prompt,
    language: "en",
    transfer_enabled: false,
    transfer_phone_number: ""
  });

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API}/agents`);
      setAgents(response.data);
    } catch (error) {
      toast.error("Failed to load agents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (playingAudio) {
        playingAudio.pause();
        playingAudio.src = "";
      }
    };
  }, [playingAudio]);

  const previewAgentVoice = async (agent) => {
    // If already previewing this agent, stop it
    if (previewingVoice === agent.id && playingAudio) {
      playingAudio.pause();
      setPlayingAudio(null);
      setPreviewingVoice(null);
      return;
    }

    // Stop any currently playing audio
    if (playingAudio) {
      playingAudio.pause();
    }

    setPreviewingVoice(agent.id);
    const voiceId = agent.voice_type === "cloned" ? agent.cloned_voice_id : (agent.preset_voice_id || "21m00Tcm4TlvDq8ikWAM");
    const previewText = `Hi, this is ${agent.name}. I'm your AI sales agent, ready to help you connect with qualified leads and close more deals!`;

    const formData = new FormData();
    formData.append("text", previewText);
    formData.append("voice_id", voiceId);

    try {
      const response = await axios.post(`${API}/voices/preview`, formData);
      const audio = new Audio(response.data.audio);
      
      audio.onended = () => {
        setPlayingAudio(null);
        setPreviewingVoice(null);
      };
      
      audio.onerror = () => {
        toast.error("Failed to play audio");
        setPlayingAudio(null);
        setPreviewingVoice(null);
      };

      setPlayingAudio(audio);
      await audio.play();
      toast.success(`Playing ${agent.name}'s voice...`);
    } catch (error) {
      console.error("Preview failed:", error);
      toast.error("Failed to generate voice preview");
      setPreviewingVoice(null);
    }
  };

  const createAgent = async () => {
    if (!newAgent.name || !newAgent.email || !newAgent.calendly_link) {
      toast.error("Please fill in all required fields");
      return;
    }

    try {
      await axios.post(`${API}/agents`, newAgent);
      toast.success("Agent created!");
      setShowCreate(false);
      setNewAgent({ 
        name: "", 
        email: "", 
        phone: "", 
        calendly_link: "", 
        max_daily_calls: 50,
        use_case: "sales_cold_calling",
        system_prompt: USE_CASE_TEMPLATES.sales_cold_calling.prompt
      });
      fetchAgents();
    } catch (error) {
      toast.error("Failed to create agent");
    }
  };

  const toggleAgent = async (agent) => {
    try {
      await axios.put(`${API}/agents/${agent.id}`, { is_active: !agent.is_active });
      toast.success(`Agent ${agent.is_active ? 'deactivated' : 'activated'}`);
      fetchAgents();
    } catch (error) {
      toast.error("Failed to update agent");
    }
  };

  const updateAgent = async () => {
    if (!editingAgent) return;
    try {
      await axios.put(`${API}/agents/${editingAgent.id}`, editingAgent);
      toast.success("Agent updated successfully");
      setEditingAgent(null);
      fetchAgents();
    } catch (error) {
      toast.error("Failed to update agent");
    }
  };

  const openEditDialog = (agent) => {
    setEditingAgent({
      ...agent,
      transfer_enabled: agent.transfer_enabled || false,
      transfer_phone_number: agent.transfer_phone_number || ""
    });
  };

  const deleteAgent = async (id) => {
    try {
      await axios.delete(`${API}/agents/${id}`);
      toast.success("Agent deleted");
      fetchAgents();
    } catch (error) {
      toast.error("Failed to delete agent");
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="agents-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Agents
          </h1>
          <p className="text-gray-500 mt-1">Manage sales agents and their Calendly links</p>
          <TrustLine className="mt-2" />
        </div>
        <div className="flex gap-2">
          <Button 
            data-testid="clone-voice-btn"
            onClick={() => setShowVoiceClone(true)}
            variant="outline"
            className="border-purple-300 text-purple-700 hover:bg-purple-50"
          >
            <Mic className="w-4 h-4 mr-2" />
            Clone Voice
          </Button>
          <Button 
            data-testid="create-agent-btn"
            onClick={() => setShowCreate(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Agent
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1,2,3].map(i => <Skeleton key={i} className="h-48" />)}
        </div>
      ) : agents.length === 0 ? (
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardContent className="p-12 text-center">
            <Users className="w-16 h-16 text-gray-300 mx-auto" />
            <p className="text-gray-500 mt-4">No agents yet. Add agents to receive qualified leads.</p>
            <Button 
              onClick={() => setShowCreate(true)}
              className="mt-4 bg-blue-600 hover:bg-blue-700 text-white"
            >
              Add Agent
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map(agent => (
            <Card key={agent.id} className={`bg-white border shadow-sm hover:shadow-md transition-shadow ${agent.is_active ? 'border-gray-200' : 'border-gray-300 opacity-60'}`} data-testid={`agent-card-${agent.id}`}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-semibold ${agent.is_active ? 'bg-blue-600' : 'bg-gray-400'}`}>
                      {agent.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                      <Badge variant={agent.is_active ? "default" : "secondary"}>
                        {agent.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      data-testid={`edit-agent-${agent.id}`}
                      onClick={() => openEditDialog(agent)}
                      className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                    >
                      <Edit3 className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      data-testid={`delete-agent-${agent.id}`}
                      onClick={() => deleteAgent(agent.id)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                
                <div className="space-y-2 text-sm mb-4">
                  <div className="flex items-center gap-2 text-gray-600">
                    <Mail className="w-4 h-4" />
                    {agent.email}
                  </div>
                  {agent.phone && (
                    <div className="flex items-center gap-2 text-gray-600">
                      <Phone className="w-4 h-4" />
                      {agent.phone}
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-blue-600">
                    <Calendar className="w-4 h-4" />
                    <a href={agent.calendly_link} target="_blank" rel="noopener noreferrer" className="hover:underline truncate">
                      Calendly Link
                    </a>
                  </div>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-4">
                  <span className="text-sm text-gray-600">Assigned Leads</span>
                  <span className="text-lg font-semibold text-gray-900">{agent.assigned_leads}</span>
                </div>

                {/* Voice Settings Indicator */}
                <div className="flex items-center gap-2 p-3 bg-purple-50 rounded-lg mb-4">
                  <Volume2 className="w-4 h-4 text-purple-600" />
                  <div className="flex-1">
                    <span className="text-sm text-gray-700">
                      {agent.voice_type === "cloned" ? agent.cloned_voice_name || "Cloned Voice" : "Preset Voice"}
                    </span>
                    {agent.voice_type === "cloned" && (
                      <Badge className="ml-2 bg-purple-100 text-purple-700 text-xs">Custom</Badge>
                    )}
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => previewAgentVoice(agent)}
                    disabled={previewingVoice && previewingVoice !== agent.id}
                    className={`${previewingVoice === agent.id ? 'text-green-600 hover:text-green-700 hover:bg-green-100' : 'text-purple-600 hover:text-purple-700 hover:bg-purple-100'}`}
                    data-testid={`preview-voice-${agent.id}`}
                    title={previewingVoice === agent.id ? "Stop preview" : "Preview voice"}
                  >
                    {previewingVoice === agent.id ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowVoiceSettings(agent)}
                    className="text-purple-600 hover:text-purple-700 hover:bg-purple-100"
                    data-testid={`voice-settings-${agent.id}`}
                  >
                    <Settings className="w-4 h-4" />
                  </Button>
                </div>

                <div className="flex gap-2">
                  <Button
                    className="flex-1"
                    variant="outline"
                    data-testid={`toggle-agent-${agent.id}`}
                    onClick={() => toggleAgent(agent)}
                  >
                    {agent.is_active ? "Deactivate" : "Activate"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Agent Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Create AI Agent
            </DialogTitle>
            <DialogDescription>
              Configure your virtual AI caller — choose a voice, language, and script
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Use Case Selector */}
            <div>
              <Label htmlFor="use-case">Use Case *</Label>
              <select
                id="use-case"
                data-testid="agent-use-case-select"
                value={newAgent.use_case}
                onChange={(e) => {
                  const useCase = e.target.value;
                  const template = USE_CASE_TEMPLATES[useCase];
                  setNewAgent({
                    ...newAgent, 
                    use_case: useCase,
                    system_prompt: template.prompt
                  });
                }}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {Object.entries(USE_CASE_TEMPLATES).map(([key, template]) => (
                  <option key={key} value={key}>{template.label}</option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {USE_CASE_TEMPLATES[newAgent.use_case]?.description}
              </p>
              {USE_CASE_TEMPLATES[newAgent.use_case]?.tips && (
                <p className="text-xs text-blue-600 mt-1 bg-blue-50 px-2 py-1 rounded">
                  💡 {USE_CASE_TEMPLATES[newAgent.use_case]?.tips}
                </p>
              )}
            </div>
            
            <div>
              <Label htmlFor="agent-name">AI Agent Name *</Label>
              <Input
                id="agent-name"
                data-testid="agent-name-input"
                value={newAgent.name}
                onChange={(e) => setNewAgent({...newAgent, name: e.target.value})}
                placeholder="Sarah (Sales Agent)"
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">What your AI will call itself on calls</p>
            </div>

            <div>
              <Label htmlFor="company-name">Company Name *</Label>
              <Input
                id="company-name"
                data-testid="agent-company-input"
                value={newAgent.company_name}
                onChange={(e) => setNewAgent({...newAgent, company_name: e.target.value})}
                placeholder="DialGenix"
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">Company the AI represents (replaces {'{company}'} in script)</p>
            </div>
            
            <div>
              <Label htmlFor="agent-email">Notification Email *</Label>
              <Input
                id="agent-email"
                data-testid="agent-email-input"
                type="email"
                value={newAgent.email}
                onChange={(e) => setNewAgent({...newAgent, email: e.target.value})}
                placeholder="alerts@yourcompany.com"
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">Receive alerts when this agent qualifies leads</p>
            </div>
            
            <div>
              <Label htmlFor="agent-phone">Outbound Phone Number</Label>
              <Input
                id="agent-phone"
                data-testid="agent-phone-input"
                value={newAgent.phone}
                onChange={(e) => setNewAgent({...newAgent, phone: e.target.value})}
                placeholder="+14155551234 (your Twilio number)"
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">Twilio number the AI calls FROM (leave blank to use default)</p>
            </div>
            
            <div>
              <Label htmlFor="calendly-link">Meeting Booking Link *</Label>
              <Input
                id="calendly-link"
                data-testid="agent-calendly-input"
                value={newAgent.calendly_link}
                onChange={(e) => setNewAgent({...newAgent, calendly_link: e.target.value})}
                placeholder="https://calendly.com/your-name/30min"
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">Where qualified leads can book meetings</p>
            </div>

            {/* Language Selection */}
            <div>
              <Label htmlFor="language" className="flex items-center gap-2">
                Language
                <span className="text-xs text-gray-400 font-normal">(AI will speak in this language)</span>
              </Label>
              <select
                id="language"
                value={newAgent.language}
                onChange={(e) => setNewAgent({...newAgent, language: e.target.value})}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.flag} {lang.name}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">Supports 50+ languages via ElevenLabs multilingual model</p>
            </div>
            
            {/* System Prompt (Advanced) */}
            <div>
              <Label htmlFor="system-prompt" className="flex items-center gap-2">
                AI Script 
                <span className="text-xs text-gray-400 font-normal">(customize if needed)</span>
              </Label>
              
              {/* Pro Tips Box */}
              <div className="mt-2 mb-3 bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-sm font-medium text-amber-900 mb-2 flex items-center gap-1">
                  <Zap className="w-4 h-4" /> Script Best Practices
                </p>
                <ul className="text-xs text-amber-800 space-y-1">
                  <li>✓ <strong>Always qualify first:</strong> "Am I speaking with the owner or manager?"</li>
                  <li>✓ <strong>Keep it short:</strong> 1-2 sentences per response max</li>
                  <li>✓ <strong>Use {'{contact_name}'}</strong> if Apollo is connected for personalization</li>
                  <li>✓ <strong>Add pauses:</strong> Use "..." for natural breathing room</li>
                </ul>
              </div>

              {/* DISC Personality Detection Tips */}
              <div className="mt-2 mb-3 bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-sm font-medium text-purple-900 mb-3 flex items-center gap-2">
                  <Brain className="w-4 h-4" /> 🧠 DISC Personality Detection Questions
                </p>
                <p className="text-xs text-purple-700 mb-3">Add these questions early in your script to quickly identify buyer personality:</p>
                
                {/* High Signal Question */}
                <div className="bg-white/60 rounded-lg p-3 mb-3 border border-purple-100">
                  <p className="text-xs font-semibold text-purple-800 mb-1">🎯 Highest Signal Question:</p>
                  <p className="text-sm text-gray-700 italic mb-2">
                    "Just so I can tailor this for you—what's most important here: getting straight to results, or understanding all the details first?"
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-red-500 text-white rounded text-xs flex items-center justify-center font-bold">D</span>
                      <span className="text-gray-600">"results", "bottom line"</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-blue-500 text-white rounded text-xs flex items-center justify-center font-bold">C</span>
                      <span className="text-gray-600">"details", "how it works"</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-yellow-500 text-white rounded text-xs flex items-center justify-center font-bold">I</span>
                      <span className="text-gray-600">vague / conversational</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-green-500 text-white rounded text-xs flex items-center justify-center font-bold">S</span>
                      <span className="text-gray-600">"both is fine"</span>
                    </div>
                  </div>
                </div>
                
                {/* Evaluation Question */}
                <div className="bg-white/60 rounded-lg p-3 mb-3 border border-purple-100">
                  <p className="text-xs font-semibold text-purple-800 mb-1">🔍 Evaluation Question:</p>
                  <p className="text-sm text-gray-700 italic mb-2">
                    "When you're evaluating something like this, what matters more—ROI, ease of use, or team fit?"
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-red-500 text-white rounded text-xs flex items-center justify-center font-bold">D</span>
                      <span className="text-gray-600">ROI / performance</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-blue-500 text-white rounded text-xs flex items-center justify-center font-bold">C</span>
                      <span className="text-gray-600">specifics / accuracy</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-yellow-500 text-white rounded text-xs flex items-center justify-center font-bold">I</span>
                      <span className="text-gray-600">team / excitement</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-green-500 text-white rounded text-xs flex items-center justify-center font-bold">S</span>
                      <span className="text-gray-600">ease / stability</span>
                    </div>
                  </div>
                </div>
                
                {/* Mirror Responses */}
                <div className="bg-gradient-to-r from-purple-100 to-pink-100 rounded-lg p-3 border border-purple-200">
                  <p className="text-xs font-semibold text-purple-800 mb-2">🔥 Pro Move: Mirror Immediately After Detection</p>
                  <div className="space-y-1.5 text-xs">
                    <div className="flex items-start gap-2">
                      <span className="w-5 h-5 bg-red-500 text-white rounded text-xs flex items-center justify-center font-bold flex-shrink-0">D</span>
                      <span className="text-gray-700">"Got it—I'll keep this focused on results."</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="w-5 h-5 bg-yellow-500 text-white rounded text-xs flex items-center justify-center font-bold flex-shrink-0">I</span>
                      <span className="text-gray-700">"Love it—this is actually where things get exciting…"</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="w-5 h-5 bg-green-500 text-white rounded text-xs flex items-center justify-center font-bold flex-shrink-0">S</span>
                      <span className="text-gray-700">"No rush—I'll go step by step so it's clear."</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="w-5 h-5 bg-blue-500 text-white rounded text-xs flex items-center justify-center font-bold flex-shrink-0">C</span>
                      <span className="text-gray-700">"Great question—let me walk you through exactly how it works."</span>
                    </div>
                  </div>
                  <p className="text-xs text-purple-600 mt-2 italic">👉 This is where prospects go: "Wait… this feels different"</p>
                </div>
              </div>

              <textarea
                id="system-prompt"
                data-testid="agent-prompt-input"
                value={newAgent.system_prompt}
                onChange={(e) => setNewAgent({...newAgent, system_prompt: e.target.value})}
                placeholder="Enter custom AI instructions..."
                rows={12}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono resize-y min-h-[200px]"
              />
              <p className="text-xs text-gray-400 mt-1">
                Variables: <code className="bg-gray-100 px-1 rounded">{'{agent_name}'}</code> = AI's name, 
                <code className="bg-gray-100 px-1 rounded ml-1">{'{company}'}</code> = company name, 
                <code className="bg-gray-100 px-1 rounded ml-1">{'{contact_name}'}</code> = lead's name (if available)
              </p>
            </div>

            {/* Live Transfer Settings */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <Label className="text-base font-semibold">Live Transfer</Label>
                  <p className="text-xs text-gray-500">Transfer interested prospects to a human team member</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newAgent.transfer_enabled}
                    onChange={(e) => setNewAgent({...newAgent, transfer_enabled: e.target.checked})}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
              
              {newAgent.transfer_enabled && (
                <div className="space-y-3 pl-4 border-l-2 border-blue-200">
                  <div>
                    <Label>Transfer Phone Number *</Label>
                    <Input
                      data-testid="transfer-phone-input"
                      value={newAgent.transfer_phone_number}
                      onChange={(e) => setNewAgent({...newAgent, transfer_phone_number: e.target.value})}
                      placeholder="+1 (555) 123-4567"
                      className="mt-1"
                    />
                    <p className="text-xs text-gray-400 mt-1">
                      When a prospect wants to speak with a human, the AI will ask: "Would you like me to connect you with a team member now?" and transfer to this number.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button 
              data-testid="save-agent-btn"
              onClick={createAgent}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Create AI Agent
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Voice Clone Modal */}
      <VoiceCloneModal
        isOpen={showVoiceClone}
        onClose={() => setShowVoiceClone(false)}
        onVoiceCloned={(voice) => {
          toast.success(`Voice "${voice.name}" cloned successfully!`);
          setShowVoiceClone(false);
        }}
      />

      {/* Voice Settings Modal */}
      {showVoiceSettings && (
        <VoiceSettingsModal
          isOpen={!!showVoiceSettings}
          onClose={() => setShowVoiceSettings(null)}
          agent={showVoiceSettings}
          onSave={() => {
            fetchAgents();
            setShowVoiceSettings(null);
          }}
        />
      )}

      {/* Edit Agent Dialog */}
      <Dialog open={!!editingAgent} onOpenChange={() => setEditingAgent(null)}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Edit Agent
            </DialogTitle>
            <DialogDescription>
              Update agent settings and live transfer configuration
            </DialogDescription>
          </DialogHeader>
          
          {editingAgent && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Agent Name</Label>
                  <Input
                    value={editingAgent.name}
                    onChange={(e) => setEditingAgent({...editingAgent, name: e.target.value})}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label>Email</Label>
                  <Input
                    value={editingAgent.email}
                    onChange={(e) => setEditingAgent({...editingAgent, email: e.target.value})}
                    className="mt-1"
                  />
                </div>
              </div>
              
              <div>
                <Label>Calendly Link</Label>
                <Input
                  value={editingAgent.calendly_link}
                  onChange={(e) => setEditingAgent({...editingAgent, calendly_link: e.target.value})}
                  className="mt-1"
                />
              </div>

              {/* Live Transfer Settings */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <Label className="text-base font-semibold">Live Transfer</Label>
                    <p className="text-xs text-gray-500">Transfer interested prospects to your team</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={editingAgent.transfer_enabled}
                      onChange={(e) => setEditingAgent({...editingAgent, transfer_enabled: e.target.checked})}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                
                {editingAgent.transfer_enabled && (
                  <div className="space-y-3 pl-4 border-l-2 border-blue-200">
                    <div>
                      <Label>Transfer Phone Number *</Label>
                      <Input
                        data-testid="edit-transfer-phone-input"
                        value={editingAgent.transfer_phone_number}
                        onChange={(e) => setEditingAgent({...editingAgent, transfer_phone_number: e.target.value})}
                        placeholder="+1 (555) 123-4567"
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-400 mt-1">
                        AI will ask: "Would you like me to connect you with a team member?" If yes, calls transfer here.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Voice Tuning Settings */}
              <div className="border-t pt-4">
                <div className="mb-3">
                  <Label className="text-base font-semibold flex items-center gap-2">
                    <Volume2 className="w-4 h-4" />
                    Voice Tuning
                  </Label>
                  <p className="text-xs text-gray-500">Adjust how natural and expressive the AI voice sounds</p>
                </div>
                
                <div className="space-y-5 pl-4 border-l-2 border-purple-200">
                  {/* Stability Slider */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <Label className="text-sm">Stability</Label>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {((editingAgent.voice_settings?.stability ?? 0.5) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Slider
                      value={[editingAgent.voice_settings?.stability ?? 0.5]}
                      onValueChange={([val]) => setEditingAgent({
                        ...editingAgent, 
                        voice_settings: {...(editingAgent.voice_settings || {}), stability: val}
                      })}
                      min={0}
                      max={1}
                      step={0.05}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>More expressive</span>
                      <span>More consistent</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      Lower = more emotional variation (natural). Higher = more predictable (can sound robotic).
                    </p>
                  </div>

                  {/* Similarity Boost Slider */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <Label className="text-sm">Clarity</Label>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {((editingAgent.voice_settings?.similarity_boost ?? 0.75) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Slider
                      value={[editingAgent.voice_settings?.similarity_boost ?? 0.75]}
                      onValueChange={([val]) => setEditingAgent({
                        ...editingAgent, 
                        voice_settings: {...(editingAgent.voice_settings || {}), similarity_boost: val}
                      })}
                      min={0}
                      max={1}
                      step={0.05}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>Softer</span>
                      <span>Clearer</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      Controls voice clarity and how closely it matches the original speaker.
                    </p>
                  </div>

                  {/* Style Slider */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <Label className="text-sm">Expressiveness</Label>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {((editingAgent.voice_settings?.style ?? 0.4) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Slider
                      value={[editingAgent.voice_settings?.style ?? 0.4]}
                      onValueChange={([val]) => setEditingAgent({
                        ...editingAgent, 
                        voice_settings: {...(editingAgent.voice_settings || {}), style: val}
                      })}
                      min={0}
                      max={1}
                      step={0.05}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>Neutral</span>
                      <span>Animated</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      Adds emotion and liveliness. Too high may cause artifacts.
                    </p>
                  </div>

                  {/* Quick Presets */}
                  <div>
                    <Label className="text-sm mb-2 block">Quick Presets</Label>
                    <div className="flex gap-2 flex-wrap">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setEditingAgent({
                          ...editingAgent,
                          voice_settings: { stability: 0.3, similarity_boost: 0.7, style: 0.5 }
                        })}
                        className="text-xs"
                      >
                        🎭 Natural
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setEditingAgent({
                          ...editingAgent,
                          voice_settings: { stability: 0.5, similarity_boost: 0.75, style: 0.3 }
                        })}
                        className="text-xs"
                      >
                        💼 Professional
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setEditingAgent({
                          ...editingAgent,
                          voice_settings: { stability: 0.25, similarity_boost: 0.8, style: 0.6 }
                        })}
                        className="text-xs"
                      >
                        ⚡ Energetic
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setEditingAgent({
                          ...editingAgent,
                          voice_settings: { stability: 0.6, similarity_boost: 0.7, style: 0.2 }
                        })}
                        className="text-xs"
                      >
                        🧘 Calm
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* DISC Personality Tips - Condensed */}
              <div className="border-t pt-4">
                <div className="mb-3">
                  <Label className="text-base font-semibold flex items-center gap-2">
                    <Brain className="w-4 h-4" />
                    Personality Detection Tips
                  </Label>
                  <p className="text-xs text-gray-500">Add these to your script to quickly identify buyer type</p>
                </div>
                
                <div className="bg-purple-50 rounded-lg p-4 border border-purple-100">
                  <p className="text-xs font-medium text-purple-800 mb-2">🎯 Ask early in the call:</p>
                  <p className="text-sm text-gray-700 italic mb-3 bg-white/60 p-2 rounded">
                    "What's most important here: getting straight to results, or understanding all the details first?"
                  </p>
                  
                  <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-red-500 text-white rounded flex items-center justify-center font-bold">D</span>
                      <span>"results" → Be direct</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-yellow-500 text-white rounded flex items-center justify-center font-bold">I</span>
                      <span>vague → Be energetic</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-green-500 text-white rounded flex items-center justify-center font-bold">S</span>
                      <span>"both" → Be patient</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-5 h-5 bg-blue-500 text-white rounded flex items-center justify-center font-bold">C</span>
                      <span>"details" → Be precise</span>
                    </div>
                  </div>
                  
                  <p className="text-xs text-purple-600 italic">AI auto-detects and adapts in real-time. Personality shows in Call History.</p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center gap-2">
                  <Label>Active</Label>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={editingAgent.is_active}
                      onChange={(e) => setEditingAgent({...editingAgent, is_active: e.target.checked})}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                  </label>
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingAgent(null)}>Cancel</Button>
            <Button 
              onClick={updateAgent}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Call History Page

export default Agents;
