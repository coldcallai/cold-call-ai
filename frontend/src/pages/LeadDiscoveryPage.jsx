import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import StatusBadge from "@/components/StatusBadge";
import TrustLine from "@/components/TrustLine";
import BookingDialog from "@/components/BookingDialog";
import {
  Phone, Calendar, Search, Plus, Trash2, CheckCircle, Clock,
  Building2, Upload, Download, Zap, X, Edit3, Tags, RefreshCw
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LeadDiscovery = () => {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("Toast alternative");
  const [industry, setIndustry] = useState("");
  const [location, setLocation] = useState("");
  const [campaigns, setCampaigns] = useState([]);
  const [selectedLead, setSelectedLead] = useState(null);
  const [selectedCampaign, setSelectedCampaign] = useState("");
  const [activeTab, setActiveTab] = useState("discover");
  const [setupStatus, setSetupStatus] = useState(null);
  const [verifyingPhone, setVerifyingPhone] = useState(null); // Track which lead is being verified
  
  // Custom keywords state
  const [customKeywords, setCustomKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState("");
  const [showKeywordManager, setShowKeywordManager] = useState(false);
  const [bulkKeywords, setBulkKeywords] = useState("");
  
  // Preview state
  const [previewing, setPreviewing] = useState(false);
  const [previewLeads, setPreviewLeads] = useState([]);
  const [showPreview, setShowPreview] = useState(false);
  
  // Line type filter
  const [lineTypeFilter, setLineTypeFilter] = useState("all");

  // Exclude industries filter (e.g., exclude medical/grocery/motels)
  const [excludeIndustries, setExcludeIndustries] = useState("");

  // Keyword Template Packs — one-click vertical presets
  const KEYWORD_PACKS = {
    "digital_marketing": {
      label: "Digital Marketing / Agency Clients",
      industry: "Digital Marketing, SEO, Advertising Agency",
      exclude: "",
      keywords: [
        "need more leads", "SEO agency", "Google Ads management", "Facebook Ads agency",
        "lead generation services", "digital marketing agency", "PPC management",
        "hire SEO company", "social media marketing", "website conversion optimization",
        "marketing automation", "grow my business online", "need more customers"
      ]
    },
    "roofing": {
      label: "Roofing Contractors",
      industry: "Roofing",
      exclude: "medical, grocery, hotel, motel, restaurant",
      keywords: [
        "roofing contractor", "roof repair", "roof replacement", "commercial roofing",
        "residential roofing", "storm damage roofing", "metal roofing", "shingle replacement",
        "roofing company near me", "emergency roof repair", "roof inspection"
      ]
    },
    "dental": {
      label: "Dental Practices",
      industry: "Dental Practice",
      exclude: "grocery, hotel, motel, restaurant, retail",
      keywords: [
        "dental practice management", "dental marketing", "patient acquisition",
        "dental SEO", "grow dental practice", "dental patient financing",
        "new patient dentistry", "dental office software", "dental appointment scheduling"
      ]
    },
    "restaurants_pos": {
      label: "Restaurants (POS/Payments)",
      industry: "Restaurant, Food & Beverage",
      exclude: "medical, grocery, hotel, motel",
      keywords: [
        "Toast alternative", "Square alternative", "Clover alternative",
        "restaurant POS system", "restaurant credit card processing", "reduce restaurant fees",
        "best POS for restaurants", "switch payment processor", "restaurant online ordering"
      ]
    },
    "saas_b2b": {
      label: "SaaS / B2B Tech",
      industry: "SaaS, Software",
      exclude: "medical, grocery, hotel, motel, restaurant, retail",
      keywords: [
        "SaaS lead generation", "B2B sales tools", "CRM alternative", "sales automation",
        "outbound sales software", "cold email tools", "sales engagement platform",
        "lead enrichment", "sales pipeline software"
      ]
    },
    "hvac_contractors": {
      label: "HVAC / Home Services",
      industry: "HVAC, Home Services",
      exclude: "medical, grocery, hotel, motel, restaurant",
      keywords: [
        "HVAC repair", "AC installation", "heating and cooling", "HVAC service",
        "plumber near me", "electrician", "home services marketing", "contractor lead gen",
        "emergency HVAC"
      ]
    },
    "insurance_agents": {
      label: "Insurance Agents",
      industry: "Insurance",
      exclude: "grocery, hotel, motel, restaurant",
      keywords: [
        "insurance leads", "life insurance leads", "medicare leads", "auto insurance quotes",
        "commercial insurance", "insurance agency marketing", "insurance CRM",
        "exclusive insurance leads"
      ]
    },
    "real_estate": {
      label: "Real Estate Agents",
      industry: "Real Estate",
      exclude: "grocery, hotel, motel, restaurant, medical",
      keywords: [
        "real estate leads", "seller leads", "buyer leads", "FSBO leads",
        "real estate CRM", "real estate marketing", "realtor website", "MLS tools",
        "expired listings"
      ]
    }
  };

  const applyKeywordPack = (packKey) => {
    const pack = KEYWORD_PACKS[packKey];
    if (!pack) return;
    setCustomKeywords(pack.keywords);
    setIndustry(pack.industry);
    setExcludeIndustries(pack.exclude);
    toast.success(`Loaded "${pack.label}" pack — ${pack.keywords.length} keywords`);
  };

  const defaultIntentKeywords = [
    "Toast alternative",
    "Square alternative",
    "Stripe alternative",
    "Clover alternative",
    "best POS system",
    "credit card processing",
    "payment processing",
    "merchant services",
    "reduce processing fees"
  ];
  
  // Use custom keywords if any, otherwise use defaults
  const intentKeywords = customKeywords.length > 0 ? customKeywords : defaultIntentKeywords;

  const addKeyword = () => {
    const keyword = newKeyword.trim();
    if (keyword && !customKeywords.includes(keyword) && customKeywords.length < 100) {
      setCustomKeywords([...customKeywords, keyword]);
      setNewKeyword("");
    } else if (customKeywords.length >= 100) {
      toast.error("Maximum 100 keywords allowed");
    }
  };

  const removeKeyword = (keywordToRemove) => {
    setCustomKeywords(customKeywords.filter(k => k !== keywordToRemove));
  };

  const clearAllKeywords = () => {
    setCustomKeywords([]);
  };

  const addBulkKeywords = () => {
    const keywords = bulkKeywords
      .split(/[\n,]/)
      .map(k => k.trim())
      .filter(k => k && !customKeywords.includes(k));
    
    const available = 100 - customKeywords.length;
    const toAdd = keywords.slice(0, available);
    
    if (toAdd.length > 0) {
      setCustomKeywords([...customKeywords, ...toAdd]);
      setBulkKeywords("");
      toast.success(`Added ${toAdd.length} keywords`);
      if (keywords.length > available) {
        toast.warning(`${keywords.length - available} keywords skipped (100 max limit)`);
      }
    }
  };

  // Preview example leads (FREE - no credits used)
  const previewExamples = async () => {
    setPreviewing(true);
    setShowPreview(true);
    try {
      const token = localStorage.getItem('session_token');
      const excludeList = excludeIndustries
        ? excludeIndustries.split(",").map(s => s.trim()).filter(Boolean)
        : null;
      const response = await axios.post(`${API}/leads/preview-examples`, {
        search_query: searchQuery,
        industry: industry || null,
        location: location || null,
        custom_keywords: customKeywords.length > 0 ? customKeywords : null,
        exclude_industries: excludeList
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setPreviewLeads(response.data.example_leads || []);
      toast.success("Preview generated! These are example leads based on your keywords.");
    } catch (error) {
      toast.error("Failed to generate preview");
      setPreviewLeads([]);
    } finally {
      setPreviewing(false);
    }
  };

  // Load saved keywords from backend
  const loadSavedKeywords = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/user/keywords`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.keywords && response.data.keywords.length > 0) {
        setCustomKeywords(response.data.keywords);
      }
    } catch (error) {
      console.error("Failed to load saved keywords:", error);
    }
  };

  // Save keywords to backend
  const saveKeywords = async () => {
    try {
      const token = localStorage.getItem('session_token');
      await axios.post(`${API}/user/keywords`, 
        { keywords: customKeywords },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`Saved ${customKeywords.length} keywords to your profile`);
    } catch (error) {
      toast.error("Failed to save keywords");
    }
  };

  const fetchLeads = async () => {
    try {
      const response = await axios.get(`${API}/leads`);
      setLeads(response.data);
    } catch (error) {
      toast.error("Failed to load leads");
    } finally {
      setLoading(false);
    }
  };

  const fetchCampaigns = async () => {
    try {
      const response = await axios.get(`${API}/campaigns`);
      setCampaigns(response.data.filter(c => c.status === 'active'));
    } catch (error) {
      console.error("Failed to fetch campaigns:", error);
    }
  };

  const fetchSetupStatus = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/setup/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSetupStatus(response.data);
    } catch (error) {
      console.error("Failed to fetch setup status:", error);
    }
  };

  useEffect(() => {
    fetchLeads();
    fetchCampaigns();
    loadSavedKeywords();
    fetchSetupStatus();
  }, []);

  const discoverLeads = async () => {
    setDiscovering(true);
    try {
      const token = localStorage.getItem('session_token');
      const excludeList = excludeIndustries
        ? excludeIndustries.split(",").map(s => s.trim()).filter(Boolean)
        : null;
      const response = await axios.post(`${API}/leads/gpt-intent-search`, {
        search_query: searchQuery,
        industry: industry || null,
        location: location || null,
        max_results: 10,
        custom_keywords: customKeywords.length > 0 ? customKeywords : null,
        campaign_id: selectedCampaign || null,
        exclude_industries: excludeList
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const { discovered, credits_used, credits_remaining, skipped_duplicates } = response.data;
      const dupeNote = skipped_duplicates > 0 ? ` (${skipped_duplicates} skipped as duplicates)` : '';
      toast.success(
        `Discovered ${discovered} high-intent leads${dupeNote}! ${credits_used} credits used, ${credits_remaining} remaining`
      );
      fetchLeads();
      // Refresh user data to update sidebar credits
      refreshUser();
    } catch (error) {
      if (error.response?.status === 402) {
        toast.error(error.response.data.detail || "Insufficient credits. Please purchase more leads.");
      } else {
        toast.error("Failed to discover leads");
      }
    } finally {
      setDiscovering(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/leads/upload-csv`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(response.data.message);
      if (response.data.errors > 0) {
        toast.warning(`${response.data.errors} rows had errors`);
      }
      fetchLeads();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to upload CSV");
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const exportLeads = async () => {
    try {
      window.open(`${API}/leads/export-csv`, '_blank');
      toast.success("Downloading leads CSV...");
    } catch (error) {
      toast.error("Failed to export leads");
    }
  };

  const simulateCall = async (leadId) => {
    // Check if setup is complete before allowing calls
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
      const token = localStorage.getItem('session_token');
      const response = await axios.post(
        `${API}/calls/simulate?lead_id=${leadId}&campaign_id=${selectedCampaign}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const { credits_remaining } = response.data;
      toast.success(`Call started! (${credits_remaining} call credits remaining)`);
      setTimeout(fetchLeads, 3000);
      // Refresh user data to update sidebar credits
      refreshUser();
    } catch (error) {
      if (error.response?.status === 402) {
        toast.error(error.response.data.detail || "Insufficient call credits. Please purchase more.");
      } else {
        toast.error("Failed to start call");
      }
    }
  };

  const deleteLead = async (leadId) => {
    try {
      await axios.delete(`${API}/leads/${leadId}`);
      toast.success("Lead deleted");
      fetchLeads();
    } catch (error) {
      toast.error("Failed to delete lead");
    }
  };

  const verifyPhone = async (leadId) => {
    setVerifyingPhone(leadId);
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(
        `${API}/leads/${leadId}/verify-phone`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const { verification } = response.data;
      const lineType = verification.line_type || 'unknown';
      const carrier = verification.carrier || 'Unknown carrier';
      
      // Update local state with verification result
      setLeads(prevLeads => 
        prevLeads.map(lead => 
          lead.id === leadId 
            ? { 
                ...lead, 
                line_type: lineType,
                carrier: carrier,
                phone_verified: verification.is_valid,
                dial_priority: verification.dial_priority
              }
            : lead
        )
      );
      
      // Show appropriate toast based on line type
      if (verification.is_mobile) {
        toast.success(`Mobile number verified: ${carrier}`, {
          description: "High pickup rate expected (80%+)"
        });
      } else if (verification.is_landline) {
        toast.info(`Landline verified: ${carrier}`, {
          description: "Business line - 20% typical pickup rate"
        });
      } else if (verification.is_voip) {
        toast.warning(`VoIP number detected: ${carrier}`, {
          description: "May have lower pickup rate"
        });
      } else {
        toast.info(`Phone verified: ${lineType}`);
      }
    } catch (error) {
      const errDetail = error.response?.data?.detail;
      const errMsg = typeof errDetail === 'string' ? errDetail : "Failed to verify phone";
      toast.error(errMsg);
    } finally {
      setVerifyingPhone(null);
    }
  };

  const verifyAllUnverified = async () => {
    const unverifiedLeads = leads.filter(l => !l.phone_verified && l.phone);
    if (unverifiedLeads.length === 0) {
      toast.info("All leads are already verified");
      return;
    }
    
    setVerifyingPhone('bulk');
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(
        `${API}/leads/verify-phones-bulk`,
        { verify_all_unverified: true },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const results = response.data.results || {};
      toast.success(`Verified ${results.verified || 0} phone numbers`, {
        description: `Mobile: ${results.mobile || 0}, Landline: ${results.landline || 0}, VoIP: ${results.voip || 0}`
      });
      
      fetchLeads(); // Refresh to show updated data
    } catch (error) {
      const errDetail = error.response?.data?.detail;
      const errMsg = typeof errDetail === 'string' ? errDetail : "Failed to bulk verify phones";
      toast.error(errMsg);
    } finally {
      setVerifyingPhone(null);
    }
  };

  // Count unverified leads
  const unverifiedCount = leads.filter(l => !l.phone_verified && l.phone).length;

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="lead-discovery-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Lead Discovery
          </h1>
          <p className="text-gray-500 mt-1">Find businesses actively searching for payment solutions</p>
          <TrustLine className="mt-2" />
        </div>
        <div className="flex items-center gap-2">
          {unverifiedCount > 0 && (
            <Button
              variant="outline"
              onClick={verifyAllUnverified}
              disabled={verifyingPhone === 'bulk'}
              className="border-blue-200 text-blue-600 hover:bg-blue-50"
              data-testid="verify-all-phones-btn"
            >
              {verifyingPhone === 'bulk' ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2" />
              )}
              Verify All ({unverifiedCount})
            </Button>
          )}
          <Button
            variant="outline"
            onClick={exportLeads}
            disabled={leads.length === 0}
            className="border-gray-300"
          >
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Tabs for Discover / Upload */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="discover" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            AI Discovery
          </TabsTrigger>
          <TabsTrigger value="upload" className="flex items-center gap-2">
            <Upload className="w-4 h-4" />
            Upload CSV
          </TabsTrigger>
        </TabsList>

        <TabsContent value="discover" className="space-y-4 mt-4">
          {/* Intent Keywords Section */}
          <Card className="bg-gradient-to-r from-cyan-50 to-teal-50 border border-cyan-200 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Tags className="w-4 h-4 text-cyan-700" />
                  <p className="text-sm font-medium text-cyan-800">
                    Intent Keywords ({customKeywords.length > 0 ? `${customKeywords.length} custom` : 'defaults'})
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowKeywordManager(!showKeywordManager)}
                  className="text-cyan-700 border-cyan-300 hover:bg-cyan-100"
                  data-testid="manage-keywords-btn"
                >
                  <Edit3 className="w-3 h-3 mr-1" />
                  {showKeywordManager ? 'Hide' : 'Manage Keywords'}
                </Button>
              </div>
              
              {/* Quick Select Keywords */}
              <div className="flex flex-wrap gap-2">
                {intentKeywords.slice(0, 15).map((keyword) => (
                  <button
                    key={keyword}
                    onClick={() => setSearchQuery(keyword)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-1 ${
                      searchQuery === keyword
                        ? 'bg-cyan-600 text-white'
                        : 'bg-white text-cyan-700 border border-cyan-300 hover:bg-cyan-100'
                    }`}
                  >
                    {keyword}
                    {customKeywords.length > 0 && (
                      <X 
                        className="w-3 h-3 ml-1 hover:text-red-500" 
                        onClick={(e) => { e.stopPropagation(); removeKeyword(keyword); }}
                      />
                    )}
                  </button>
                ))}
                {intentKeywords.length > 15 && (
                  <span className="px-3 py-1.5 text-sm text-cyan-600">
                    +{intentKeywords.length - 15} more
                  </span>
                )}
              </div>

              {/* Keyword Manager Panel */}
              {showKeywordManager && (
                <div className="mt-4 pt-4 border-t border-cyan-200 space-y-4">
                  {/* Add Single Keyword */}
                  <div>
                    <Label className="text-cyan-800 text-sm">Add Keyword</Label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        value={newKeyword}
                        onChange={(e) => setNewKeyword(e.target.value)}
                        placeholder="e.g., best CRM software"
                        className="flex-1"
                        onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
                        data-testid="new-keyword-input"
                      />
                      <Button 
                        onClick={addKeyword}
                        disabled={!newKeyword.trim() || customKeywords.length >= 100}
                        className="bg-cyan-600 hover:bg-cyan-700"
                        data-testid="add-keyword-btn"
                      >
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Bulk Add Keywords */}
                  <div>
                    <Label className="text-cyan-800 text-sm">Bulk Add (paste multiple, comma or newline separated)</Label>
                    <div className="flex gap-2 mt-1">
                      <Textarea
                        value={bulkKeywords}
                        onChange={(e) => setBulkKeywords(e.target.value)}
                        placeholder="keyword 1, keyword 2&#10;keyword 3&#10;keyword 4"
                        className="flex-1 h-20"
                        data-testid="bulk-keywords-input"
                      />
                      <Button 
                        onClick={addBulkKeywords}
                        disabled={!bulkKeywords.trim()}
                        className="bg-cyan-600 hover:bg-cyan-700 self-end"
                        data-testid="add-bulk-btn"
                      >
                        Add All
                      </Button>
                    </div>
                  </div>

                  {/* Keywords Summary */}
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-cyan-700">
                      {customKeywords.length}/100 keywords
                    </span>
                    <div className="flex gap-2">
                      {customKeywords.length > 0 && (
                        <>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={saveKeywords}
                            className="text-green-600 border-green-300 hover:bg-green-50"
                            data-testid="save-keywords-btn"
                          >
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Save Keywords
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={clearAllKeywords}
                            className="text-red-600 border-red-300 hover:bg-red-50"
                            data-testid="clear-keywords-btn"
                          >
                            <Trash2 className="w-3 h-3 mr-1" />
                            Clear All
                          </Button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* All Custom Keywords List */}
                  {customKeywords.length > 0 && (
                    <div className="bg-white rounded-lg p-3 max-h-40 overflow-y-auto">
                      <div className="flex flex-wrap gap-1">
                        {customKeywords.map((keyword, idx) => (
                          <span 
                            key={idx}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-cyan-100 text-cyan-800 rounded text-xs"
                          >
                            {keyword}
                            <X 
                              className="w-3 h-3 cursor-pointer hover:text-red-500" 
                              onClick={() => removeKeyword(keyword)}
                            />
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Keyword Template Packs — one-click vertical presets */}
          <Card className="bg-gradient-to-br from-violet-50 to-indigo-50 border border-violet-200 shadow-sm mb-4" data-testid="keyword-packs-card">
            <CardContent className="p-4">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <Zap className="w-4 h-4 text-violet-700" />
                <span className="text-sm font-semibold text-violet-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                  Quick Start — Keyword Packs
                </span>
                <span className="text-xs text-violet-700">(loads industry + keywords + exclusions in one click)</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(KEYWORD_PACKS).map(([key, pack]) => (
                  <Button
                    key={key}
                    data-testid={`keyword-pack-${key}`}
                    size="sm"
                    variant="outline"
                    className="border-violet-300 bg-white text-violet-800 hover:bg-violet-100 text-xs"
                    onClick={() => applyKeywordPack(key)}
                  >
                    {pack.label}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Search Form */}
          <Card className="bg-white border border-gray-200 shadow-sm">
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <Label htmlFor="search">Search Query</Label>
                  <Input
                    id="search"
                    data-testid="lead-search-input"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="e.g., Toast alternative"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="industry">Industry (Optional)</Label>
                  <Input
                    id="industry"
                    data-testid="lead-industry-input"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    placeholder="e.g., Restaurant, Retail"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="location">Location (Optional)</Label>
                  <Input
                    id="location"
                    data-testid="lead-location-input"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="e.g., Texas, New York"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label>Campaign for Calling</Label>
                  <Select value={selectedCampaign} onValueChange={setSelectedCampaign}>
                    <SelectTrigger data-testid="campaign-select" className="mt-1">
                      <SelectValue placeholder="Select campaign" />
                    </SelectTrigger>
                    <SelectContent>
                      {campaigns.map(c => (
                        <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="mt-4">
                <Label htmlFor="exclude-industries" className="text-xs text-gray-600">
                  Exclude Industries (comma separated — blocks GPT from returning these)
                </Label>
                <Input
                  id="exclude-industries"
                  data-testid="exclude-industries-input"
                  value={excludeIndustries}
                  onChange={(e) => setExcludeIndustries(e.target.value)}
                  placeholder="e.g., medical, grocery, motel, hotel, restaurant"
                  className="mt-1 text-sm"
                />
              </div>
              <div className="mt-4 flex justify-end gap-3">
                <Button 
                  variant="outline"
                  data-testid="preview-btn"
                  onClick={previewExamples} 
                  disabled={previewing}
                  className="border-cyan-500 text-cyan-700 hover:bg-cyan-50"
                >
                  {previewing ? (
                    <>
                      <Clock className="w-4 h-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Preview Examples (Free)
                    </>
                  )}
                </Button>
                <Button 
                  data-testid="discover-btn"
                  onClick={discoverLeads} 
                  disabled={discovering}
                  className="bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white"
                >
                  {discovering ? (
                    <>
                      <Clock className="w-4 h-4 mr-2 animate-spin" />
                      AI Searching...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 mr-2" />
                      Discover High-Intent Leads
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Preview Results Section */}
          {showPreview && (
            <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 shadow-sm mt-4">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Search className="w-5 h-5 text-amber-600" />
                    <CardTitle className="text-lg text-amber-800" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                      Example Leads Preview
                    </CardTitle>
                    <span className="px-2 py-0.5 bg-amber-200 text-amber-800 text-xs rounded-full">FREE</span>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setShowPreview(false)}
                    className="text-amber-600 hover:text-amber-800"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                <CardDescription className="text-amber-700">
                  These are example leads based on your keywords. Run "Discover" to find and save real leads.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {previewing ? (
                  <div className="text-center py-8">
                    <Clock className="w-8 h-8 animate-spin text-amber-500 mx-auto mb-2" />
                    <p className="text-amber-700">Generating preview examples...</p>
                  </div>
                ) : previewLeads.length > 0 ? (
                  <div className="space-y-3">
                    {previewLeads.map((lead, idx) => (
                      <div key={idx} className="bg-white rounded-lg p-4 border border-amber-200">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-semibold text-gray-900">{lead.name}</h4>
                            <p className="text-sm text-gray-600">{lead.industry} • {lead.location}</p>
                            <p className="text-sm text-gray-500 mt-1">{lead.phone}</p>
                          </div>
                          <span className="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded">Example</span>
                        </div>
                        <div className="mt-2">
                          <p className="text-xs text-gray-500 mb-1">Intent Signals:</p>
                          <div className="flex flex-wrap gap-1">
                            {(lead.intent_signals || []).slice(0, 3).map((signal, i) => (
                              <span key={i} className="px-2 py-0.5 bg-cyan-100 text-cyan-700 text-xs rounded">
                                {signal}
                              </span>
                            ))}
                          </div>
                        </div>
                        {lead.pain_point && (
                          <p className="text-xs text-gray-500 mt-2 italic">"{lead.pain_point}"</p>
                        )}
                      </div>
                    ))}
                    <div className="text-center pt-2">
                      <Button 
                        onClick={discoverLeads}
                        disabled={discovering}
                        className="bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white"
                      >
                        <Zap className="w-4 h-4 mr-2" />
                        Find Real Leads Like These
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-center py-4 text-amber-700">No preview leads generated. Try different keywords.</p>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="upload" className="mt-4">
          <Card className="bg-white border border-gray-200 shadow-sm">
            <CardHeader>
              <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                Upload Your Lead List
              </CardTitle>
              <CardDescription>
                Import leads from a CSV file. We'll call them for you.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-cyan-400 transition-colors">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-2">Drag and drop your CSV file, or click to browse</p>
                <p className="text-sm text-gray-400 mb-4">Required columns: business_name, phone</p>
                <p className="text-sm text-gray-400 mb-4">Optional: email, contact_name</p>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="csv-upload"
                  disabled={uploading}
                />
                <label htmlFor="csv-upload">
                  <Button 
                    asChild 
                    disabled={uploading}
                    className="bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white cursor-pointer"
                  >
                    <span>
                      {uploading ? (
                        <>
                          <Clock className="w-4 h-4 mr-2 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4 mr-2" />
                          Choose CSV File
                        </>
                      )}
                    </span>
                  </Button>
                </label>
              </div>
              
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-700 mb-2">CSV Template</p>
                <code className="text-xs text-gray-600 block bg-white p-3 rounded border">
                  business_name,phone,email,contact_name<br/>
                  "Joe's Pizza","+1-555-0123","joe@joespizza.com","Joe Smith"<br/>
                  "Main St Retail","+1-555-0124","info@mainst.com","Sarah Johnson"
                </code>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Leads Table */}
      <Card className="bg-white border border-gray-200 shadow-sm">
        <CardHeader className="border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-center justify-between">
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Discovered Leads ({leads.length})
            </CardTitle>
            <div className="flex items-center gap-4">
              {/* Line Type Filter */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Filter:</span>
                <Select value={lineTypeFilter} onValueChange={setLineTypeFilter}>
                  <SelectTrigger className="w-[140px] h-8" data-testid="line-type-filter">
                    <SelectValue placeholder="All Types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="mobile">Mobile Only</SelectItem>
                    <SelectItem value="landline">Landline Only</SelectItem>
                    <SelectItem value="voip">VoIP Only</SelectItem>
                    <SelectItem value="unverified">Unverified</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="text-sm text-gray-500">
                {leads.filter(l => l.source === 'gpt_intent_search').length} from GPT Intent Search
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 space-y-4">
              {[1,2,3].map(i => <Skeleton key={i} className="h-16" />)}
            </div>
          ) : leads.length === 0 ? (
            <div className="p-12 text-center">
              <Building2 className="w-16 h-16 text-gray-300 mx-auto" />
              <p className="text-gray-500 mt-4">No leads found. Click "Discover High-Intent Leads" to find prospects in buying mode.</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {leads
                .filter(lead => {
                  if (lineTypeFilter === 'all') return true;
                  if (lineTypeFilter === 'unverified') return !lead.phone_verified;
                  if (lineTypeFilter === 'mobile') return ['mobile', 'cellphone', 'wireless'].includes(lead.line_type?.toLowerCase());
                  if (lineTypeFilter === 'landline') return ['landline', 'fixedline', 'fixed'].includes(lead.line_type?.toLowerCase());
                  if (lineTypeFilter === 'voip') return ['voip', 'nonfixedvoip', 'non-fixed voip', 'virtual'].includes(lead.line_type?.toLowerCase());
                  return true;
                })
                .map((lead) => (
                <div key={lead.id} className="p-4 hover:bg-gray-50 transition-colors" data-testid={`lead-row-${lead.id}`}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <h3 className="font-semibold text-gray-900">{lead.business_name}</h3>
                        <StatusBadge status={lead.status} />
                        {lead.source === 'gpt_intent_search' && (
                          <Badge className="bg-cyan-100 text-cyan-700 border-0">AI Found</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                        <span className="flex items-center gap-2">
                          {lead.phone}
                          {/* Line Type Badge */}
                          {lead.line_type && lead.line_type !== 'unknown' && (
                            <Badge 
                              className={`text-xs ${
                                lead.line_type === 'mobile' || lead.line_type === 'cellphone' || lead.line_type === 'wireless'
                                  ? 'bg-green-100 text-green-700 border-green-200'
                                  : lead.line_type === 'landline' || lead.line_type === 'fixedline'
                                    ? 'bg-blue-100 text-blue-700 border-blue-200'
                                    : lead.line_type === 'voip' || lead.line_type === 'nonFixedVoip'
                                      ? 'bg-orange-100 text-orange-700 border-orange-200'
                                      : 'bg-gray-100 text-gray-600'
                              }`}
                              data-testid={`line-type-${lead.id}`}
                            >
                              {lead.line_type === 'mobile' || lead.line_type === 'cellphone' || lead.line_type === 'wireless' ? 'Mobile' :
                               lead.line_type === 'landline' || lead.line_type === 'fixedline' ? 'Landline' :
                               lead.line_type === 'voip' || lead.line_type === 'nonFixedVoip' ? 'VoIP' : lead.line_type}
                            </Badge>
                          )}
                          {/* Verify Button */}
                          {!lead.phone_verified && lead.phone && (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 px-2 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                              onClick={() => verifyPhone(lead.id)}
                              disabled={verifyingPhone === lead.id}
                              data-testid={`verify-phone-${lead.id}`}
                            >
                              {verifyingPhone === lead.id ? (
                                <RefreshCw className="w-3 h-3 animate-spin" />
                              ) : (
                                <>
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  Verify
                                </>
                              )}
                            </Button>
                          )}
                          {lead.phone_verified && !lead.line_type && (
                            <CheckCircle className="w-4 h-4 text-green-500" title="Phone verified" />
                          )}
                        </span>
                        {lead.email && <span>{lead.email}</span>}
                      </div>
                      {/* Carrier info if available */}
                      {lead.carrier && (
                        <p className="text-xs text-gray-400 mt-0.5">{lead.carrier}</p>
                      )}
                      {/* Intent Signals */}
                      {lead.intent_signals && lead.intent_signals.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {lead.intent_signals.slice(0, 3).map((signal, idx) => (
                            <span 
                              key={idx} 
                              className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-amber-50 text-amber-700 border border-amber-200"
                            >
                              {signal.length > 40 ? signal.substring(0, 40) + '...' : signal}
                            </span>
                          ))}
                          {lead.intent_signals.length > 3 && (
                            <span className="text-xs text-gray-400">+{lead.intent_signals.length - 3} more</span>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {lead.qualification_score !== null && (
                        <div className="text-center px-3">
                          <p className="text-xs text-gray-500">Score</p>
                          <p className={`text-lg font-bold ${lead.qualification_score >= 60 ? 'text-emerald-600' : 'text-gray-600'}`}>
                            {lead.qualification_score}
                          </p>
                        </div>
                      )}
                      {lead.status === 'new' && (
                        <Button 
                          size="sm" 
                          data-testid={`call-lead-${lead.id}`}
                          onClick={() => simulateCall(lead.id)}
                          disabled={!selectedCampaign}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white"
                        >
                          <Phone className="w-3 h-3 mr-1" />
                          Call
                        </Button>
                      )}
                      {lead.status === 'qualified' && (
                        <Button 
                          size="sm" 
                          data-testid={`book-lead-${lead.id}`}
                          onClick={() => setSelectedLead(lead)}
                          className="bg-purple-600 hover:bg-purple-700 text-white"
                        >
                          <Calendar className="w-3 h-3 mr-1" />
                          Book
                        </Button>
                      )}
                      <Button 
                        size="sm" 
                        variant="ghost"
                        data-testid={`delete-lead-${lead.id}`}
                        onClick={() => deleteLead(lead.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Booking Dialog */}
      <BookingDialog 
        lead={selectedLead} 
        onClose={() => setSelectedLead(null)}
        onSuccess={() => {
          setSelectedLead(null);
          fetchLeads();
        }}
      />
    </div>
  );
};

export default LeadDiscovery;
