import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { 
  Star, Send, MessageSquare, Plus, Trash2, Upload,
  CheckCircle, Clock, AlertCircle, Loader2
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ReviewRequestsPage = () => {
  const [googleReviewUrl, setGoogleReviewUrl] = useState("");
  const [customMessage, setCustomMessage] = useState("");
  const [patients, setPatients] = useState([{ name: "", phone: "" }]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_URL}/api/reviews/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setHistory(data.requests || []);
      }
    } catch (error) {
      console.error("Failed to fetch history:", error);
    }
    setLoading(false);
  };

  const addPatient = () => {
    setPatients([...patients, { name: "", phone: "" }]);
  };

  const removePatient = (index) => {
    if (patients.length > 1) {
      setPatients(patients.filter((_, i) => i !== index));
    }
  };

  const updatePatient = (index, field, value) => {
    const updated = [...patients];
    updated[index][field] = value;
    setPatients(updated);
  };

  const sendRequests = async () => {
    if (!googleReviewUrl) {
      alert("Please enter your Google Review URL");
      return;
    }

    const validPatients = patients.filter(p => p.phone && p.name);
    if (validPatients.length === 0) {
      alert("Please add at least one patient with name and phone");
      return;
    }

    setSending(true);
    setSuccessMessage("");

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_URL}/api/reviews/send-bulk`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          patients: validPatients,
          google_review_url: googleReviewUrl,
          custom_message: customMessage || null
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSuccessMessage(`✅ Sent ${data.sent} review request(s)!`);
        setPatients([{ name: "", phone: "" }]);
        fetchHistory();
      } else {
        const error = await response.json();
        alert(`Failed: ${error.detail}`);
      }
    } catch (error) {
      console.error("Failed to send:", error);
      alert("Failed to send review requests");
    }

    setSending(false);
  };

  return (
    <div className="p-6 space-y-6" data-testid="review-requests-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Star className="w-6 h-6 text-yellow-400" />
            Review Requests
          </h1>
          <p className="text-gray-400 mt-1">Send SMS review requests to patients after their visit</p>
        </div>
      </div>

      {/* Setup Section */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Setup</h2>
        
        <div className="space-y-4">
          <div>
            <Label htmlFor="google-url" className="text-gray-300">Google Review URL *</Label>
            <Input
              id="google-url"
              value={googleReviewUrl}
              onChange={(e) => setGoogleReviewUrl(e.target.value)}
              placeholder="https://g.page/r/your-business-id/review"
              className="mt-1 bg-white/10 border-white/20 text-white"
            />
            <p className="text-xs text-gray-500 mt-1">
              Find this in Google Business Profile → Share → "Get more reviews" link
            </p>
          </div>

          <div>
            <Label htmlFor="custom-message" className="text-gray-300">Custom Message (Optional)</Label>
            <Textarea
              id="custom-message"
              value={customMessage}
              onChange={(e) => setCustomMessage(e.target.value)}
              placeholder="Hi {name}! Thank you for visiting us today. We'd love to hear about your experience..."
              className="mt-1 bg-white/10 border-white/20 text-white min-h-[80px]"
            />
            <p className="text-xs text-gray-500 mt-1">
              Leave blank for default message. The review URL will be added automatically.
            </p>
          </div>
        </div>
      </div>

      {/* Patients Section */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Patients</h2>
          <Button 
            onClick={addPatient} 
            variant="outline" 
            size="sm"
            className="border-purple-500/50 text-purple-400 hover:bg-purple-500/10"
          >
            <Plus className="w-4 h-4 mr-1" />
            Add Patient
          </Button>
        </div>

        <div className="space-y-3">
          {patients.map((patient, index) => (
            <div key={index} className="flex items-center gap-3">
              <Input
                value={patient.name}
                onChange={(e) => updatePatient(index, "name", e.target.value)}
                placeholder="Patient Name"
                className="bg-white/10 border-white/20 text-white flex-1"
              />
              <Input
                value={patient.phone}
                onChange={(e) => updatePatient(index, "phone", e.target.value)}
                placeholder="+1 555-123-4567"
                className="bg-white/10 border-white/20 text-white flex-1"
              />
              {patients.length > 1 && (
                <Button
                  onClick={() => removePatient(index)}
                  variant="ghost"
                  size="icon"
                  className="text-red-400 hover:bg-red-500/10"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              )}
            </div>
          ))}
        </div>

        {successMessage && (
          <div className="mt-4 p-3 bg-emerald-500/20 border border-emerald-500/30 rounded-lg text-emerald-400 text-sm">
            {successMessage}
          </div>
        )}

        <div className="mt-6">
          <Button
            onClick={sendRequests}
            disabled={sending}
            className="w-full bg-gradient-to-r from-purple-500 to-cyan-500 hover:from-purple-600 hover:to-cyan-600"
          >
            {sending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Send Review Requests
              </>
            )}
          </Button>
        </div>
      </div>

      {/* History Section */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Recent Requests
        </h2>

        {loading ? (
          <div className="text-center py-8 text-gray-400">
            <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
            Loading...
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <MessageSquare className="w-10 h-10 mx-auto mb-2 opacity-50" />
            No review requests sent yet
          </div>
        ) : (
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {history.map((req, index) => (
              <div 
                key={index}
                className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <div>
                    <p className="text-white font-medium">{req.patient_name}</p>
                    <p className="text-gray-500 text-sm">{req.patient_phone}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded-full">
                    Sent
                  </span>
                  <p className="text-gray-500 text-xs mt-1">
                    {new Date(req.sent_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tips */}
      <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4">
        <h3 className="text-yellow-400 font-medium mb-2">💡 Tips for More Reviews</h3>
        <ul className="text-gray-400 text-sm space-y-1">
          <li>• Send requests within 1 hour of their appointment</li>
          <li>• Personalize the message with their name</li>
          <li>• Keep it short and friendly</li>
          <li>• Best days: Tuesday-Thursday (highest response rates)</li>
        </ul>
      </div>
    </div>
  );
};

export default ReviewRequestsPage;
