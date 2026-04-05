import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Calendar, RefreshCw } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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
            Select an agent to assign this qualified lead. A personalized booking link will be generated with the lead's info pre-filled.
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
                  <p className="text-sm font-medium text-gray-900">
                    Personalized Calendly Link
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    The booking link will include:
                  </p>
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

export default BookingDialog;
