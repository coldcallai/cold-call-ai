import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { 
  Shield, Upload, AlertTriangle, CheckCircle, Clock, RefreshCw,
  ExternalLink, FileText, Users, Trash2, Plus, Download, AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DNCManagementPage = () => {
  const [stats, setStats] = useState(null);
  const [refreshReminder, setRefreshReminder] = useState(null);
  const [litigators, setLitigators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showAddLitigator, setShowAddLitigator] = useState(false);
  const [newLitigator, setNewLitigator] = useState({ phone: "", name: "", firm: "", notes: "" });

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, reminderRes, litigatorsRes] = await Promise.all([
        axios.get(`${API}/compliance/dnc/stats`),
        axios.get(`${API}/compliance/dnc/refresh-reminder`),
        axios.get(`${API}/compliance/litigators?limit=100`)
      ]);
      setStats(statsRes.data);
      setRefreshReminder(reminderRes.data);
      setLitigators(litigatorsRes.data.litigators || []);
    } catch (error) {
      console.error("Failed to fetch DNC data:", error);
      toast.error("Failed to load DNC management data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleFTCUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadProgress(10);

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploadProgress(30);
      const response = await axios.post(`${API}/compliance/dnc/upload-ftc`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 70) / progressEvent.total) + 30;
          setUploadProgress(Math.min(progress, 95));
        }
      });
      setUploadProgress(100);
      toast.success(response.data.message);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to upload FTC DNC data");
    } finally {
      setUploading(false);
      setUploadProgress(0);
      event.target.value = "";
    }
  };

  const handleLitigatorUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${API}/compliance/litigators/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success(response.data.message);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to upload litigator list");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  const handleAddLitigator = async () => {
    if (!newLitigator.phone) {
      toast.error("Phone number is required");
      return;
    }

    try {
      await axios.post(`${API}/compliance/litigators/add`, null, {
        params: {
          phone_number: newLitigator.phone,
          name: newLitigator.name || undefined,
          firm: newLitigator.firm || undefined,
          notes: newLitigator.notes || undefined
        }
      });
      toast.success("Litigator added successfully");
      setShowAddLitigator(false);
      setNewLitigator({ phone: "", name: "", firm: "", notes: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to add litigator");
    }
  };

  const handleRemoveLitigator = async (phone) => {
    if (!window.confirm("Remove this number from the litigator list?")) return;

    try {
      await axios.delete(`${API}/compliance/litigators/${encodeURIComponent(phone)}`);
      toast.success("Litigator removed");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to remove litigator");
    }
  };

  const getUrgencyColor = (urgency) => {
    switch (urgency) {
      case "critical": return "bg-red-100 border-red-500 text-red-800";
      case "high": return "bg-orange-100 border-orange-500 text-orange-800";
      case "warning": return "bg-yellow-100 border-yellow-500 text-yellow-800";
      default: return "bg-green-100 border-green-500 text-green-800";
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "current": return <Badge className="bg-green-100 text-green-800">Current</Badge>;
      case "due_soon": return <Badge className="bg-yellow-100 text-yellow-800">Due Soon</Badge>;
      case "overdue": return <Badge className="bg-orange-100 text-orange-800">Overdue</Badge>;
      case "critical": return <Badge className="bg-red-100 text-red-800">Critical</Badge>;
      default: return <Badge variant="secondary">Never Loaded</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="p-6 md:p-8 space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="dnc-management-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            DNC Compliance Management
          </h1>
          <p className="text-gray-500 mt-1">Manage National DNC Registry data and TCPA litigator lists</p>
        </div>
        <Button variant="outline" onClick={fetchData} data-testid="refresh-dnc-data">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Refresh Reminder Alert */}
      {refreshReminder && refreshReminder.needs_refresh && (
        <Alert className={`border-l-4 ${getUrgencyColor(refreshReminder.urgency)}`}>
          <AlertTriangle className="h-5 w-5" />
          <AlertTitle className="font-semibold">
            {refreshReminder.urgency === "critical" ? "CRITICAL: " : ""}
            DNC Data Refresh Required
          </AlertTitle>
          <AlertDescription className="mt-1">
            {refreshReminder.message}
            <Button 
              variant="link" 
              className="p-0 h-auto ml-2 text-blue-600"
              onClick={() => window.open("https://telemarketing.donotcall.gov", "_blank")}
            >
              Download from FTC <ExternalLink className="w-3 h-3 ml-1" />
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* National DNC Card */}
        <Card className="border border-gray-200">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="w-5 h-5 text-blue-600" />
                National DNC List
              </CardTitle>
              {stats && getStatusBadge(stats.national_dnc?.refresh_status)}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-3xl font-bold text-gray-900">
              {stats?.national_dnc?.count?.toLocaleString() || 0}
              <span className="text-sm font-normal text-gray-500 ml-2">numbers</span>
            </div>
            
            {stats?.national_dnc?.last_refresh && (
              <div className="text-sm text-gray-500">
                <Clock className="w-4 h-4 inline mr-1" />
                Last refresh: {new Date(stats.national_dnc.last_refresh).toLocaleDateString()}
                {stats.national_dnc.days_since_refresh !== null && (
                  <span className="ml-1">({stats.national_dnc.days_since_refresh} days ago)</span>
                )}
              </div>
            )}

            <div className="pt-2">
              <Label htmlFor="ftc-upload" className="cursor-pointer">
                <div className="flex items-center justify-center w-full h-20 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors">
                  {uploading ? (
                    <div className="w-full px-4">
                      <Progress value={uploadProgress} className="h-2" />
                      <p className="text-sm text-center mt-2 text-gray-500">Uploading... {uploadProgress}%</p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <Upload className="w-6 h-6 mx-auto text-gray-400" />
                      <p className="text-sm text-gray-500 mt-1">Upload FTC DNC Data</p>
                    </div>
                  )}
                </div>
              </Label>
              <input
                id="ftc-upload"
                type="file"
                accept=".txt,.csv"
                className="hidden"
                onChange={handleFTCUpload}
                disabled={uploading}
                data-testid="ftc-upload-input"
              />
            </div>

            <Button 
              variant="outline" 
              size="sm" 
              className="w-full"
              onClick={() => window.open("https://telemarketing.donotcall.gov", "_blank")}
            >
              <Download className="w-4 h-4 mr-2" />
              Get FTC Data
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
          </CardContent>
        </Card>

        {/* Litigator List Card */}
        <Card className="border border-gray-200">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                TCPA Litigators
              </CardTitle>
              <Badge variant="destructive">{stats?.litigator_list?.count || 0}</Badge>
            </div>
            <CardDescription>Known TCPA plaintiff phone numbers</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-3xl font-bold text-red-600">
              {stats?.litigator_list?.count || 0}
              <span className="text-sm font-normal text-gray-500 ml-2">blocked numbers</span>
            </div>

            <p className="text-sm text-gray-500">
              Calls to these numbers are automatically blocked to prevent TCPA lawsuits ($500-$1,500 per violation).
            </p>

            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                className="flex-1"
                onClick={() => setShowAddLitigator(true)}
              >
                <Plus className="w-4 h-4 mr-1" />
                Add
              </Button>
              <Label htmlFor="litigator-upload" className="flex-1">
                <Button variant="outline" size="sm" className="w-full" asChild>
                  <span>
                    <Upload className="w-4 h-4 mr-1" />
                    Upload List
                  </span>
                </Button>
              </Label>
              <input
                id="litigator-upload"
                type="file"
                accept=".txt,.csv"
                className="hidden"
                onChange={handleLitigatorUpload}
                disabled={uploading}
              />
            </div>
          </CardContent>
        </Card>

        {/* Internal DNC Card */}
        <Card className="border border-gray-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Users className="w-5 h-5 text-purple-600" />
              Internal DNC List
            </CardTitle>
            <CardDescription>Opt-outs from your calls</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-3xl font-bold text-purple-600">
              {stats?.internal_dnc?.count || 0}
              <span className="text-sm font-normal text-gray-500 ml-2">numbers</span>
            </div>

            <p className="text-sm text-gray-500">
              Numbers automatically added when callers request removal during calls ("stop calling", "remove me").
            </p>

            <div className="bg-purple-50 p-3 rounded-lg">
              <p className="text-xs text-purple-800">
                <CheckCircle className="w-3 h-3 inline mr-1" />
                Auto-managed: Numbers are added instantly when opt-out phrases are detected during calls.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs for Detailed Views */}
      <Tabs defaultValue="litigators" className="mt-6">
        <TabsList>
          <TabsTrigger value="litigators">Litigator List</TabsTrigger>
          <TabsTrigger value="instructions">FTC Data Instructions</TabsTrigger>
        </TabsList>

        <TabsContent value="litigators">
          <Card>
            <CardHeader>
              <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                TCPA Litigator Phone Numbers
              </CardTitle>
              <CardDescription>
                Phone numbers associated with known TCPA plaintiff attorneys and serial litigators
              </CardDescription>
            </CardHeader>
            <CardContent>
              {litigators.length === 0 ? (
                <div className="text-center py-8">
                  <AlertTriangle className="w-12 h-12 text-gray-300 mx-auto" />
                  <p className="text-gray-500 mt-3">No litigators in the list yet</p>
                  <p className="text-sm text-gray-400 mt-1">
                    Add known TCPA plaintiff numbers to protect against lawsuits
                  </p>
                  <Button 
                    variant="outline" 
                    className="mt-4"
                    onClick={() => setShowAddLitigator(true)}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add First Litigator
                  </Button>
                </div>
              ) : (
                <ScrollArea className="h-[300px]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Phone Number</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Firm</TableHead>
                        <TableHead>Risk</TableHead>
                        <TableHead>Added</TableHead>
                        <TableHead></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {litigators.map((lit) => (
                        <TableRow key={lit.phone_number}>
                          <TableCell className="font-mono">{lit.phone_number}</TableCell>
                          <TableCell>{lit.name || "-"}</TableCell>
                          <TableCell>{lit.firm || "-"}</TableCell>
                          <TableCell>
                            <Badge variant="destructive">High Risk</Badge>
                          </TableCell>
                          <TableCell className="text-sm text-gray-500">
                            {lit.added_at ? new Date(lit.added_at).toLocaleDateString() : "-"}
                          </TableCell>
                          <TableCell>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleRemoveLitigator(lit.phone_number)}
                            >
                              <Trash2 className="w-4 h-4 text-red-500" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="instructions">
          <Card>
            <CardHeader>
              <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                How to Download FTC National DNC Data
              </CardTitle>
              <CardDescription>
                Free quarterly downloads from the official FTC registry
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>FTC Safe Harbor Requirement</AlertTitle>
                <AlertDescription>
                  To maintain safe harbor protection under TCPA, you must refresh your DNC data at least every 31 days.
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                <div className="flex gap-4 items-start">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold shrink-0">1</div>
                  <div>
                    <h4 className="font-semibold">Register as a Telemarketer</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      Visit <a href="https://telemarketing.donotcall.gov" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">telemarketing.donotcall.gov</a> and create an account. 
                      You'll need to register your organization and pay the annual fee ($74-$21,725 based on area codes).
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 items-start">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold shrink-0">2</div>
                  <div>
                    <h4 className="font-semibold">Download Area Code Files</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      Select the area codes you call and download the data files. Files are in TXT format with one phone number per line.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 items-start">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold shrink-0">3</div>
                  <div>
                    <h4 className="font-semibold">Upload to ColdCall.ai</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      Use the upload button above to import your FTC DNC data. You can upload multiple area code files - they'll be merged automatically.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 items-start">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold shrink-0">4</div>
                  <div>
                    <h4 className="font-semibold">Set a 31-Day Reminder</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      The system will warn you when your DNC data is due for refresh. Download fresh data from FTC monthly to maintain compliance.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Supported File Formats</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• <code className="bg-gray-200 px-1 rounded">.txt</code> - One phone number per line (FTC standard format)</li>
                  <li>• <code className="bg-gray-200 px-1 rounded">.csv</code> - CSV with phone numbers in first column</li>
                  <li>• Phone numbers: 10 digits (area code + number) or 11 digits (1 + area code + number)</li>
                </ul>
              </div>

              <Button 
                className="w-full"
                onClick={() => window.open("https://telemarketing.donotcall.gov", "_blank")}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Go to FTC Do Not Call Registry
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Litigator Dialog */}
      <Dialog open={showAddLitigator} onOpenChange={setShowAddLitigator}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add TCPA Litigator</DialogTitle>
            <DialogDescription>
              Add a phone number associated with a known TCPA plaintiff or serial litigator
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="lit-phone">Phone Number *</Label>
              <Input
                id="lit-phone"
                placeholder="(555) 123-4567"
                value={newLitigator.phone}
                onChange={(e) => setNewLitigator(prev => ({ ...prev, phone: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lit-name">Name (optional)</Label>
              <Input
                id="lit-name"
                placeholder="John Doe"
                value={newLitigator.name}
                onChange={(e) => setNewLitigator(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lit-firm">Law Firm (optional)</Label>
              <Input
                id="lit-firm"
                placeholder="Smith & Associates"
                value={newLitigator.firm}
                onChange={(e) => setNewLitigator(prev => ({ ...prev, firm: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lit-notes">Notes (optional)</Label>
              <Input
                id="lit-notes"
                placeholder="Known serial TCPA plaintiff"
                value={newLitigator.notes}
                onChange={(e) => setNewLitigator(prev => ({ ...prev, notes: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddLitigator(false)}>Cancel</Button>
            <Button onClick={handleAddLitigator} className="bg-red-600 hover:bg-red-700">
              Add to Blocked List
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DNCManagementPage;
