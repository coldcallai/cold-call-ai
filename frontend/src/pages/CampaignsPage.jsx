import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import StatusBadge from "@/components/StatusBadge";
import TrustLine from "@/components/TrustLine";
import {
  Target, Plus, Play, Pause, Trash2, Clock, Settings, RefreshCw, PhoneOff, Mail
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Campaigns = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showFollowUpSettings, setShowFollowUpSettings] = useState(null); // campaign for settings modal
  const [followUpSettings, setFollowUpSettings] = useState({
    enabled: true,
    no_answer_retry_enabled: true,
    no_answer_retry_count: 3,
    no_answer_retry_delay_hours: 24,
    voicemail_followup_enabled: true,
    voicemail_followup_delay_hours: 48
  });
  const [newCampaign, setNewCampaign] = useState({
    name: "",
    description: "",
    ai_script: "Hello, this is an AI assistant calling about credit card processing solutions for your business. Am I speaking with the owner or manager?",
    calls_per_day: 100,
    voicemail_enabled: true,
    voicemail_message: "",
    response_wait_seconds: 4,
    company_name: "",
    icp_config: {
      target_industries: [],
      preferred_company_sizes: ["11-50", "51-200"],
      min_intent_signals: 1,
      preferred_roles: ["Owner", "CEO", "Manager", "Director"]
    },
    min_icp_score: 0,
    // A/B Testing
    ab_testing_enabled: false,
    script_variant_b: "",
    ab_split_percentage: 50
  });

  const fetchCampaigns = async () => {
    try {
      const response = await axios.get(`${API}/campaigns`);
      setCampaigns(response.data);
    } catch (error) {
      toast.error("Failed to load campaigns");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const createCampaign = async () => {
    if (!newCampaign.name || !newCampaign.ai_script) {
      toast.error("Please fill in all required fields");
      return;
    }

    try {
      await axios.post(`${API}/campaigns`, newCampaign);
      toast.success("Campaign created!");
      setShowCreate(false);
      setNewCampaign({ name: "", description: "", ai_script: "", calls_per_day: 100, voicemail_enabled: true, voicemail_message: "", response_wait_seconds: 4, company_name: "", icp_config: { target_industries: [], preferred_company_sizes: ["11-50", "51-200"], min_intent_signals: 1, preferred_roles: ["Owner", "CEO", "Manager", "Director"] }, min_icp_score: 0 });
      fetchCampaigns();
    } catch (error) {
      toast.error("Failed to create campaign");
    }
  };

  const toggleCampaign = async (campaign) => {
    const endpoint = campaign.status === 'active' ? 'pause' : 'start';
    try {
      await axios.post(`${API}/campaigns/${campaign.id}/${endpoint}`);
      toast.success(`Campaign ${endpoint === 'start' ? 'started' : 'paused'}`);
      fetchCampaigns();
    } catch (error) {
      toast.error("Failed to update campaign");
    }
  };

  const deleteCampaign = async (id) => {
    try {
      await axios.delete(`${API}/campaigns/${id}`);
      toast.success("Campaign deleted");
      fetchCampaigns();
    } catch (error) {
      toast.error("Failed to delete campaign");
    }
  };

  const openFollowUpSettings = async (campaign) => {
    setShowFollowUpSettings(campaign);
    try {
      const response = await axios.get(`${API}/campaigns/${campaign.id}/followup-settings`);
      setFollowUpSettings(response.data.settings);
    } catch (error) {
      // Use defaults if no settings exist
      setFollowUpSettings({
        enabled: true,
        no_answer_retry_enabled: true,
        no_answer_retry_count: 3,
        no_answer_retry_delay_hours: 24,
        voicemail_followup_enabled: true,
        voicemail_followup_delay_hours: 48
      });
    }
  };

  const saveFollowUpSettings = async () => {
    if (!showFollowUpSettings) return;
    
    try {
      const formData = new FormData();
      Object.entries(followUpSettings).forEach(([key, value]) => {
        formData.append(key, value);
      });
      
      await axios.put(`${API}/campaigns/${showFollowUpSettings.id}/followup-settings`, formData);
      toast.success("Follow-up settings saved!");
      setShowFollowUpSettings(null);
      fetchCampaigns();
    } catch (error) {
      toast.error("Failed to save follow-up settings");
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="campaigns-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Campaigns
          </h1>
          <p className="text-gray-500 mt-1">Manage your AI calling campaigns</p>
          <TrustLine className="mt-2" />
        </div>
        <Button 
          data-testid="create-campaign-btn"
          onClick={() => setShowCreate(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Campaign
        </Button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1,2,3].map(i => <Skeleton key={i} className="h-48" />)}
        </div>
      ) : campaigns.length === 0 ? (
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardContent className="p-12 text-center">
            <Target className="w-16 h-16 text-gray-300 mx-auto" />
            <p className="text-gray-500 mt-4">No campaigns yet. Create your first campaign to start calling.</p>
            <Button 
              onClick={() => setShowCreate(true)}
              className="mt-4 bg-blue-600 hover:bg-blue-700 text-white"
            >
              Create Campaign
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {campaigns.map(campaign => (
            <Card key={campaign.id} className="bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow" data-testid={`campaign-card-${campaign.id}`}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                      {campaign.name}
                    </CardTitle>
                    <StatusBadge status={campaign.status} />
                  </div>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      data-testid={`followup-settings-${campaign.id}`}
                      onClick={() => openFollowUpSettings(campaign)}
                      className="text-cyan-600 hover:text-cyan-700 hover:bg-cyan-50"
                      title="Follow-up Settings"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      data-testid={`delete-campaign-${campaign.id}`}
                      onClick={() => deleteCampaign(campaign.id)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                  {campaign.description || "No description"}
                </p>
                
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="text-center p-2 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">Total Calls</p>
                    <p className="text-lg font-semibold text-gray-900">{campaign.total_calls}</p>
                  </div>
                  <div className="text-center p-2 bg-emerald-50 rounded-lg">
                    <p className="text-xs text-gray-500">Qualified</p>
                    <p className="text-lg font-semibold text-emerald-600">{campaign.qualified_leads}</p>
                  </div>
                </div>

                <Button
                  className="w-full"
                  data-testid={`toggle-campaign-${campaign.id}`}
                  variant={campaign.status === 'active' ? 'outline' : 'default'}
                  onClick={() => toggleCampaign(campaign)}
                >
                  {campaign.status === 'active' ? (
                    <>
                      <Pause className="w-4 h-4 mr-2" />
                      Pause Campaign
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Start Campaign
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Campaign Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Create New Campaign
            </DialogTitle>
            <DialogDescription>
              Set up a new AI calling campaign with a custom script
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="campaign-name">Campaign Name *</Label>
              <Input
                id="campaign-name"
                data-testid="campaign-name-input"
                value={newCampaign.name}
                onChange={(e) => setNewCampaign({...newCampaign, name: e.target.value})}
                placeholder="e.g., Q1 Credit Card Processing Outreach"
                className="mt-1"
              />
            </div>
            
            <div>
              <Label htmlFor="campaign-desc">Description</Label>
              <Input
                id="campaign-desc"
                data-testid="campaign-desc-input"
                value={newCampaign.description}
                onChange={(e) => setNewCampaign({...newCampaign, description: e.target.value})}
                placeholder="Brief description of the campaign"
                className="mt-1"
              />
            </div>
            
            <div>
              <Label htmlFor="ai-script">AI Script {newCampaign.ab_testing_enabled ? "(Variant A)" : "*"}</Label>
              <Textarea
                id="ai-script"
                data-testid="campaign-script-input"
                value={newCampaign.ai_script}
                onChange={(e) => setNewCampaign({...newCampaign, ai_script: e.target.value})}
                placeholder="Enter the script the AI will use during calls..."
                className="mt-1 min-h-[150px]"
              />
              <p className="text-xs text-blue-600 mt-1 bg-blue-50 px-2 py-1 rounded">
                💡 Use {'{company}'} for your company name, {'{contact_name}'} for the lead's name. Keep responses SHORT (1-2 sentences) for natural conversation flow.
              </p>
            </div>

            {/* A/B Testing Section */}
            <div className="border border-purple-200 rounded-lg p-4 bg-purple-50/50">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h4 className="font-medium text-purple-900 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    A/B Script Testing
                  </h4>
                  <p className="text-sm text-purple-700">Test two scripts to see which converts better</p>
                </div>
                <Button
                  variant={newCampaign.ab_testing_enabled ? "default" : "outline"}
                  size="sm"
                  onClick={() => setNewCampaign({...newCampaign, ab_testing_enabled: !newCampaign.ab_testing_enabled})}
                  className={newCampaign.ab_testing_enabled ? "bg-purple-600 hover:bg-purple-700" : ""}
                >
                  {newCampaign.ab_testing_enabled ? "Enabled" : "Enable"}
                </Button>
              </div>

              {newCampaign.ab_testing_enabled && (
                <div className="space-y-4 mt-4 pt-4 border-t border-purple-200">
                  <div>
                    <Label htmlFor="script-variant-b">Script Variant B</Label>
                    <Textarea
                      id="script-variant-b"
                      value={newCampaign.script_variant_b}
                      onChange={(e) => setNewCampaign({...newCampaign, script_variant_b: e.target.value})}
                      placeholder="Enter an alternative script to test against Variant A..."
                      className="mt-1 min-h-[120px] bg-white"
                    />
                  </div>

                  <div>
                    <Label>Traffic Split</Label>
                    <div className="flex items-center gap-4 mt-2">
                      <div className="flex-1">
                        <input
                          type="range"
                          min="10"
                          max="90"
                          step="10"
                          value={newCampaign.ab_split_percentage}
                          onChange={(e) => setNewCampaign({...newCampaign, ab_split_percentage: parseInt(e.target.value)})}
                          className="w-full"
                        />
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded font-medium">
                          A: {newCampaign.ab_split_percentage}%
                        </span>
                        <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded font-medium">
                          B: {100 - newCampaign.ab_split_percentage}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-3 border border-purple-200">
                    <p className="text-sm text-purple-800">
                      <strong>📊 How it works:</strong> Leads will be randomly assigned to Variant A or B. Track qualification rates in Analytics to see which script performs better.
                    </p>
                  </div>
                </div>
              )}
            </div>
            
            <div>
              <Label htmlFor="calls-per-day">Calls Per Day</Label>
              <Input
                id="calls-per-day"
                data-testid="campaign-calls-input"
                type="number"
                value={newCampaign.calls_per_day}
                onChange={(e) => setNewCampaign({...newCampaign, calls_per_day: parseInt(e.target.value) || 0})}
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">Recommended: 50-100 for B2B, 200+ for high-volume campaigns</p>
            </div>

            <div>
              <Label htmlFor="company-name">Your Company Name</Label>
              <Input
                id="company-name"
                value={newCampaign.company_name}
                onChange={(e) => setNewCampaign({...newCampaign, company_name: e.target.value})}
                placeholder="e.g., ABC Solutions"
                className="mt-1"
              />
              <p className="text-xs text-gray-400 mt-1">Used in AI greeting and voicemail</p>
            </div>

            {/* AI Conversation Settings */}
            <div className="border-t pt-4 mt-4">
              <h4 className="font-medium mb-3">AI Conversation Settings</h4>
              
              <div className="mb-4">
                <Label htmlFor="response-wait">Response Wait Time (seconds)</Label>
                <div className="flex items-center gap-3 mt-1">
                  <Input
                    id="response-wait"
                    type="number"
                    min="1"
                    max="10"
                    value={newCampaign.response_wait_seconds}
                    onChange={(e) => setNewCampaign({...newCampaign, response_wait_seconds: parseInt(e.target.value) || 4})}
                    className="w-24"
                  />
                  <span className="text-sm text-gray-500">seconds</span>
                  <div className="flex-1">
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={newCampaign.response_wait_seconds}
                      onChange={(e) => setNewCampaign({...newCampaign, response_wait_seconds: parseInt(e.target.value)})}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                    />
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  How long AI waits for caller to respond before continuing. Recommended: 4-6 seconds.
                </p>
              </div>
            </div>

            {/* Voicemail Drop Settings */}
            <div className="border-t pt-4 mt-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <Label className="text-base font-medium">Voicemail Drop</Label>
                  <p className="text-sm text-gray-500">Auto-leave voicemail when machine detected (saves ~$0.14/call)</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newCampaign.voicemail_enabled}
                    onChange={(e) => setNewCampaign({...newCampaign, voicemail_enabled: e.target.checked})}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-cyan-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500"></div>
                </label>
              </div>
              
              {newCampaign.voicemail_enabled && (
                <div>
                  <Label htmlFor="voicemail-message">Voicemail Drop Script</Label>
                  <Textarea
                    id="voicemail-message"
                    value={newCampaign.voicemail_message}
                    onChange={(e) => setNewCampaign({...newCampaign, voicemail_message: e.target.value})}
                    placeholder="Hi {contact_name}, this is {agent_name} calling for {business_name}. I tried reaching you about an opportunity that could help your business. Visit dialgenix.ai to learn more, or I'll try you again soon. Thanks!"
                    className="mt-1 min-h-[100px]"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Variables: {'{contact_name}'}, {'{business_name}'}, {'{company_name}'}, {'{agent_name}'} • Include your website URL!
                  </p>
                </div>
              )}
            </div>

            {/* ICP (Ideal Customer Profile) Settings */}
            <div className="border-t pt-4 mt-4">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-5 h-5 text-cyan-500" />
                <h4 className="font-medium">Ideal Customer Profile (ICP)</h4>
              </div>
              <p className="text-sm text-gray-500 mb-4">Configure which leads are prioritized for calling based on their fit.</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Target Company Sizes</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {["1-10", "11-50", "51-200", "201-500", "500+"].map(size => (
                      <button
                        key={size}
                        type="button"
                        onClick={() => {
                          const current = newCampaign.icp_config?.preferred_company_sizes || [];
                          const updated = current.includes(size) 
                            ? current.filter(s => s !== size)
                            : [...current, size];
                          setNewCampaign({
                            ...newCampaign, 
                            icp_config: {...newCampaign.icp_config, preferred_company_sizes: updated}
                          });
                        }}
                        className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
                          (newCampaign.icp_config?.preferred_company_sizes || []).includes(size)
                            ? "bg-cyan-100 border-cyan-500 text-cyan-700"
                            : "border-gray-300 text-gray-600 hover:border-gray-400"
                        }`}
                      >
                        {size} employees
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <Label>Preferred Roles</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {["Owner", "CEO", "Manager", "Director", "VP", "CFO"].map(role => (
                      <button
                        key={role}
                        type="button"
                        onClick={() => {
                          const current = newCampaign.icp_config?.preferred_roles || [];
                          const updated = current.includes(role) 
                            ? current.filter(r => r !== role)
                            : [...current, role];
                          setNewCampaign({
                            ...newCampaign, 
                            icp_config: {...newCampaign.icp_config, preferred_roles: updated}
                          });
                        }}
                        className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
                          (newCampaign.icp_config?.preferred_roles || []).includes(role)
                            ? "bg-cyan-100 border-cyan-500 text-cyan-700"
                            : "border-gray-300 text-gray-600 hover:border-gray-400"
                        }`}
                      >
                        {role}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <Label htmlFor="target-industries">Target Industries (comma-separated)</Label>
                <Input
                  id="target-industries"
                  placeholder="e.g., Restaurant, Retail, Healthcare, Professional Services"
                  value={(newCampaign.icp_config?.target_industries || []).join(", ")}
                  onChange={(e) => {
                    const industries = e.target.value ? e.target.value.split(",").map(i => i.trim()).filter(i => i) : [];
                    setNewCampaign({
                      ...newCampaign,
                      icp_config: {...newCampaign.icp_config, target_industries: industries}
                    });
                  }}
                  className="mt-1"
                />
                <p className="text-xs text-gray-400 mt-1">Leave empty to target all industries</p>
              </div>

              <div className="mt-4">
                <Label htmlFor="min-icp">Minimum ICP Score to Dial</Label>
                <div className="flex items-center gap-3 mt-1">
                  <Input
                    id="min-icp"
                    type="number"
                    min="0"
                    max="100"
                    value={newCampaign.min_icp_score || 0}
                    onChange={(e) => setNewCampaign({...newCampaign, min_icp_score: parseInt(e.target.value) || 0})}
                    className="w-24"
                  />
                  <span className="text-sm text-gray-500">/ 100</span>
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="10"
                      value={newCampaign.min_icp_score || 0}
                      onChange={(e) => setNewCampaign({...newCampaign, min_icp_score: parseInt(e.target.value)})}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                    />
                  </div>
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>0 - Call all leads</span>
                  <span>40 - Skip D-tier</span>
                  <span>60 - Only A/B tier</span>
                  <span>80 - Only A-tier</span>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button 
              data-testid="save-campaign-btn"
              onClick={createCampaign}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Create Campaign
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Follow-Up Settings Modal */}
      <Dialog open={!!showFollowUpSettings} onOpenChange={() => setShowFollowUpSettings(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              <RefreshCw className="w-5 h-5 text-cyan-500" />
              Follow-Up Settings
            </DialogTitle>
            <DialogDescription>
              Configure automatic follow-up calls for "{showFollowUpSettings?.name}"
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Master Toggle */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <Label className="text-base font-medium">Enable Auto Follow-Ups</Label>
                <p className="text-sm text-gray-500">Automatically schedule retry calls</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={followUpSettings.enabled}
                  onChange={(e) => setFollowUpSettings({...followUpSettings, enabled: e.target.checked})}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-cyan-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500"></div>
              </label>
            </div>

            {followUpSettings.enabled && (
              <>
                {/* No-Answer Retry Settings */}
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <PhoneOff className="w-4 h-4 text-orange-500" />
                      <Label className="font-medium">No-Answer Retries</Label>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={followUpSettings.no_answer_retry_enabled}
                        onChange={(e) => setFollowUpSettings({...followUpSettings, no_answer_retry_enabled: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-orange-500"></div>
                    </label>
                  </div>

                  {followUpSettings.no_answer_retry_enabled && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-sm text-gray-600">Max Retries</Label>
                        <Select
                          value={String(followUpSettings.no_answer_retry_count)}
                          onValueChange={(v) => setFollowUpSettings({...followUpSettings, no_answer_retry_count: parseInt(v)})}
                        >
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="1">1 retry</SelectItem>
                            <SelectItem value="2">2 retries</SelectItem>
                            <SelectItem value="3">3 retries</SelectItem>
                            <SelectItem value="5">5 retries</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-sm text-gray-600">Delay Between</Label>
                        <Select
                          value={String(followUpSettings.no_answer_retry_delay_hours)}
                          onValueChange={(v) => setFollowUpSettings({...followUpSettings, no_answer_retry_delay_hours: parseInt(v)})}
                        >
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="4">4 hours</SelectItem>
                            <SelectItem value="12">12 hours</SelectItem>
                            <SelectItem value="24">24 hours</SelectItem>
                            <SelectItem value="48">48 hours</SelectItem>
                            <SelectItem value="72">72 hours</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  )}
                </div>

                {/* Voicemail Follow-Up Settings */}
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-blue-500" />
                      <Label className="font-medium">Voicemail Follow-Up</Label>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={followUpSettings.voicemail_followup_enabled}
                        onChange={(e) => setFollowUpSettings({...followUpSettings, voicemail_followup_enabled: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-500"></div>
                    </label>
                  </div>

                  {followUpSettings.voicemail_followup_enabled && (
                    <div>
                      <Label className="text-sm text-gray-600">Follow up after voicemail</Label>
                      <Select
                        value={String(followUpSettings.voicemail_followup_delay_hours)}
                        onValueChange={(v) => setFollowUpSettings({...followUpSettings, voicemail_followup_delay_hours: parseInt(v)})}
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="24">24 hours</SelectItem>
                          <SelectItem value="48">48 hours (recommended)</SelectItem>
                          <SelectItem value="72">72 hours</SelectItem>
                          <SelectItem value="96">4 days</SelectItem>
                          <SelectItem value="168">1 week</SelectItem>
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-gray-400 mt-2">
                        Give leads time to listen to voicemail before calling back
                      </p>
                    </div>
                  )}
                </div>

                {/* Info Box */}
                <div className="bg-cyan-50 border border-cyan-200 rounded-lg p-4">
                  <p className="text-sm text-cyan-800">
                    <strong>How it works:</strong> When a call ends with no-answer or voicemail, 
                    DialGenix automatically schedules a follow-up call based on these settings. 
                    Follow-ups stop when the lead answers or gets booked.
                  </p>
                </div>
              </>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFollowUpSettings(null)}>Cancel</Button>
            <Button 
              onClick={saveFollowUpSettings}
              className="bg-cyan-600 hover:bg-cyan-700 text-white"
              data-testid="save-followup-settings-btn"
            >
              Save Settings
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Campaigns;
