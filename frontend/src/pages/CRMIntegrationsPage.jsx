import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { 
  CheckCircle, XCircle, RefreshCw, ExternalLink, Copy, Trash2,
  AlertCircle, ArrowRight, Zap, Upload
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// CRM Provider logos/icons
const CRM_PROVIDERS = {
  gohighlevel: {
    name: "GoHighLevel",
    description: "All-in-one marketing platform for agencies",
    color: "bg-emerald-500",
    bgLight: "bg-emerald-50",
    textColor: "text-emerald-700",
    icon: "GHL"
  },
  salesforce: {
    name: "Salesforce",
    description: "Enterprise CRM for sales teams",
    color: "bg-blue-500",
    bgLight: "bg-blue-50",
    textColor: "text-blue-700",
    icon: "SF"
  },
  hubspot: {
    name: "HubSpot",
    description: "Free CRM with marketing tools",
    color: "bg-orange-500",
    bgLight: "bg-orange-50",
    textColor: "text-orange-700",
    icon: "HS"
  }
};

const CRMIntegrationsPage = () => {
  const [crmStatus, setCrmStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pushLogs, setPushLogs] = useState([]);
  const [showConnectDialog, setShowConnectDialog] = useState(false);
  const [connectingProvider, setConnectingProvider] = useState(null);
  const [apiKey, setApiKey] = useState("");
  const [instanceUrl, setInstanceUrl] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);

  const fetchCRMStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/crm/status`);
      setCrmStatus(response.data);
    } catch (error) {
      console.error("Failed to fetch CRM status:", error);
      if (error.response?.status === 403) {
        setCrmStatus({ enabled: false, upgrade_required: true });
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchPushLogs = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/crm/push-logs?limit=20`);
      setPushLogs(response.data.logs || []);
    } catch (error) {
      console.error("Failed to fetch push logs:", error);
    }
  }, []);

  useEffect(() => {
    fetchCRMStatus();
    fetchPushLogs();
  }, [fetchCRMStatus, fetchPushLogs]);

  const handleConnect = (provider) => {
    setConnectingProvider(provider);
    setApiKey("");
    setInstanceUrl("");
    setShowConnectDialog(true);
  };

  const handleDisconnect = async (provider) => {
    if (!window.confirm(`Are you sure you want to disconnect ${CRM_PROVIDERS[provider].name}?`)) {
      return;
    }

    try {
      await axios.post(`${API}/crm/disconnect/${provider}`);
      toast.success(`${CRM_PROVIDERS[provider].name} disconnected`);
      fetchCRMStatus();
    } catch (error) {
      toast.error("Failed to disconnect CRM");
    }
  };

  const submitConnection = async () => {
    if (!apiKey) {
      toast.error("Please enter an API key");
      return;
    }

    if (connectingProvider === "salesforce" && !instanceUrl) {
      toast.error("Please enter your Salesforce instance URL");
      return;
    }

    setIsConnecting(true);
    try {
      const response = await axios.post(`${API}/crm/connect`, {
        provider: connectingProvider,
        api_key: apiKey,
        instance_url: instanceUrl || undefined
      });

      if (response.data.status === "connected") {
        toast.success(`${CRM_PROVIDERS[connectingProvider].name} connected successfully!`);
        setShowConnectDialog(false);
        fetchCRMStatus();
      } else if (response.data.status === "redirect") {
        // OAuth flow - redirect to auth URL
        window.location.href = response.data.auth_url;
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to connect CRM");
    } finally {
      setIsConnecting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 md:p-8 space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      </div>
    );
  }

  // Show upgrade prompt if CRM integration not enabled
  if (!crmStatus?.enabled) {
    return (
      <div className="p-6 md:p-8 space-y-6" data-testid="crm-page">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            CRM Integrations
          </h1>
          <p className="text-gray-500 mt-1">Connect your CRM to auto-sync qualified leads</p>
        </div>

        <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Zap className="w-8 h-8 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Unlock CRM Integrations
            </h2>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              Automatically push qualified leads to GoHighLevel, Salesforce, or HubSpot. 
              Available on Professional plan and above.
            </p>
            <Button className="bg-blue-600 hover:bg-blue-700 text-white" asChild>
              <a href="/app/packs">
                <ArrowRight className="w-4 h-4 mr-2" />
                Upgrade Your Plan
              </a>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="crm-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            CRM Integrations
          </h1>
          <p className="text-gray-500 mt-1">Connect your CRM to auto-sync qualified leads</p>
        </div>
        <Button variant="outline" onClick={fetchCRMStatus} data-testid="refresh-crm-status">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <p className="font-medium text-blue-900">How it works</p>
            <p className="text-sm text-blue-700 mt-1">
              When a lead's status changes to "Qualified", it will automatically be pushed to all connected CRMs. 
              You can also manually push leads from the Funnel page.
            </p>
          </div>
        </div>
      </div>

      {/* CRM Connection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {crmStatus?.connections?.map((crm) => {
          const provider = CRM_PROVIDERS[crm.provider];
          if (!provider) return null;

          return (
            <Card key={crm.provider} className="bg-white border border-gray-200 shadow-sm" data-testid={`crm-card-${crm.provider}`}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 ${provider.color} rounded-lg flex items-center justify-center text-white font-bold text-sm`}>
                      {provider.icon}
                    </div>
                    <div>
                      <CardTitle className="text-lg">{provider.name}</CardTitle>
                      <CardDescription className="text-xs">{provider.description}</CardDescription>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Status */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Status</span>
                  <Badge 
                    variant={crm.is_connected ? "default" : "secondary"}
                    className={crm.is_connected ? "bg-green-100 text-green-800" : ""}
                    data-testid={`crm-status-${crm.provider}`}
                  >
                    {crm.is_connected ? (
                      <><CheckCircle className="w-3 h-3 mr-1" /> Connected</>
                    ) : (
                      <><XCircle className="w-3 h-3 mr-1" /> Not Connected</>
                    )}
                  </Badge>
                </div>

                {/* Stats (if connected) */}
                {crm.is_connected && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Leads Pushed</span>
                      <span className="font-semibold">{crm.total_leads_pushed}</span>
                    </div>
                    {crm.last_sync_at && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Last Sync</span>
                        <span className="text-sm text-gray-500">
                          {new Date(crm.last_sync_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                    {crm.last_error && (
                      <div className="bg-red-50 border border-red-200 rounded p-2">
                        <p className="text-xs text-red-700 truncate">{crm.last_error}</p>
                      </div>
                    )}
                  </>
                )}

                {/* Action Button */}
                {crm.is_connected ? (
                  <Button 
                    variant="outline" 
                    className="w-full text-red-600 hover:bg-red-50 border-red-200"
                    onClick={() => handleDisconnect(crm.provider)}
                    data-testid={`disconnect-${crm.provider}`}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Disconnect
                  </Button>
                ) : (
                  <Button 
                    className={`w-full ${provider.color} hover:opacity-90 text-white`}
                    onClick={() => handleConnect(crm.provider)}
                    data-testid={`connect-${crm.provider}`}
                  >
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Connect {provider.name}
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Recent Push Logs */}
      <Card className="bg-white border border-gray-200 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Recent Lead Syncs
            </CardTitle>
            <CardDescription>History of leads pushed to CRMs</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={fetchPushLogs}>
            <RefreshCw className="w-3 h-3 mr-1" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {pushLogs.length === 0 ? (
            <div className="text-center py-8">
              <Upload className="w-12 h-12 text-gray-300 mx-auto" />
              <p className="text-gray-500 mt-3">No lead syncs yet</p>
              <p className="text-sm text-gray-400">
                Leads will appear here when qualified leads are pushed to your CRMs
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[300px]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Lead</TableHead>
                    <TableHead>CRM</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pushLogs.map((log) => {
                    const provider = CRM_PROVIDERS[log.provider];
                    return (
                      <TableRow key={log.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{log.lead_data?.business_name || "Unknown"}</p>
                            <p className="text-xs text-gray-500">{log.lead_data?.contact_name}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={provider?.bgLight}>
                            <span className={provider?.textColor}>{provider?.name}</span>
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={log.status === "success" ? "default" : "destructive"}
                            className={log.status === "success" ? "bg-green-100 text-green-800" : ""}
                          >
                            {log.status === "success" ? (
                              <><CheckCircle className="w-3 h-3 mr-1" /> Success</>
                            ) : (
                              <><XCircle className="w-3 h-3 mr-1" /> Failed</>
                            )}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {new Date(log.created_at).toLocaleString()}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Connect Dialog */}
      <Dialog open={showConnectDialog} onOpenChange={setShowConnectDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              Connect {connectingProvider && CRM_PROVIDERS[connectingProvider]?.name}
            </DialogTitle>
            <DialogDescription>
              Enter your API key to connect your CRM account
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="api-key">API Key / Access Token</Label>
              <Input
                id="api-key"
                type="password"
                placeholder="Enter your API key..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                data-testid="crm-api-key-input"
              />
              <p className="text-xs text-gray-500">
                {connectingProvider === "gohighlevel" && (
                  <>Get your API key from GoHighLevel Settings &gt; API Keys</>
                )}
                {connectingProvider === "salesforce" && (
                  <>Get your access token from Salesforce Setup &gt; Connected Apps</>
                )}
                {connectingProvider === "hubspot" && (
                  <>Get your private app access token from HubSpot Settings &gt; Private Apps</>
                )}
              </p>
            </div>

            {connectingProvider === "salesforce" && (
              <div className="space-y-2">
                <Label htmlFor="instance-url">Salesforce Instance URL</Label>
                <Input
                  id="instance-url"
                  placeholder="https://your-instance.salesforce.com"
                  value={instanceUrl}
                  onChange={(e) => setInstanceUrl(e.target.value)}
                  data-testid="salesforce-instance-url"
                />
                <p className="text-xs text-gray-500">
                  Your Salesforce domain (e.g., https://mycompany.my.salesforce.com)
                </p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConnectDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={submitConnection} 
              disabled={isConnecting}
              className="bg-blue-600 hover:bg-blue-700"
              data-testid="submit-crm-connection"
            >
              {isConnecting ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Connecting...</>
              ) : (
                <>Connect</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CRMIntegrationsPage;
