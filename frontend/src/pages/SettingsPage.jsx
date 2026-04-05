import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Settings, Phone, Mail, CreditCard, Shield, Users, Plus, Trash2, 
  RefreshCw, ExternalLink, AlertCircle, CheckCircle, Building2, Calendar, ChevronRight, Database, Search, Zap
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SettingsPage = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [webhooks, setWebhooks] = useState([]);
  const [showCreateWebhook, setShowCreateWebhook] = useState(false);
  const [newWebhook, setNewWebhook] = useState({
    name: "",
    event_type: "lead_qualified",
    notification_emails: ""
  });
  const [testingWebhook, setTestingWebhook] = useState(null);
  
  // Team management state
  const [teamMembers, setTeamMembers] = useState([]);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [loadingTeam, setLoadingTeam] = useState(false);
  
  // Number Pool state
  const [numberPool, setNumberPool] = useState([]);
  const [showAddNumber, setShowAddNumber] = useState(false);
  const [newNumber, setNewNumber] = useState("");
  const [rotationMode, setRotationMode] = useState("round-robin");
  const [numberPoolEnabled, setNumberPoolEnabled] = useState(false);
  
  // Integration setup modals
  const [showTwilioSetup, setShowTwilioSetup] = useState(false);
  const [showTwitterSetup, setShowTwitterSetup] = useState(false);
  const [showEmailSetup, setShowEmailSetup] = useState(false);
  const [showCalendlySetup, setShowCalendlySetup] = useState(false);
  
  // Integration form states
  const [twilioForm, setTwilioForm] = useState({
    account_sid: "",
    auth_token: "",
    phone_number: ""
  });
  const [twitterForm, setTwitterForm] = useState({
    api_key: "",
    api_secret: "",
    bearer_token: ""
  });
  const [emailForm, setEmailForm] = useState({
    resend_api_key: "",
    from_email: ""
  });
  const [calendlyForm, setCalendlyForm] = useState({
    calendly_url: ""
  });
  const [apolloForm, setApolloForm] = useState({
    api_key: ""
  });
  
  // Additional modal states
  const [showApolloSetup, setShowApolloSetup] = useState(false);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
      // Load number pool settings
      if (response.data.number_pool) {
        setNumberPool(response.data.number_pool || []);
        setRotationMode(response.data.rotation_mode || "round-robin");
        setNumberPoolEnabled(response.data.number_pool_enabled || false);
      }
      // Load integration settings into forms
      if (response.data.twilio_account_sid) {
        setTwilioForm({
          account_sid: response.data.twilio_account_sid || "",
          auth_token: response.data.twilio_auth_token ? "••••••••" : "",
          phone_number: response.data.twilio_phone_number || ""
        });
      }
      if (response.data.twitter_api_key) {
        setTwitterForm({
          api_key: response.data.twitter_api_key ? "••••••••" : "",
          api_secret: response.data.twitter_api_secret ? "••••••••" : "",
          bearer_token: response.data.twitter_bearer_token ? "••••••••" : ""
        });
      }
      if (response.data.resend_api_key) {
        setEmailForm({
          resend_api_key: response.data.resend_api_key ? "••••••••" : "",
          from_email: response.data.from_email || ""
        });
      }
      if (response.data.calendly_url) {
        setCalendlyForm({
          calendly_url: response.data.calendly_url || ""
        });
      }
      if (response.data.apollo_api_key) {
        setApolloForm({
          api_key: response.data.apollo_api_key ? "••••••••" : ""
        });
      }
    } catch (error) {
      toast.error("Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  const fetchWebhooks = async () => {
    try {
      const response = await axios.get(`${API}/webhooks`);
      setWebhooks(response.data);
    } catch (error) {
      console.error("Failed to fetch webhooks:", error);
    }
  };

  const fetchTeamMembers = async () => {
    setLoadingTeam(true);
    try {
      const response = await axios.get(`${API}/team/members`);
      setTeamMembers(response.data);
    } catch (error) {
      console.error("Failed to fetch team members:", error);
    } finally {
      setLoadingTeam(false);
    }
  };

  const inviteTeamMember = async () => {
    if (!inviteEmail) {
      toast.error("Please enter an email address");
      return;
    }
    try {
      await axios.post(`${API}/team/invite`, {
        email: inviteEmail,
        role: inviteRole
      });
      toast.success(`Invitation sent to ${inviteEmail}`);
      setShowInviteModal(false);
      setInviteEmail("");
      fetchTeamMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send invitation");
    }
  };

  const removeTeamMember = async (memberId) => {
    if (!confirm("Are you sure you want to remove this team member?")) return;
    try {
      await axios.delete(`${API}/team/members/${memberId}`);
      toast.success("Team member removed");
      fetchTeamMembers();
    } catch (error) {
      toast.error("Failed to remove team member");
    }
  };

  const updateMemberRole = async (memberId, newRole) => {
    try {
      await axios.put(`${API}/team/members/${memberId}`, { role: newRole });
      toast.success("Role updated");
      fetchTeamMembers();
    } catch (error) {
      toast.error("Failed to update role");
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchWebhooks();
    fetchTeamMembers();
  }, []);

  const updateSettings = async (updates) => {
    try {
      const response = await axios.put(`${API}/settings`, updates);
      setSettings(response.data);
      toast.success("Settings updated");
    } catch (error) {
      toast.error("Failed to update settings");
    }
  };

  const createWebhook = async () => {
    if (!newWebhook.name || !newWebhook.notification_emails) {
      toast.error("Please fill in all fields");
      return;
    }

    const emails = newWebhook.notification_emails.split(',').map(e => e.trim()).filter(e => e);
    if (emails.length === 0) {
      toast.error("Please enter at least one email");
      return;
    }

    try {
      await axios.post(`${API}/webhooks`, {
        name: newWebhook.name,
        event_type: newWebhook.event_type,
        notification_emails: emails
      });
      toast.success("Webhook created!");
      setShowCreateWebhook(false);
      setNewWebhook({ name: "", event_type: "lead_qualified", notification_emails: "" });
      fetchWebhooks();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create webhook");
    }
  };

  const toggleWebhook = async (webhook) => {
    try {
      await axios.put(`${API}/webhooks/${webhook.id}`, { is_active: !webhook.is_active });
      toast.success(`Webhook ${webhook.is_active ? 'disabled' : 'enabled'}`);
      fetchWebhooks();
    } catch (error) {
      toast.error("Failed to update webhook");
    }
  };

  const deleteWebhook = async (id) => {
    try {
      await axios.delete(`${API}/webhooks/${id}`);
      toast.success("Webhook deleted");
      fetchWebhooks();
    } catch (error) {
      toast.error("Failed to delete webhook");
    }
  };

  const testWebhook = async (webhook) => {
    setTestingWebhook(webhook.id);
    try {
      await axios.post(`${API}/webhooks/test/${webhook.id}`);
      toast.success("Test notification sent!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send test notification");
    } finally {
      setTestingWebhook(null);
    }
  };

  if (loading) {
    return (
      <div className="p-6 md:p-8 space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="settings-page">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
          Settings
        </h1>
        <p className="text-gray-500 mt-1">Configure integrations, notifications, and qualification criteria</p>
        <p className="text-xs text-blue-600 mt-1 bg-blue-50 px-2 py-1 rounded inline-block">
          💡 Connect Twilio for calls, ElevenLabs for voice, Apollo for lead enrichment, and Stripe for payments.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Integration Status
            </CardTitle>
            <CardDescription>Connect external services</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Twilio Voice */}
            <div 
              onClick={() => setShowTwilioSetup(true)}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Phone className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium">Twilio Voice</p>
                  <p className="text-sm text-gray-500">For making real phone calls</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={settings?.twilio_configured ? "default" : "secondary"}>
                  {settings?.twilio_configured ? "Connected" : "Not Connected"}
                </Badge>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
              </div>
            </div>
            
            {/* Twitter/X API */}
            <div 
              onClick={() => setShowTwitterSetup(true)}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <Search className="w-5 h-5 text-gray-600" />
                </div>
                <div>
                  <p className="font-medium">Twitter/X API</p>
                  <p className="text-sm text-gray-500">For intent monitoring</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={settings?.twitter_configured ? "default" : "secondary"}>
                  {settings?.twitter_configured ? "Connected" : "Not Connected"}
                </Badge>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
              </div>
            </div>
            
            {/* Email Notifications */}
            <div 
              onClick={() => setShowEmailSetup(true)}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Mail className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="font-medium">Email Notifications</p>
                  <p className="text-sm text-gray-500">Via Resend API</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={settings?.email_notifications_configured ? "default" : "secondary"}>
                  {settings?.email_notifications_configured ? "Connected" : "Not Connected"}
                </Badge>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
              </div>
            </div>
            
            {/* Calendly */}
            <div 
              onClick={() => setShowCalendlySetup(true)}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium">Calendly</p>
                  <p className="text-sm text-gray-500">For booking meetings</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={settings?.calendly_url ? "default" : "secondary"}>
                  {settings?.calendly_url ? "Connected" : "Not Connected"}
                </Badge>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
              </div>
            </div>

            {/* Apollo.io Lead Enrichment */}
            <div 
              onClick={() => setShowApolloSetup(true)}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <Database className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <p className="font-medium">Apollo.io</p>
                  <p className="text-sm text-gray-500">Lead enrichment & contact names</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={settings?.apollo_configured ? "default" : "secondary"}>
                  {settings?.apollo_configured ? "Connected" : "Not Connected"}
                </Badge>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Twilio Setup Modal */}
        {showTwilioSetup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-lg mx-4">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Phone className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <CardTitle>Connect Twilio Voice</CardTitle>
                    <CardDescription>Required for making real phone calls</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-blue-900 mb-2">How to get your Twilio credentials:</p>
                  <ol className="text-blue-800 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://console.twilio.com" target="_blank" rel="noopener noreferrer" className="underline">console.twilio.com</a></li>
                    <li>Copy your Account SID and Auth Token from the dashboard</li>
                    <li>Buy a phone number from Phone Numbers → Buy a Number</li>
                  </ol>
                </div>
                
                <div>
                  <Label htmlFor="twilio_sid">Account SID</Label>
                  <Input
                    id="twilio_sid"
                    placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    value={twilioForm.account_sid}
                    onChange={(e) => setTwilioForm({...twilioForm, account_sid: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
                
                <div>
                  <Label htmlFor="twilio_token">Auth Token</Label>
                  <Input
                    id="twilio_token"
                    type="password"
                    placeholder="Enter your auth token"
                    value={twilioForm.auth_token}
                    onChange={(e) => setTwilioForm({...twilioForm, auth_token: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
                
                <div>
                  <Label htmlFor="twilio_phone">Phone Number</Label>
                  <Input
                    id="twilio_phone"
                    placeholder="+14155551234"
                    value={twilioForm.phone_number}
                    onChange={(e) => setTwilioForm({...twilioForm, phone_number: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">Your Twilio phone number in E.164 format</p>
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button variant="outline" onClick={() => setShowTwilioSetup(false)} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    if (!twilioForm.account_sid || !twilioForm.auth_token || !twilioForm.phone_number) {
                      toast.error("Please fill in all fields");
                      return;
                    }
                    try {
                      await updateSettings({
                        twilio_account_sid: twilioForm.account_sid,
                        twilio_auth_token: twilioForm.auth_token,
                        twilio_phone_number: twilioForm.phone_number,
                        twilio_configured: true
                      });
                      setShowTwilioSetup(false);
                      toast.success("Twilio connected successfully!");
                    } catch (error) {
                      toast.error("Failed to save Twilio settings");
                    }
                  }}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  Connect Twilio
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Twitter Setup Modal */}
        {showTwitterSetup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-lg mx-4">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Search className="w-5 h-5 text-gray-600" />
                  </div>
                  <div>
                    <CardTitle>Connect Twitter/X API</CardTitle>
                    <CardDescription>For monitoring buyer intent signals</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-gray-900 mb-2">How to get your X API credentials:</p>
                  <ol className="text-gray-700 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://developer.twitter.com" target="_blank" rel="noopener noreferrer" className="underline text-blue-600">developer.twitter.com</a></li>
                    <li>Create a project and app</li>
                    <li>Generate API keys and Bearer Token</li>
                  </ol>
                </div>
                
                <div>
                  <Label htmlFor="twitter_key">API Key</Label>
                  <Input
                    id="twitter_key"
                    type="password"
                    placeholder="Enter your API key"
                    value={twitterForm.api_key}
                    onChange={(e) => setTwitterForm({...twitterForm, api_key: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
                
                <div>
                  <Label htmlFor="twitter_secret">API Secret</Label>
                  <Input
                    id="twitter_secret"
                    type="password"
                    placeholder="Enter your API secret"
                    value={twitterForm.api_secret}
                    onChange={(e) => setTwitterForm({...twitterForm, api_secret: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
                
                <div>
                  <Label htmlFor="twitter_bearer">Bearer Token</Label>
                  <Input
                    id="twitter_bearer"
                    type="password"
                    placeholder="Enter your bearer token"
                    value={twitterForm.bearer_token}
                    onChange={(e) => setTwitterForm({...twitterForm, bearer_token: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button variant="outline" onClick={() => setShowTwitterSetup(false)} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    if (!twitterForm.api_key || !twitterForm.api_secret) {
                      toast.error("Please fill in API key and secret");
                      return;
                    }
                    try {
                      await updateSettings({
                        twitter_api_key: twitterForm.api_key,
                        twitter_api_secret: twitterForm.api_secret,
                        twitter_bearer_token: twitterForm.bearer_token,
                        twitter_configured: true
                      });
                      setShowTwitterSetup(false);
                      toast.success("Twitter/X connected successfully!");
                    } catch (error) {
                      toast.error("Failed to save Twitter settings");
                    }
                  }}
                  className="flex-1 bg-gray-900 hover:bg-gray-800"
                >
                  Connect Twitter/X
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Email Setup Modal */}
        {showEmailSetup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-lg mx-4">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <Mail className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <CardTitle>Connect Email Notifications</CardTitle>
                    <CardDescription>Get notified when leads are qualified</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-purple-900 mb-2">How to get your Resend API key:</p>
                  <ol className="text-purple-800 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://resend.com" target="_blank" rel="noopener noreferrer" className="underline">resend.com</a> and create an account</li>
                    <li>Verify your domain (or use their test domain)</li>
                    <li>Go to API Keys → Create API Key</li>
                  </ol>
                </div>
                
                <div>
                  <Label htmlFor="resend_key">Resend API Key</Label>
                  <Input
                    id="resend_key"
                    type="password"
                    placeholder="re_xxxxxxxxxxxxxxxxxxxxxxxxx"
                    value={emailForm.resend_api_key}
                    onChange={(e) => setEmailForm({...emailForm, resend_api_key: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>
                
                <div>
                  <Label htmlFor="from_email">From Email Address</Label>
                  <Input
                    id="from_email"
                    type="email"
                    placeholder="notifications@yourdomain.com"
                    value={emailForm.from_email}
                    onChange={(e) => setEmailForm({...emailForm, from_email: e.target.value})}
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">Must be from a verified domain in Resend</p>
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button variant="outline" onClick={() => setShowEmailSetup(false)} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    if (!emailForm.resend_api_key) {
                      toast.error("Please enter your Resend API key");
                      return;
                    }
                    try {
                      await updateSettings({
                        resend_api_key: emailForm.resend_api_key,
                        from_email: emailForm.from_email,
                        email_notifications_configured: true
                      });
                      setShowEmailSetup(false);
                      toast.success("Email notifications connected!");
                    } catch (error) {
                      toast.error("Failed to save email settings");
                    }
                  }}
                  className="flex-1 bg-purple-600 hover:bg-purple-700"
                >
                  Connect Email
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Calendly Setup Modal */}
        {showCalendlySetup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-lg mx-4">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <CardTitle>Connect Calendly</CardTitle>
                    <CardDescription>Let AI book meetings on your calendar</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-green-900 mb-2">How to get your Calendly link:</p>
                  <ol className="text-green-800 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://calendly.com" target="_blank" rel="noopener noreferrer" className="underline">calendly.com</a></li>
                    <li>Create an event type (e.g., "15 Min Discovery Call")</li>
                    <li>Copy the scheduling link</li>
                  </ol>
                </div>
                
                <div>
                  <Label htmlFor="calendly_url">Calendly Scheduling Link</Label>
                  <Input
                    id="calendly_url"
                    placeholder="https://calendly.com/yourname/15min"
                    value={calendlyForm.calendly_url}
                    onChange={(e) => setCalendlyForm({...calendlyForm, calendly_url: e.target.value})}
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">The AI will direct qualified leads to book here</p>
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <p className="text-sm text-amber-800">
                    <strong>Tip:</strong> You can also set different Calendly links per agent in the agent settings.
                  </p>
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button variant="outline" onClick={() => setShowCalendlySetup(false)} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    if (!calendlyForm.calendly_url) {
                      toast.error("Please enter your Calendly link");
                      return;
                    }
                    try {
                      await updateSettings({
                        calendly_url: calendlyForm.calendly_url
                      });
                      setShowCalendlySetup(false);
                      toast.success("Calendly connected!");
                    } catch (error) {
                      toast.error("Failed to save Calendly settings");
                    }
                  }}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  Connect Calendly
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Apollo.io Setup Modal */}
        {showApolloSetup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                    <Database className="w-5 h-5 text-orange-600" />
                  </div>
                  <div>
                    <CardTitle>Connect Apollo.io</CardTitle>
                    <CardDescription>Enrich leads with owner/manager contact names</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Benefits */}
                <div className="bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-200 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-500" />
                    Why Connect Apollo?
                  </h4>
                  <ul className="text-sm text-orange-800 space-y-1">
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span><strong>Get contact names</strong> — Know who you're calling before dialing</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span><strong>Identify decision makers</strong> — Owner, Manager, CEO titles</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span><strong>Better personalization</strong> — "Hi John, this is Sarah..."</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span><strong>Higher conversion</strong> — 40% better response with names</span>
                    </li>
                  </ul>
                </div>

                {/* Pricing Info */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-blue-900 mb-2">Apollo.io Pricing:</p>
                  <ul className="text-blue-800 space-y-1">
                    <li>• <strong>Free tier:</strong> 100 credits/month (enough to test)</li>
                    <li>• <strong>Basic:</strong> $49/mo for 5,000 credits</li>
                    <li>• <strong>Professional:</strong> $99/mo for unlimited</li>
                  </ul>
                  <p className="mt-2 text-blue-700">1 credit = 1 lead enriched with contact info</p>
                </div>
                
                {/* Setup Instructions */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm">
                  <p className="font-medium text-gray-900 mb-2">How to get your Apollo API key:</p>
                  <ol className="text-gray-700 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://app.apollo.io" target="_blank" rel="noopener noreferrer" className="underline text-blue-600">app.apollo.io</a> (create free account)</li>
                    <li>Click Settings (gear icon) → Integrations</li>
                    <li>Find "API Keys" section → Create new key</li>
                    <li>Copy and paste the key below</li>
                  </ol>
                </div>
                
                <div>
                  <Label htmlFor="apollo_key">Apollo API Key</Label>
                  <Input
                    id="apollo_key"
                    type="password"
                    placeholder="Enter your Apollo API key"
                    value={apolloForm.api_key}
                    onChange={(e) => setApolloForm({...apolloForm, api_key: e.target.value})}
                    className="mt-1 font-mono text-sm"
                  />
                </div>

                {/* What Happens Next */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <p className="text-sm text-green-800">
                    <strong>Once connected:</strong> When you discover or import leads, we'll automatically fetch contact names and titles. Your AI will then personalize calls: "Hi [Name], am I speaking with the owner?"
                  </p>
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button variant="outline" onClick={() => setShowApolloSetup(false)} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    if (!apolloForm.api_key || apolloForm.api_key === "••••••••") {
                      toast.error("Please enter your Apollo API key");
                      return;
                    }
                    try {
                      await updateSettings({
                        apollo_api_key: apolloForm.api_key,
                        apollo_configured: true
                      });
                      setShowApolloSetup(false);
                      toast.success("Apollo.io connected! Leads will now be enriched with contact names.");
                    } catch (error) {
                      toast.error("Failed to save Apollo settings");
                    }
                  }}
                  className="flex-1 bg-orange-600 hover:bg-orange-700"
                >
                  Connect Apollo
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Number Pool / Caller ID Rotation Card */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }} className="flex items-center gap-2">
                  <RefreshCw className="w-5 h-5 text-blue-600" />
                  Caller ID Rotation
                </CardTitle>
                <CardDescription>Rotate through multiple numbers for higher answer rates</CardDescription>
              </div>
              <Badge variant={numberPoolEnabled && numberPool.length >= 2 ? "default" : "secondary"}>
                {numberPoolEnabled && numberPool.length >= 2 ? `${numberPool.length} Numbers Active` : "Not Active"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Benefits Section */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-4">
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                Why Use Number Rotation?
              </h4>
              <div className="grid md:grid-cols-2 gap-3 text-sm">
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span><strong>+30-40% answer rates</strong> with local presence</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span><strong>Avoid spam flags</strong> by spreading calls</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span><strong>Professional appearance</strong> like a real team</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span><strong>No easy callbacks</strong> — numbers rotate</span>
                </div>
              </div>
            </div>

            {/* Setup Instructions */}
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <h4 className="font-semibold text-gray-900 mb-3">How to Set Up:</h4>
              <ol className="space-y-2 text-sm text-gray-700">
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">1</span>
                  <span><strong>Buy Twilio numbers</strong> — Go to <a href="https://console.twilio.com/us1/develop/phone-numbers/manage/incoming" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Twilio Console</a> → Phone Numbers → Buy a Number (~$1-2/month each)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">2</span>
                  <span><strong>Add 5-10 numbers</strong> — Mix of local area codes matching your target regions</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">3</span>
                  <span><strong>Paste numbers below</strong> — Format: +1XXXXXXXXXX (include country code)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">4</span>
                  <span><strong>Choose rotation mode</strong> — Round-robin (sequential), Random, or Geographic</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">5</span>
                  <span><strong>Enable rotation</strong> — Toggle on and your campaigns will auto-rotate</span>
                </li>
              </ol>
            </div>

            {/* Enable Toggle */}
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-white">
              <div>
                <p className="font-medium">Enable Number Rotation</p>
                <p className="text-sm text-gray-500">Requires at least 2 numbers in pool</p>
              </div>
              <Button
                variant={numberPoolEnabled ? "default" : "outline"}
                onClick={() => {
                  if (numberPool.length < 2 && !numberPoolEnabled) {
                    toast.error("Add at least 2 numbers to enable rotation");
                    return;
                  }
                  const newValue = !numberPoolEnabled;
                  setNumberPoolEnabled(newValue);
                  updateSettings({ number_pool_enabled: newValue });
                }}
                disabled={numberPool.length < 2}
              >
                {numberPoolEnabled ? "Enabled" : "Disabled"}
              </Button>
            </div>

            {/* Rotation Mode Selector */}
            <div>
              <Label className="mb-2 block">Rotation Mode</Label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: "round-robin", label: "Round Robin", desc: "Sequential order" },
                  { value: "random", label: "Random", desc: "Randomized each call" },
                  { value: "geographic", label: "Geographic", desc: "Match lead area code" }
                ].map((mode) => (
                  <button
                    key={mode.value}
                    onClick={() => {
                      setRotationMode(mode.value);
                      updateSettings({ rotation_mode: mode.value });
                    }}
                    className={`p-3 rounded-lg border-2 text-center transition-all ${
                      rotationMode === mode.value
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:border-blue-300"
                    }`}
                  >
                    <p className={`font-medium text-sm ${rotationMode === mode.value ? "text-blue-700" : "text-gray-700"}`}>
                      {mode.label}
                    </p>
                    <p className="text-xs text-gray-500">{mode.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Number Pool List */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label>Your Number Pool ({numberPool.length} numbers)</Label>
                <Button
                  size="sm"
                  onClick={() => setShowAddNumber(true)}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Number
                </Button>
              </div>

              {numberPool.length === 0 ? (
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Phone className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 mb-2">No numbers in pool yet</p>
                  <p className="text-sm text-gray-400">Add Twilio numbers to start rotating caller IDs</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {numberPool.map((number, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-700">{index + 1}</span>
                        </div>
                        <div>
                          <p className="font-mono font-medium text-gray-900">{number}</p>
                          <p className="text-xs text-gray-500">
                            Area code: {number.slice(2, 5)}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const updated = numberPool.filter((_, i) => i !== index);
                          setNumberPool(updated);
                          updateSettings({ number_pool: updated });
                          toast.success("Number removed");
                        }}
                        className="text-red-500 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Add Number Modal */}
            {showAddNumber && (
              <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <Card className="w-full max-w-md mx-4">
                  <CardHeader>
                    <CardTitle>Add Twilio Number</CardTitle>
                    <CardDescription>Enter a phone number from your Twilio account</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="newNumber">Phone Number</Label>
                      <Input
                        id="newNumber"
                        placeholder="+14155551234"
                        value={newNumber}
                        onChange={(e) => setNewNumber(e.target.value)}
                        className="mt-1 font-mono"
                      />
                      <p className="text-xs text-gray-500 mt-1">Format: +1XXXXXXXXXX (include country code)</p>
                    </div>
                    
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                      <p className="text-sm text-amber-800">
                        <strong>Important:</strong> This number must be purchased in your Twilio account and configured for voice calls.
                      </p>
                    </div>
                  </CardContent>
                  <div className="flex gap-2 p-6 pt-0">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowAddNumber(false);
                        setNewNumber("");
                      }}
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={() => {
                        // Validate phone number format
                        const phoneRegex = /^\+1[0-9]{10}$/;
                        if (!phoneRegex.test(newNumber)) {
                          toast.error("Invalid format. Use +1XXXXXXXXXX");
                          return;
                        }
                        if (numberPool.includes(newNumber)) {
                          toast.error("This number is already in your pool");
                          return;
                        }
                        const updated = [...numberPool, newNumber];
                        setNumberPool(updated);
                        updateSettings({ number_pool: updated });
                        setShowAddNumber(false);
                        setNewNumber("");
                        toast.success("Number added to pool!");
                      }}
                      className="flex-1 bg-blue-600 hover:bg-blue-700"
                    >
                      Add Number
                    </Button>
                  </div>
                </Card>
              </div>
            )}

            {/* Pricing Note */}
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4">
              <h4 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
                <CreditCard className="w-4 h-4" />
                Cost Breakdown
              </h4>
              <div className="text-sm text-green-800 space-y-1">
                <p><strong>Twilio numbers:</strong> ~$1-2/month per number (paid to Twilio)</p>
                <p><strong>Rotation feature:</strong> Included with Professional+ plans, or $39/month add-on</p>
                <p className="text-green-600 mt-2">💡 Tip: Start with 5-10 numbers for optimal rotation</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Team Management Card */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }} className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-indigo-600" />
                  Team Management
                </CardTitle>
                <CardDescription>Invite team members and manage access</CardDescription>
              </div>
              <Badge variant={teamMembers.length > 0 ? "default" : "secondary"}>
                {teamMembers.length + 1} {teamMembers.length === 0 ? "User" : "Users"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Plan Info */}
            <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
              <h4 className="font-semibold text-indigo-900 mb-2 flex items-center gap-2">
                <Zap className="w-4 h-4 text-indigo-600" />
                Team Seats by Plan
              </h4>
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div className="bg-white rounded-lg p-3 text-center border border-indigo-100">
                  <p className="font-medium text-gray-900">Starter</p>
                  <p className="text-2xl font-bold text-indigo-600">1</p>
                  <p className="text-xs text-gray-500">seat</p>
                </div>
                <div className="bg-white rounded-lg p-3 text-center border border-indigo-100">
                  <p className="font-medium text-gray-900">Professional</p>
                  <p className="text-2xl font-bold text-indigo-600">5</p>
                  <p className="text-xs text-gray-500">seats</p>
                </div>
                <div className="bg-white rounded-lg p-3 text-center border border-indigo-100">
                  <p className="font-medium text-gray-900">Unlimited</p>
                  <p className="text-2xl font-bold text-indigo-600">5</p>
                  <p className="text-xs text-gray-500">seats</p>
                </div>
              </div>
            </div>

            {/* Current User (Owner) */}
            <div>
              <Label className="mb-3 block">Account Owner</Label>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center text-white font-semibold">
                    {settings?.email?.charAt(0)?.toUpperCase() || "U"}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{settings?.email || "Loading..."}</p>
                    <p className="text-sm text-gray-500">Account Owner</p>
                  </div>
                </div>
                <Badge className="bg-indigo-600">Owner</Badge>
              </div>
            </div>

            {/* Team Members List */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label>Team Members ({teamMembers.length})</Label>
                <Button
                  size="sm"
                  onClick={() => setShowInviteModal(true)}
                  className="bg-indigo-600 hover:bg-indigo-700"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Invite Member
                </Button>
              </div>

              {loadingTeam ? (
                <div className="text-center py-8 text-gray-500">Loading team...</div>
              ) : teamMembers.length === 0 ? (
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Users className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 mb-2">No team members yet</p>
                  <p className="text-sm text-gray-400">Invite colleagues to collaborate on campaigns</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {teamMembers.map((member) => (
                    <div key={member.id} className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 hover:border-indigo-200 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-semibold">
                          {member.email?.charAt(0)?.toUpperCase() || "?"}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{member.email}</p>
                          <p className="text-sm text-gray-500">
                            {member.status === "pending" ? "Invitation pending" : `Joined ${new Date(member.joined_at).toLocaleDateString()}`}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <select
                          value={member.role}
                          onChange={(e) => updateMemberRole(member.id, e.target.value)}
                          className="text-sm border border-gray-300 rounded-md px-2 py-1"
                        >
                          <option value="member">Member</option>
                          <option value="admin">Admin</option>
                        </select>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeTeamMember(member.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Role Permissions Info */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-3">Role Permissions</h4>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-medium text-gray-700 mb-2">👤 Member</p>
                  <ul className="text-gray-600 space-y-1">
                    <li>• View all campaigns & leads</li>
                    <li>• Create & edit agents</li>
                    <li>• Make calls</li>
                    <li>• View call recordings</li>
                  </ul>
                </div>
                <div>
                  <p className="font-medium text-gray-700 mb-2">👑 Admin</p>
                  <ul className="text-gray-600 space-y-1">
                    <li>• All Member permissions</li>
                    <li>• Manage team members</li>
                    <li>• View billing & usage</li>
                    <li>• Change settings</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Invite Team Member Modal */}
        {showInviteModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md mx-4">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <Mail className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <CardTitle>Invite Team Member</CardTitle>
                    <CardDescription>Send an invitation to join your team</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="invite-email">Email Address</Label>
                  <Input
                    id="invite-email"
                    type="email"
                    placeholder="colleague@company.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="mt-1"
                  />
                </div>
                
                <div>
                  <Label htmlFor="invite-role">Role</Label>
                  <select
                    id="invite-role"
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="member">Member — Can use platform, view data</option>
                    <option value="admin">Admin — Can manage team & settings</option>
                  </select>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> They'll receive an email invitation to create an account and join your team.
                  </p>
                </div>
              </CardContent>
              <div className="flex gap-2 p-6 pt-0">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowInviteModal(false);
                    setInviteEmail("");
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={inviteTeamMember}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700"
                >
                  Send Invitation
                </Button>
              </div>
            </Card>
          </div>
        )}

        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Qualification Criteria
            </CardTitle>
            <CardDescription>Set thresholds for lead qualification</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="threshold">Qualification Threshold (Score)</Label>
              <Input
                id="threshold"
                data-testid="qual-threshold-input"
                type="number"
                value={settings?.qualification_threshold || 60}
                onChange={(e) => updateSettings({ qualification_threshold: parseInt(e.target.value) })}
                className="mt-1"
              />
              <p className="text-xs text-gray-500 mt-1">Leads must score above this to be qualified</p>
            </div>
            
            <div>
              <Label htmlFor="interest">Minimum Interest Level (1-10)</Label>
              <Input
                id="interest"
                data-testid="min-interest-input"
                type="number"
                min="1"
                max="10"
                value={settings?.min_interest_level || 6}
                onChange={(e) => updateSettings({ min_interest_level: parseInt(e.target.value) })}
                className="mt-1"
              />
            </div>
            
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div>
                <p className="font-medium">Require Decision Maker</p>
                <p className="text-sm text-gray-500">Only qualify if speaking with owner/manager</p>
              </div>
              <Button
                variant={settings?.require_decision_maker ? "default" : "outline"}
                data-testid="require-dm-toggle"
                onClick={() => updateSettings({ require_decision_maker: !settings?.require_decision_maker })}
              >
                {settings?.require_decision_maker ? "Required" : "Optional"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Low Balance Alerts Card */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Low Balance Alerts
            </CardTitle>
            <CardDescription>Get notified when your credits are running low</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div>
                <p className="font-medium">Enable Low Balance Alerts</p>
                <p className="text-sm text-gray-500">Receive email when credits drop below threshold</p>
              </div>
              <Button
                variant={settings?.low_balance_alerts_enabled ? "default" : "outline"}
                data-testid="low-balance-toggle"
                onClick={() => updateSettings({ low_balance_alerts_enabled: !settings?.low_balance_alerts_enabled })}
              >
                {settings?.low_balance_alerts_enabled ? "Enabled" : "Disabled"}
              </Button>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="lead-threshold">Lead Credit Threshold</Label>
                <Input
                  id="lead-threshold"
                  type="number"
                  min="0"
                  value={settings?.low_lead_threshold || 20}
                  onChange={(e) => updateSettings({ low_lead_threshold: parseInt(e.target.value) || 20 })}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">Alert when leads drop below this</p>
              </div>
              <div>
                <Label htmlFor="call-threshold">Call Credit Threshold</Label>
                <Input
                  id="call-threshold"
                  type="number"
                  min="0"
                  value={settings?.low_call_threshold || 20}
                  onChange={(e) => updateSettings({ low_call_threshold: parseInt(e.target.value) || 20 })}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">Alert when calls drop below this</p>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800">
                <strong>💡 Tip:</strong> Set thresholds high enough to give you time to purchase more credits before running out.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Agency White-labeling Card */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Agency White-labeling
            </CardTitle>
            <CardDescription>Customize branding for your clients</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div>
                <p className="font-medium">Hide DialGenix Branding</p>
                <p className="text-sm text-gray-500">Remove DialGenix logo and mentions from the dashboard</p>
              </div>
              <Button
                variant={settings?.whitelabel_enabled ? "default" : "outline"}
                data-testid="whitelabel-toggle"
                onClick={() => updateSettings({ whitelabel_enabled: !settings?.whitelabel_enabled })}
              >
                {settings?.whitelabel_enabled ? "Hidden" : "Visible"}
              </Button>
            </div>

            {settings?.whitelabel_enabled && (
              <>
                <div>
                  <Label htmlFor="custom-brand">Custom Brand Name</Label>
                  <Input
                    id="custom-brand"
                    placeholder="Your Agency Name"
                    value={settings?.custom_brand_name || ""}
                    onChange={(e) => updateSettings({ custom_brand_name: e.target.value })}
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">Replaces "DialGenix" throughout the app</p>
                </div>

                <div>
                  <Label htmlFor="custom-logo">Custom Logo URL</Label>
                  <Input
                    id="custom-logo"
                    placeholder="https://yoursite.com/logo.png"
                    value={settings?.custom_logo_url || ""}
                    onChange={(e) => updateSettings({ custom_logo_url: e.target.value })}
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">Square image, 200x200px recommended (PNG or SVG)</p>
                </div>

                <div>
                  <Label htmlFor="custom-color">Primary Brand Color</Label>
                  <div className="flex gap-2 mt-1">
                    <input
                      type="color"
                      id="custom-color"
                      value={settings?.custom_brand_color || "#3b82f6"}
                      onChange={(e) => updateSettings({ custom_brand_color: e.target.value })}
                      className="w-12 h-10 rounded cursor-pointer border border-gray-300"
                    />
                    <Input
                      value={settings?.custom_brand_color || "#3b82f6"}
                      onChange={(e) => updateSettings({ custom_brand_color: e.target.value })}
                      placeholder="#3b82f6"
                      className="font-mono"
                    />
                  </div>
                </div>
              </>
            )}

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
              <p className="text-sm text-purple-800">
                <strong>🏢 Agency Feature:</strong> Perfect for reselling DialGenix to your clients under your own brand.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
      <Card className="bg-white border border-gray-200 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Email Notifications
            </CardTitle>
            <CardDescription>Get notified when leads qualify or meetings are booked</CardDescription>
          </div>
          <Button 
            data-testid="create-webhook-btn"
            onClick={() => setShowCreateWebhook(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Notification
          </Button>
        </CardHeader>
        <CardContent>
          {!settings?.email_notifications_configured && (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg mb-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
                <div>
                  <p className="font-medium text-amber-800">Email notifications not configured</p>
                  <p className="text-sm text-amber-700 mt-1">
                    Add your <code className="bg-amber-100 px-1 rounded">RESEND_API_KEY</code> to the backend .env file to enable email notifications.
                    Get your API key at <a href="https://resend.com" target="_blank" rel="noopener noreferrer" className="underline">resend.com</a>
                  </p>
                </div>
              </div>
            </div>
          )}

          {webhooks.length === 0 ? (
            <div className="text-center py-8">
              <Mail className="w-12 h-12 text-gray-300 mx-auto" />
              <p className="text-gray-500 mt-3">No email notifications configured</p>
              <p className="text-sm text-gray-400">Add a notification to get alerts when leads qualify or meetings are booked</p>
            </div>
          ) : (
            <div className="space-y-3">
              {webhooks.map(webhook => (
                <div 
                  key={webhook.id} 
                  data-testid={`webhook-${webhook.id}`}
                  className={`p-4 border rounded-lg ${webhook.is_active ? 'border-gray-200 bg-white' : 'border-gray-100 bg-gray-50 opacity-60'}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900">{webhook.name}</h4>
                        <Badge variant={webhook.is_active ? "default" : "secondary"}>
                          {webhook.is_active ? "Active" : "Disabled"}
                        </Badge>
                        <Badge variant="outline" className="capitalize">
                          {webhook.event_type.replace('_', ' ')}
                        </Badge>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {webhook.notification_emails.map((email, idx) => (
                          <span key={idx} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700">
                            <Mail className="w-3 h-3 mr-1" />
                            {email}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        data-testid={`test-webhook-${webhook.id}`}
                        onClick={() => testWebhook(webhook)}
                        disabled={testingWebhook === webhook.id || !settings?.email_notifications_configured}
                      >
                        {testingWebhook === webhook.id ? "Sending..." : "Test"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        data-testid={`toggle-webhook-${webhook.id}`}
                        onClick={() => toggleWebhook(webhook)}
                      >
                        {webhook.is_active ? "Disable" : "Enable"}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        data-testid={`delete-webhook-${webhook.id}`}
                        onClick={() => deleteWebhook(webhook.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Webhook Dialog */}
      <Dialog open={showCreateWebhook} onOpenChange={setShowCreateWebhook}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Add Email Notification
            </DialogTitle>
            <DialogDescription>
              Configure email alerts for lead qualification or meeting booking events
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="webhook-name">Notification Name *</Label>
              <Input
                id="webhook-name"
                data-testid="webhook-name-input"
                value={newWebhook.name}
                onChange={(e) => setNewWebhook({...newWebhook, name: e.target.value})}
                placeholder="e.g., Sales Team Alert"
                className="mt-1"
              />
            </div>
            
            <div>
              <Label>Event Type *</Label>
              <Select 
                value={newWebhook.event_type} 
                onValueChange={(v) => setNewWebhook({...newWebhook, event_type: v})}
              >
                <SelectTrigger data-testid="webhook-event-select" className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="lead_qualified">Lead Qualified</SelectItem>
                  <SelectItem value="meeting_booked">Meeting Booked</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500 mt-1">
                {newWebhook.event_type === 'lead_qualified' 
                  ? 'Triggers when a lead passes qualification criteria after a call'
                  : 'Triggers when a qualified lead is assigned to an agent for booking'}
              </p>
            </div>
            
            <div>
              <Label htmlFor="webhook-emails">Notification Emails *</Label>
              <Textarea
                id="webhook-emails"
                data-testid="webhook-emails-input"
                value={newWebhook.notification_emails}
                onChange={(e) => setNewWebhook({...newWebhook, notification_emails: e.target.value})}
                placeholder="email1@example.com, email2@example.com"
                className="mt-1"
                rows={2}
              />
              <p className="text-xs text-gray-500 mt-1">Separate multiple emails with commas</p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateWebhook(false)}>Cancel</Button>
            <Button 
              data-testid="save-webhook-btn"
              onClick={createWebhook}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Create Notification
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Credit Packs Page

export default SettingsPage;
