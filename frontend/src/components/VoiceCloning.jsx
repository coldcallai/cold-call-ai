import { useState, useEffect, useRef } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Slider } from "./ui/slider";
import { 
  Mic, Upload, Play, Pause, Trash2, Plus, Volume2, 
  CheckCircle, Loader2, AlertCircle, X 
} from "lucide-react";
import { toast } from "sonner";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const VoiceCloneModal = ({ isOpen, onClose, onVoiceCloned }) => {
  const [step, setStep] = useState(1); // 1: upload, 2: preview, 3: done
  const [files, setFiles] = useState([]);
  const [voiceName, setVoiceName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length + files.length > 5) {
      toast.error("Maximum 5 files allowed");
      return;
    }
    
    // Validate file types
    const validFiles = selectedFiles.filter(f => 
      f.type.includes("audio") || f.name.endsWith(".mp3") || f.name.endsWith(".wav")
    );
    
    if (validFiles.length !== selectedFiles.length) {
      toast.error("Only MP3 and WAV files are supported");
    }
    
    setFiles([...files, ...validFiles]);
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleClone = async () => {
    if (!voiceName.trim()) {
      toast.error("Please enter a name for your voice");
      return;
    }
    if (files.length === 0) {
      toast.error("Please upload at least one audio file");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    files.forEach(f => formData.append("files", f));
    formData.append("voice_name", voiceName);
    formData.append("description", description);

    try {
      const response = await fetch(`${API_URL}/api/voices/clone`, {
        method: "POST",
        credentials: "include",
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to clone voice");
      }

      toast.success("Voice cloned successfully!");
      setStep(3);
      onVoiceCloned(data);
    } catch (error) {
      console.error("Clone failed:", error);
      toast.error(error.message || "Failed to clone voice");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg bg-white">
        <CardHeader className="relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <Mic className="w-5 h-5 text-white" />
            </div>
            <div>
              <CardTitle>Clone Your Voice</CardTitle>
              <CardDescription>Upload audio samples to create a custom AI voice</CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {step === 1 && (
            <>
              {/* Voice Name */}
              <div className="space-y-2">
                <Label>Voice Name</Label>
                <Input
                  placeholder="e.g., My Sales Voice"
                  value={voiceName}
                  onChange={(e) => setVoiceName(e.target.value)}
                />
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label>Description (optional)</Label>
                <Input
                  placeholder="e.g., Energetic, professional tone"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              {/* File Upload */}
              <div className="space-y-2">
                <Label>Audio Samples (1-5 files)</Label>
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center cursor-pointer hover:border-purple-300 hover:bg-purple-50/50 transition-colors"
                >
                  <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">
                    Click to upload MP3 or WAV files
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    At least 30 seconds total, clear audio, no background noise
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*,.mp3,.wav"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>

              {/* Selected Files */}
              {files.length > 0 && (
                <div className="space-y-2">
                  <Label>Selected Files ({files.length}/5)</Label>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {files.map((file, index) => (
                      <div key={index} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Volume2 className="w-4 h-4 text-purple-500" />
                          <span className="text-sm text-gray-700 truncate max-w-[200px]">{file.name}</span>
                        </div>
                        <button
                          onClick={() => removeFile(index)}
                          className="text-gray-400 hover:text-red-500"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tips */}
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-sm text-amber-800 font-medium mb-1">Tips for best results:</p>
                <ul className="text-xs text-amber-700 space-y-1">
                  <li>• Use clear audio without background noise</li>
                  <li>• Speak naturally with variety in tone</li>
                  <li>• Include at least 30 seconds of speech</li>
                  <li>• Multiple samples improve quality</li>
                </ul>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <Button variant="outline" onClick={onClose} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={handleClone}
                  disabled={loading || files.length === 0 || !voiceName.trim()}
                  className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Cloning...
                    </>
                  ) : (
                    <>
                      <Mic className="w-4 h-4 mr-2" />
                      Clone Voice
                    </>
                  )}
                </Button>
              </div>
            </>
          )}

          {step === 3 && (
            <div className="text-center py-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Voice Cloned Successfully!</h3>
              <p className="text-gray-600 text-sm mb-4">
                Your custom voice "{voiceName}" is now ready to use with your AI agents.
              </p>
              <Button onClick={onClose} className="bg-green-600 hover:bg-green-700 text-white">
                Done
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Voice presets for one-click setup
const VOICE_PRESETS = {
  professional: {
    name: "Professional",
    description: "Calm, clear, and trustworthy — ideal for B2B sales",
    stability: 0.7,
    similarityBoost: 0.75,
    style: 0.2,
    icon: "💼"
  },
  conversational: {
    name: "Conversational", 
    description: "Natural and friendly — great for warm leads",
    stability: 0.5,
    similarityBoost: 0.75,
    style: 0.4,
    icon: "💬"
  },
  energetic: {
    name: "Energetic",
    description: "Upbeat and enthusiastic — perfect for promotions",
    stability: 0.35,
    similarityBoost: 0.8,
    style: 0.6,
    icon: "⚡"
  }
};

const VoiceSettingsModal = ({ isOpen, onClose, agent, onSave }) => {
  const [voiceType, setVoiceType] = useState(agent?.voice_type || "preset");
  const [selectedVoiceId, setSelectedVoiceId] = useState(agent?.preset_voice_id || agent?.cloned_voice_id || "21m00Tcm4TlvDq8ikWAM");
  const [presetVoices, setPresetVoices] = useState([]);
  const [clonedVoices, setClonedVoices] = useState([]);
  const [stability, setStability] = useState(agent?.voice_settings?.stability || 0.5);
  const [similarityBoost, setSimilarityBoost] = useState(agent?.voice_settings?.similarity_boost || 0.75);
  const [style, setStyle] = useState(agent?.voice_settings?.style || 0.3);
  const [activePreset, setActivePreset] = useState(null);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewAudio, setPreviewAudio] = useState(null);
  const audioRef = useRef(null);

  // Apply a preset
  const applyPreset = (presetKey) => {
    const preset = VOICE_PRESETS[presetKey];
    setStability(preset.stability);
    setSimilarityBoost(preset.similarityBoost);
    setStyle(preset.style);
    setActivePreset(presetKey);
  };

  useEffect(() => {
    if (isOpen) {
      fetchVoices();
    }
  }, [isOpen]);

  const fetchVoices = async () => {
    try {
      const [presetsRes, clonedRes] = await Promise.all([
        fetch(`${API_URL}/api/voices/presets`, { credentials: "include" }),
        fetch(`${API_URL}/api/voices/cloned`, { credentials: "include" })
      ]);
      
      if (presetsRes.ok) {
        const data = await presetsRes.json();
        setPresetVoices(data.voices);
      }
      if (clonedRes.ok) {
        const data = await clonedRes.json();
        setClonedVoices(data.voices);
      }
    } catch (error) {
      console.error("Failed to fetch voices:", error);
    }
  };

  const handlePreview = async () => {
    setPreviewLoading(true);
    const formData = new FormData();
    formData.append("text", "Hi, this is a preview of how I'll sound on your sales calls. I'm ready to help you close more deals!");
    formData.append("voice_id", selectedVoiceId);

    try {
      const response = await fetch(`${API_URL}/api/voices/preview`, {
        method: "POST",
        credentials: "include",
        body: formData
      });

      if (!response.ok) throw new Error("Preview failed");

      const data = await response.json();
      setPreviewAudio(data.audio);
      
      if (audioRef.current) {
        audioRef.current.src = data.audio;
        audioRef.current.play();
      }
    } catch (error) {
      toast.error("Failed to generate preview");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    const formData = new FormData();
    formData.append("voice_type", voiceType);
    formData.append("voice_id", selectedVoiceId);
    formData.append("stability", stability);
    formData.append("similarity_boost", similarityBoost);
    formData.append("style", style);

    try {
      const response = await fetch(`${API_URL}/api/agents/${agent.id}/voice`, {
        method: "PUT",
        credentials: "include",
        body: formData
      });

      if (!response.ok) throw new Error("Failed to save");

      toast.success("Voice settings saved!");
      onSave();
      onClose();
    } catch (error) {
      toast.error("Failed to save voice settings");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg bg-white max-h-[90vh] overflow-y-auto">
        <CardHeader className="relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
          <CardTitle>Voice Settings - {agent?.name}</CardTitle>
          <CardDescription>Configure the AI voice for this agent</CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Quick Start Guide */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm font-medium text-blue-900 mb-2">Quick Setup Guide</p>
            <p className="text-xs text-blue-700">
              1. Choose a voice type below (Preset or your Cloned voice)<br/>
              2. Select a Quick Preset OR fine-tune with sliders<br/>
              3. Click "Preview Voice" to hear it before saving
            </p>
          </div>

          {/* Voice Type Selection */}
          <div className="space-y-3">
            <Label>Voice Type</Label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setVoiceType("preset")}
                className={`p-4 rounded-lg border-2 transition-all ${
                  voiceType === "preset" 
                    ? "border-blue-500 bg-blue-50" 
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <Volume2 className={`w-6 h-6 mx-auto mb-2 ${voiceType === "preset" ? "text-blue-600" : "text-gray-400"}`} />
                <p className={`font-medium ${voiceType === "preset" ? "text-blue-900" : "text-gray-700"}`}>Preset Voice</p>
                <p className="text-xs text-gray-500 mt-1">ElevenLabs library</p>
              </button>
              <button
                onClick={() => setVoiceType("cloned")}
                className={`p-4 rounded-lg border-2 transition-all ${
                  voiceType === "cloned" 
                    ? "border-purple-500 bg-purple-50" 
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <Mic className={`w-6 h-6 mx-auto mb-2 ${voiceType === "cloned" ? "text-purple-600" : "text-gray-400"}`} />
                <p className={`font-medium ${voiceType === "cloned" ? "text-purple-900" : "text-gray-700"}`}>Cloned Voice</p>
                <p className="text-xs text-gray-500 mt-1">Your custom voice</p>
              </button>
            </div>
          </div>

          {/* Voice Selection */}
          <div className="space-y-3">
            <Label>{voiceType === "preset" ? "Select Preset Voice" : "Select Cloned Voice"}</Label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
              {voiceType === "preset" ? (
                presetVoices.map(voice => (
                  <button
                    key={voice.id}
                    onClick={() => setSelectedVoiceId(voice.id)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      selectedVoiceId === voice.id
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:border-blue-200"
                    }`}
                  >
                    <p className="font-medium text-sm">{voice.name}</p>
                    <p className="text-xs text-gray-500">{voice.description}</p>
                  </button>
                ))
              ) : clonedVoices.length > 0 ? (
                clonedVoices.map(voice => (
                  <button
                    key={voice.id}
                    onClick={() => setSelectedVoiceId(voice.elevenlabs_voice_id)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      selectedVoiceId === voice.elevenlabs_voice_id
                        ? "border-purple-500 bg-purple-50"
                        : "border-gray-200 hover:border-purple-200"
                    }`}
                  >
                    <p className="font-medium text-sm">{voice.name}</p>
                    <p className="text-xs text-gray-500">{voice.description || "Custom cloned voice"}</p>
                  </button>
                ))
              ) : (
                <div className="col-span-2 text-center py-6 text-gray-500">
                  <Mic className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">No cloned voices yet</p>
                  <p className="text-xs">Create one from the Agents page</p>
                </div>
              )}
            </div>
          </div>

          {/* Voice Tuning */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Voice Tuning</Label>
              <span className="text-xs text-gray-400">Or choose a quick preset below</span>
            </div>

            {/* Quick Presets */}
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(VOICE_PRESETS).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() => applyPreset(key)}
                  className={`p-3 rounded-lg border-2 text-center transition-all ${
                    activePreset === key
                      ? "border-green-500 bg-green-50"
                      : "border-gray-200 hover:border-green-300 hover:bg-green-50/50"
                  }`}
                >
                  <span className="text-xl">{preset.icon}</span>
                  <p className={`text-xs font-medium mt-1 ${activePreset === key ? "text-green-700" : "text-gray-700"}`}>
                    {preset.name}
                  </p>
                </button>
              ))}
            </div>
            <p className="text-xs text-center text-gray-500 -mt-1">
              Click a preset to auto-fill recommended settings
            </p>

            {/* Stability Slider */}
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Stability</span>
                <span className="text-sm font-mono bg-gray-100 px-2 py-0.5 rounded">{stability.toFixed(2)}</span>
              </div>
              <Slider
                value={[stability]}
                onValueChange={([v]) => { setStability(v); setActivePreset(null); }}
                max={1}
                step={0.05}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400">
                <span>More expressive</span>
                <span>More consistent</span>
              </div>
              <p className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                <strong>Tip:</strong> Use 0.3-0.5 for natural conversations, 0.7+ for scripted messages
              </p>
            </div>

            {/* Similarity Slider */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Similarity</span>
                <span className="text-sm font-mono bg-gray-100 px-2 py-0.5 rounded">{similarityBoost.toFixed(2)}</span>
              </div>
              <Slider
                value={[similarityBoost]}
                onValueChange={([v]) => { setSimilarityBoost(v); setActivePreset(null); }}
                max={1}
                step={0.05}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400">
                <span>More variation</span>
                <span>Closer to original</span>
              </div>
              <p className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                <strong>Tip:</strong> Keep at 0.7-0.8 for best clarity. Lower only if voice sounds too robotic.
              </p>
            </div>

            {/* Style Slider */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Style</span>
                <span className="text-sm font-mono bg-gray-100 px-2 py-0.5 rounded">{style.toFixed(2)}</span>
              </div>
              <Slider
                value={[style]}
                onValueChange={([v]) => { setStyle(v); setActivePreset(null); }}
                max={1}
                step={0.05}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400">
                <span>Calm delivery</span>
                <span>Animated delivery</span>
              </div>
              <p className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                <strong>Tip:</strong> Use 0.2-0.4 for sales calls, 0.5+ for promotional/energetic campaigns
              </p>
            </div>
          </div>

          {/* Preview */}
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={handlePreview}
              disabled={previewLoading}
              className="flex-1"
            >
              {previewLoading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Play className="w-4 h-4 mr-2" />
              )}
              Preview Voice
            </Button>
            <audio ref={audioRef} className="hidden" />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <Button variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={loading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save Settings"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export { VoiceCloneModal, VoiceSettingsModal };
