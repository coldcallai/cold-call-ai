import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import StatusBadge from "@/components/StatusBadge";
import {
  History, Phone, PhoneOff, Clock, Play, Download, RefreshCw, ChevronRight, CheckCircle, XCircle, User
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CallHistory = () => {
  const { token } = useAuth();
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCall, setSelectedCall] = useState(null);
  const [subscriptionFeatures, setSubscriptionFeatures] = useState(null);
  const [playingAudio, setPlayingAudio] = useState(null);
  const [loadingTranscript, setLoadingTranscript] = useState(false);
  const [transcriptData, setTranscriptData] = useState(null);

  const fetchCalls = async () => {
    try {
      const [callsRes, featuresRes] = await Promise.all([
        axios.get(`${API}/calls`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/subscription/features`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setCalls(callsRes.data);
      setSubscriptionFeatures(featuresRes.data.features);
    } catch (error) {
      toast.error("Failed to load calls");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, [token]);

  const playRecording = async (call) => {
    if (!subscriptionFeatures?.call_recording) {
      toast.error("Call recording requires Starter plan or higher");
      return;
    }
    
    if (!call.recording_url) {
      toast.error("No recording available for this call");
      return;
    }

    try {
      // Get audio stream
      const response = await axios.get(
        `${API}/calls/${call.id}/recording/stream`,
        { 
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      
      const audioUrl = URL.createObjectURL(response.data);
      const audio = new Audio(audioUrl);
      
      // Stop any currently playing audio
      if (playingAudio) {
        playingAudio.pause();
      }
      
      setPlayingAudio(audio);
      audio.play();
      
      audio.onended = () => {
        setPlayingAudio(null);
        URL.revokeObjectURL(audioUrl);
      };
      
      toast.success("Playing recording...");
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Recording access requires a higher subscription tier");
      } else {
        toast.error("Failed to play recording");
      }
    }
  };

  const stopRecording = () => {
    if (playingAudio) {
      playingAudio.pause();
      setPlayingAudio(null);
    }
  };

  const loadTranscript = async (call) => {
    if (!subscriptionFeatures?.call_transcription) {
      toast.error("Transcription requires Professional plan or higher");
      return;
    }

    setLoadingTranscript(true);
    try {
      const response = await axios.get(
        `${API}/calls/${call.id}/transcript`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTranscriptData(response.data);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Transcription requires Professional plan or higher");
      } else if (error.response?.status === 404) {
        toast.info("No transcript available. Request one below.");
      } else {
        toast.error("Failed to load transcript");
      }
    } finally {
      setLoadingTranscript(false);
    }
  };

  const requestTranscription = async (call) => {
    try {
      await axios.post(
        `${API}/calls/${call.id}/transcribe`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Transcription requested! Check back in a minute.");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to request transcription");
    }
  };

  const openCallDetails = async (call) => {
    setSelectedCall(call);
    setTranscriptData(null);
    
    // Auto-load transcript if user has access and call has one
    if (subscriptionFeatures?.call_transcription && call.full_transcript) {
      loadTranscript(call);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="call-history-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            Call History
          </h1>
          <p className="text-gray-500 mt-1">View recordings, transcripts, and qualification results</p>
          <p className="text-xs text-blue-600 mt-1 bg-blue-50 px-2 py-1 rounded inline-block">
            💡 Click any call to see the full transcript, qualification score, and play the recording.
          </p>
        </div>
        
        {/* Feature badges */}
        <div className="flex items-center gap-2">
          {subscriptionFeatures?.call_recording ? (
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
              <CheckCircle className="w-3 h-3 mr-1" /> Recordings
            </Badge>
          ) : (
            <Badge variant="outline" className="bg-gray-50 text-gray-500">
              Recordings (Starter+)
            </Badge>
          )}
          {subscriptionFeatures?.call_transcription ? (
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
              <CheckCircle className="w-3 h-3 mr-1" /> Transcripts
            </Badge>
          ) : (
            <Badge variant="outline" className="bg-gray-50 text-gray-500">
              Transcripts (Pro+)
            </Badge>
          )}
        </div>
      </div>

      <Card className="bg-white border border-gray-200 shadow-sm">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 space-y-4">
              {[1,2,3].map(i => <Skeleton key={i} className="h-16" />)}
            </div>
          ) : calls.length === 0 ? (
            <div className="p-12 text-center">
              <History className="w-16 h-16 text-gray-300 mx-auto" />
              <p className="text-gray-500 mt-4">No calls yet. Start a campaign to make calls.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Call ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Recording</TableHead>
                  <TableHead>Qualification</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {calls.map((call) => (
                  <TableRow key={call.id} data-testid={`call-row-${call.id}`}>
                    <TableCell className="font-mono text-sm">{call.id.slice(0, 8)}...</TableCell>
                    <TableCell>
                      <StatusBadge status={call.status} />
                    </TableCell>
                    <TableCell>{call.duration_seconds}s</TableCell>
                    <TableCell>
                      {call.recording_url ? (
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8 w-8 p-0"
                            onClick={() => playingAudio ? stopRecording() : playRecording(call)}
                            disabled={!subscriptionFeatures?.call_recording}
                          >
                            {playingAudio ? (
                              <Pause className="w-4 h-4 text-blue-600" />
                            ) : (
                              <Play className="w-4 h-4 text-blue-600" />
                            )}
                          </Button>
                          {call.full_transcript && (
                            <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700">
                              Transcript
                            </Badge>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {call.qualification_result ? (
                        <div className="flex items-center gap-2">
                          {call.qualification_result.is_qualified ? (
                            <CheckCircle className="w-4 h-4 text-emerald-600" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-500" />
                          )}
                          <span className="text-sm">
                            Score: {call.qualification_result.score}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {new Date(call.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        data-testid={`view-call-${call.id}`}
                        onClick={() => openCallDetails(call)}
                      >
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Call Details Dialog - Enhanced with Recording & Transcript */}
      <Dialog open={!!selectedCall} onOpenChange={() => { setSelectedCall(null); setTranscriptData(null); stopRecording(); }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Call Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedCall && (
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Status</p>
                  <StatusBadge status={selectedCall.status} />
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Duration</p>
                  <p className="font-semibold">{selectedCall.duration_seconds}s</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Answered By</p>
                  <p className="font-semibold capitalize">{selectedCall.answered_by || "Unknown"}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Date</p>
                  <p className="font-semibold">{new Date(selectedCall.created_at).toLocaleString()}</p>
                </div>
              </div>

              {/* Recording Player */}
              {selectedCall.recording_url && subscriptionFeatures?.call_recording && (
                <div className="p-4 border border-blue-200 rounded-lg bg-blue-50/50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-100 rounded-full">
                        <Phone className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">Call Recording</p>
                        <p className="text-sm text-gray-500">
                          {selectedCall.recording_duration_seconds || selectedCall.duration_seconds}s duration
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={() => playingAudio ? stopRecording() : playRecording(selectedCall)}
                      className="gap-2"
                    >
                      {playingAudio ? (
                        <>
                          <Pause className="w-4 h-4" /> Stop
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4" /> Play Recording
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )}

              {/* Qualification Result */}
              {selectedCall.qualification_result && (
                <div className="p-4 border border-gray-200 rounded-lg">
                  <h4 className="font-semibold mb-3">Qualification Result</h4>
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div>
                      <p className="text-gray-500">Qualified</p>
                      <p className={`font-semibold ${selectedCall.qualification_result.is_qualified ? 'text-emerald-600' : 'text-red-600'}`}>
                        {selectedCall.qualification_result.is_qualified ? 'Yes' : 'No'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Decision Maker</p>
                      <p className="font-semibold">
                        {selectedCall.qualification_result.is_decision_maker ? 'Yes' : 'No'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Interest Level</p>
                      <p className="font-semibold">{selectedCall.qualification_result.interest_level}/10</p>
                    </div>
                  </div>
                  <div className="mt-3">
                    <p className="text-gray-500 text-sm">Score</p>
                    <Progress value={selectedCall.qualification_result.score} className="h-2 mt-1" />
                    <p className="text-right text-sm font-semibold mt-1">{selectedCall.qualification_result.score}/100</p>
                  </div>
                </div>
              )}

              {/* Full Transcript (Whisper) */}
              {subscriptionFeatures?.call_transcription && (
                <div className="border border-purple-200 rounded-lg overflow-hidden">
                  <div className="p-4 bg-purple-50 border-b border-purple-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-purple-900">Full Transcript</h4>
                        {selectedCall.transcription_status === "processing" && (
                          <Badge className="bg-yellow-100 text-yellow-800">Processing...</Badge>
                        )}
                      </div>
                      {!transcriptData && !loadingTranscript && (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => loadTranscript(selectedCall)}
                            disabled={!selectedCall.full_transcript}
                          >
                            Load Transcript
                          </Button>
                          {!selectedCall.full_transcript && selectedCall.recording_url && (
                            <Button
                              size="sm"
                              onClick={() => requestTranscription(selectedCall)}
                            >
                              Request Transcription
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="p-4 bg-white">
                    {loadingTranscript ? (
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-4 w-5/6" />
                      </div>
                    ) : transcriptData ? (
                      <div className="space-y-4">
                        {/* Full text */}
                        <div className="p-3 bg-gray-50 rounded-lg">
                          <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                            {transcriptData.full_transcript}
                          </p>
                        </div>
                        
                        {/* Timestamped segments */}
                        {transcriptData.segments && transcriptData.segments.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 mb-2">Timestamped Segments</p>
                            <ScrollArea className="h-[150px] border rounded-lg p-2">
                              <div className="space-y-2">
                                {transcriptData.segments.map((segment, idx) => (
                                  <div key={idx} className="flex gap-3 text-sm">
                                    <span className="text-gray-400 font-mono w-20 flex-shrink-0">
                                      {Math.floor(segment.start / 60)}:{String(Math.floor(segment.start % 60)).padStart(2, '0')}
                                    </span>
                                    <span className="text-gray-700">{segment.text}</span>
                                  </div>
                                ))}
                              </div>
                            </ScrollArea>
                          </div>
                        )}
                      </div>
                    ) : selectedCall.full_transcript ? (
                      <p className="text-sm text-gray-500">Click "Load Transcript" to view.</p>
                    ) : (
                      <p className="text-sm text-gray-500">
                        No transcript available. 
                        {selectedCall.recording_url ? " Click 'Request Transcription' to generate one." : " No recording found."}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* AI Conversation Transcript (existing) */}
              {selectedCall.transcript && selectedCall.transcript.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-3">AI Conversation Log</h4>
                  <ScrollArea className="h-[200px] border border-gray-200 rounded-lg p-4">
                    <div className="space-y-3">
                      {selectedCall.transcript.map((msg, idx) => (
                        <div key={idx} className={`flex gap-3 ${msg.role === 'ai' ? '' : 'flex-row-reverse'}`}>
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                            msg.role === 'ai' ? 'bg-blue-100' : 'bg-gray-100'
                          }`}>
                            {msg.role === 'ai' ? (
                              <Phone className="w-4 h-4 text-blue-600" />
                            ) : (
                              <User className="w-4 h-4 text-gray-600" />
                            )}
                          </div>
                          <div className={`p-3 rounded-lg max-w-[80%] ${
                            msg.role === 'ai' ? 'bg-blue-50' : 'bg-gray-50'
                          }`}>
                            <p className="text-sm">{msg.text}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Settings Page

export default CallHistory;
