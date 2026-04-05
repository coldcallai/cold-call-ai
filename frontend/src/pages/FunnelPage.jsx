import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Plus, Phone, Calendar, CheckCircle, Zap, PhoneCall,
  UserCheck, CalendarCheck, ArrowRight, RefreshCw
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Booking Dialog Component
const BookingDialog = ({ lead, onClose, onSuccess }) => {
  const { token } = useAuth();
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [notes, setNotes] = useState("");
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    if (lead) {
      fetchAgents();
    }
  }, [lead]);

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API}/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAgents(response.data.filter(a => a.is_active));
    } catch (error) {
      console.error("Failed to fetch agents:", error);
    }
  };

  const bookMeeting = async () => {
    if (!selectedAgent) {
      toast.error("Please select an agent");
      return;
    }

    setBooking(true);
    try {
      const response = await axios.post(`${API}/bookings`, {
        lead_id: lead.id,
        agent_id: selectedAgent,
        notes: notes || null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(
        <div>
          <p className="font-medium">Meeting booked successfully!</p>
          <p className="text-sm text-gray-600 mt-1">Opening personalized Calendly link...</p>
        </div>
      );
      
      window.open(response.data.booking_link, '_blank');
      onSuccess();
    } catch (error) {
      const detail = error.response?.data?.detail || "Failed to book meeting";
      if (error.response?.status === 403) {
        toast.error("Calendar booking requires Professional plan or higher");
      } else {
        toast.error(detail);
      }
    } finally {
      setBooking(false);
    }
  };

  if (!lead) return null;

  const selectedAgentData = agents.find(a => a.id === selectedAgent);

  return (
    <Dialog open={!!lead} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Book Meeting for {lead.business_name}
          </DialogTitle>
          <DialogDescription>
            Select an agent to assign this qualified lead.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div>
            <Label>Select Agent</Label>
            <Select value={selectedAgent} onValueChange={setSelectedAgent}>
              <SelectTrigger data-testid="agent-select-booking" className="mt-1">
                <SelectValue placeholder="Choose an agent" />
              </SelectTrigger>
              <SelectContent>
                {agents.length === 0 ? (
                  <div className="p-2 text-sm text-gray-500 text-center">
                    No agents available. Create an agent first.
                  </div>
                ) : (
                  agents.map(agent => (
                    <SelectItem key={agent.id} value={agent.id}>
                      <div className="flex items-center gap-2">
                        <span>{agent.name}</span>
                        <span className="text-gray-500 text-xs">
                          ({agent.booked_meetings || 0} meetings)
                        </span>
                      </div>
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label>Notes (optional)</Label>
            <Input
              placeholder="Add notes about this lead..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1"
            />
          </div>
          
          {selectedAgentData && (
            <div className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-100">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Calendar className="w-4 h-4 text-purple-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">Personalized Calendly Link</p>
                  <ul className="text-xs text-gray-500 mt-1 space-y-0.5">
                    {lead.contact_name && <li>• Name: {lead.contact_name}</li>}
                    {lead.email && <li>• Email: {lead.email}</li>}
                    {lead.phone && <li>• Phone: {lead.phone}</li>}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button 
            data-testid="confirm-booking-btn"
            onClick={bookMeeting}
            disabled={booking || !selectedAgent}
            className="bg-purple-600 hover:bg-purple-700 text-white gap-2"
          >
            {booking ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Booking...
              </>
            ) : (
              <>
                <Calendar className="w-4 h-4" />
                Book Meeting
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Main Funnel Page Component
const FunnelPage = () => {
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedLead, setSelectedLead] = useState(null);
  const [selectedCampaign, setSelectedCampaign] = useState("");
  const [setupStatus, setSetupStatus] = useState(null);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const token = localStorage.getItem('session_token');
      const [leadsRes, statsRes, agentsRes, campaignsRes, setupRes] = await Promise.all([
        axios.get(`${API}/leads`),
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/agents`),
        axios.get(`${API}/campaigns`),
        axios.get(`${API}/setup/status`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: { can_make_calls: true } }))
      ]);
      setLeads(leadsRes.data);
      setStats(statsRes.data);
      setAgents(agentsRes.data.filter(a => a.is_active));
      setCampaigns(campaignsRes.data.filter(c => c.status === 'active'));
      setSetupStatus(setupRes.data);
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast.error("Failed to load funnel data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const simulateCall = async (leadId) => {
    if (setupStatus && !setupStatus.can_make_calls) {
      toast.error("Complete your setup first to make calls", {
        description: "Go to Getting Started to finish setup",
        action: {
          label: "Go to Setup",
          onClick: () => navigate("/app/getting-started")
        }
      });
      return;
    }
    
    if (!selectedCampaign) {
      toast.error("Please select a campaign first");
      return;
    }
    try {
      await axios.post(`${API}/calls/simulate?lead_id=${leadId}&campaign_id=${selectedCampaign}`);
      toast.success("Call started!");
      setTimeout(fetchData, 3000);
    } catch (error) {
      if (error.response?.status === 402) {
        toast.error("You've run out of call credits", {
          description: "Upgrade your plan to continue making calls",
          action: {
            label: "Upgrade",
            onClick: () => navigate("/app/packs")
          }
        });
      } else {
        toast.error("Failed to start call");
      }
    }
  };

  // Group leads by status
  const newLeads = leads.filter(l => l.status === 'new');
  const contactedLeads = leads.filter(l => l.status === 'contacted');
  const qualifiedLeads = leads.filter(l => l.status === 'qualified');
  const bookedLeads = leads.filter(l => l.status === 'booked');
  const notQualifiedLeads = leads.filter(l => l.status === 'not_qualified');

  const funnelStages = [
    { id: 'new', title: 'New Leads', leads: newLeads, icon: Zap, color: 'bg-blue-500', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-700' },
    { id: 'contacted', title: 'Contacted', leads: contactedLeads, icon: PhoneCall, color: 'bg-amber-500', bgColor: 'bg-amber-50', borderColor: 'border-amber-200', textColor: 'text-amber-700' },
    { id: 'qualified', title: 'Qualified', leads: qualifiedLeads, icon: UserCheck, color: 'bg-emerald-500', bgColor: 'bg-emerald-50', borderColor: 'border-emerald-200', textColor: 'text-emerald-700' },
    { id: 'booked', title: 'Booked', leads: bookedLeads, icon: CalendarCheck, color: 'bg-purple-500', bgColor: 'bg-purple-50', borderColor: 'border-purple-200', textColor: 'text-purple-700' },
  ];

  if (loading) {
    return (
      <div className="p-6 md:p-8 space-y-6" data-testid="funnel-loading">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-96" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="funnel-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Sales Funnel
          </h1>
          <p className="text-gray-500 mt-1">Track leads through your qualification pipeline</p>
          <p className="text-xs text-blue-600 mt-1 bg-blue-50 px-2 py-1 rounded inline-block">
            💡 Drag leads between stages or click to call. Select a campaign first to start calling.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={selectedCampaign} onValueChange={setSelectedCampaign}>
            <SelectTrigger data-testid="funnel-campaign-select" className="w-[200px]">
              <SelectValue placeholder="Select campaign" />
            </SelectTrigger>
            <SelectContent>
              {campaigns.map(c => (
                <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button 
            data-testid="funnel-discover-btn"
            className="bg-blue-600 hover:bg-blue-700 text-white"
            onClick={() => window.location.href = '/app/leads'}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Leads
          </Button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Total Leads</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{leads.length}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Qualification Rate</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{stats?.qualification_rate || 0}%</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Booking Rate</p>
          <p className="text-2xl font-bold text-purple-600 mt-1">{stats?.booking_rate || 0}%</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Total Calls</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{stats?.total_calls || 0}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Not Qualified</p>
          <p className="text-2xl font-bold text-red-500 mt-1">{notQualifiedLeads.length}</p>
        </div>
      </div>

      {/* Funnel Flow Visual */}
      <div className="flex items-center justify-center gap-2 py-4">
        {funnelStages.map((stage, idx) => (
          <div key={stage.id} className="flex items-center">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${stage.bgColor} ${stage.borderColor} border`}>
              <stage.icon className={`w-4 h-4 ${stage.textColor}`} />
              <span className={`font-semibold ${stage.textColor}`}>{stage.leads.length}</span>
            </div>
            {idx < funnelStages.length - 1 && (
              <ArrowRight className="w-5 h-5 text-gray-300 mx-2" />
            )}
          </div>
        ))}
      </div>

      {/* Kanban-style Columns */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {funnelStages.map((stage) => {
          const Icon = stage.icon;
          return (
            <div key={stage.id} className="flex flex-col" data-testid={`funnel-stage-${stage.id}`}>
              <div className={`${stage.bgColor} ${stage.borderColor} border rounded-t-xl p-4`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-lg ${stage.color} flex items-center justify-center`}>
                      <Icon className="w-4 h-4 text-white" />
                    </div>
                    <h3 className={`font-semibold ${stage.textColor}`} style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                      {stage.title}
                    </h3>
                  </div>
                  <span className={`text-xl font-bold ${stage.textColor}`}>{stage.leads.length}</span>
                </div>
              </div>

              <div className="flex-1 bg-white border border-t-0 border-gray-200 rounded-b-xl">
                <ScrollArea className="h-[400px]">
                  {stage.leads.length === 0 ? (
                    <div className="p-6 text-center">
                      <div className={`w-12 h-12 rounded-full ${stage.bgColor} flex items-center justify-center mx-auto`}>
                        <Icon className={`w-6 h-6 ${stage.textColor} opacity-50`} />
                      </div>
                      <p className="text-sm text-gray-400 mt-3">No leads</p>
                    </div>
                  ) : (
                    <div className="p-3 space-y-2">
                      {stage.leads.map((lead) => (
                        <div 
                          key={lead.id}
                          data-testid={`funnel-lead-${lead.id}`}
                          className="bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg p-3 transition-colors cursor-pointer"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-gray-900 text-sm truncate">{lead.business_name}</p>
                              <p className="text-xs text-gray-500 mt-0.5">{lead.phone}</p>
                              {lead.qualification_score !== null && (
                                <div className="flex items-center gap-2 mt-2">
                                  <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                    <div 
                                      className={`h-full ${lead.qualification_score >= 60 ? 'bg-emerald-500' : 'bg-gray-400'}`}
                                      style={{ width: `${lead.qualification_score}%` }}
                                    />
                                  </div>
                                  <span className="text-xs font-medium text-gray-600">{lead.qualification_score}</span>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          <div className="mt-3 flex gap-2">
                            {stage.id === 'new' && (
                              <Button 
                                size="sm" 
                                className="flex-1 h-7 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                                onClick={() => simulateCall(lead.id)}
                                disabled={!selectedCampaign}
                              >
                                <Phone className="w-3 h-3 mr-1" />
                                Call
                              </Button>
                            )}
                            {stage.id === 'qualified' && (
                              <Button 
                                size="sm" 
                                className="flex-1 h-7 text-xs bg-purple-600 hover:bg-purple-700 text-white"
                                onClick={() => setSelectedLead(lead)}
                              >
                                <Calendar className="w-3 h-3 mr-1" />
                                Book
                              </Button>
                            )}
                            {stage.id === 'booked' && (
                              <div className="flex items-center gap-1 text-xs text-purple-600">
                                <CheckCircle className="w-3 h-3" />
                                <span>Meeting scheduled</span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </div>
            </div>
          );
        })}
      </div>

      <BookingDialog 
        lead={selectedLead} 
        onClose={() => setSelectedLead(null)}
        onSuccess={() => {
          setSelectedLead(null);
          fetchData();
        }}
      />
    </div>
  );
};

export default FunnelPage;
