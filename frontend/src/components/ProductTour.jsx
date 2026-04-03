import { useEffect, useState } from "react";
import { driver } from "driver.js";
import "driver.js/dist/driver.css";
import { HelpCircle, Play, X } from "lucide-react";
import { Button } from "./ui/button";

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Define tours for different pages/features
const TOURS = {
  dashboard: {
    name: "Dashboard Overview",
    description: "Learn how to navigate your sales funnel",
    steps: [
      {
        element: '[data-testid="funnel-stats"]',
        popover: {
          title: "Your Sales Funnel",
          description: "Track leads as they move through your pipeline — from discovery to qualified to booked meetings.",
          side: "bottom"
        }
      },
      {
        element: '[data-testid="campaign-card"]',
        popover: {
          title: "Active Campaigns",
          description: "Each campaign runs your AI agents on autopilot. Click any campaign to see detailed analytics.",
          side: "right"
        }
      },
      {
        element: '[data-testid="recent-calls"]',
        popover: {
          title: "Recent Calls",
          description: "Monitor your AI's performance in real-time. Listen to recordings and see call outcomes.",
          side: "top"
        }
      }
    ]
  },
  agents: {
    name: "Setting Up AI Agents",
    description: "Configure your virtual sales team",
    steps: [
      {
        element: '[data-testid="create-agent-btn"]',
        popover: {
          title: "Create Your First Agent",
          description: "Click here to create an AI agent. You'll define their voice, script, and personality.",
          side: "bottom"
        }
      },
      {
        element: '[data-testid="agent-card"]',
        popover: {
          title: "Your AI Agents",
          description: "Each agent can have different voices, scripts, and target audiences. Think of them as specialized salespeople.",
          side: "right"
        }
      },
      {
        element: '[data-testid="voice-settings-btn"]',
        popover: {
          title: "Voice Settings",
          description: "Click the gear icon to customize your agent's voice. Choose presets or fine-tune stability, similarity, and style.",
          side: "left"
        }
      },
      {
        element: '[data-testid="clone-voice-btn"]',
        popover: {
          title: "Clone Your Voice",
          description: "Upload audio samples to create a custom AI voice that sounds like you or your best salesperson!",
          side: "left"
        }
      }
    ]
  },
  voiceSettings: {
    name: "Voice Tuning Guide",
    description: "Make your AI sound natural",
    steps: [
      {
        popover: {
          title: "Voice Tuning 101",
          description: "Your AI's voice can make or break a call. Let's learn how to tune it perfectly.",
          side: "center"
        }
      },
      {
        popover: {
          title: "Quick Presets",
          description: "Start with a preset: Professional (calm B2B), Conversational (friendly), or Energetic (promotions).",
          side: "center"
        }
      },
      {
        popover: {
          title: "Stability Slider",
          description: "LOW = More expressive, emotional, human-like (but may vary between calls). HIGH = Consistent, robotic (same every time). For sales calls, 0.4-0.6 is the sweet spot.",
          side: "center"
        }
      },
      {
        popover: {
          title: "Similarity Slider",
          description: "How close to the original voice. Keep at 0.7-0.8 for clarity. Only lower if the voice sounds too artificial.",
          side: "center"
        }
      },
      {
        popover: {
          title: "Style Slider",
          description: "How animated the delivery is. LOW = Calm, measured. HIGH = Energetic, enthusiastic. Match to your campaign type!",
          side: "center"
        }
      },
      {
        popover: {
          title: "Always Preview!",
          description: "Click 'Preview Voice' before saving. Your AI will speak a sample so you can hear exactly how it sounds.",
          side: "center"
        }
      }
    ]
  },
  campaigns: {
    name: "Creating Campaigns",
    description: "Launch your first AI calling campaign",
    steps: [
      {
        element: '[data-testid="new-campaign-btn"]',
        popover: {
          title: "Create a Campaign",
          description: "Campaigns connect your AI agents to your leads. Click here to start one.",
          side: "bottom"
        }
      },
      {
        element: '[data-testid="campaign-name-input"]',
        popover: {
          title: "Name Your Campaign",
          description: "Choose a descriptive name like 'Q1 SaaS Outreach' or 'Restaurant Owners NYC'.",
          side: "right"
        }
      },
      {
        element: '[data-testid="agent-select"]',
        popover: {
          title: "Assign an Agent",
          description: "Select which AI agent will make these calls. Different agents = different scripts and voices.",
          side: "right"
        }
      },
      {
        element: '[data-testid="calls-per-day"]',
        popover: {
          title: "Daily Call Limit",
          description: "How many calls per day? Start with 50-100 to test, then scale up once you see results.",
          side: "right"
        }
      }
    ]
  },
  leads: {
    name: "Lead Discovery",
    description: "Find high-intent prospects",
    steps: [
      {
        element: '[data-testid="discover-leads-btn"]',
        popover: {
          title: "AI Lead Discovery",
          description: "Our AI finds businesses actively looking for solutions like yours. Click to discover new leads.",
          side: "bottom"
        }
      },
      {
        element: '[data-testid="industry-filter"]',
        popover: {
          title: "Target Industries",
          description: "Filter by industry to find the most relevant prospects for your offering.",
          side: "right"
        }
      },
      {
        element: '[data-testid="intent-signals"]',
        popover: {
          title: "Intent Signals",
          description: "We track buying signals like job postings, tech stack changes, and funding rounds to find ready-to-buy leads.",
          side: "left"
        }
      }
    ]
  }
};

// Video tutorials configuration (placeholder URLs - replace with real Loom/YouTube links)
const VIDEO_TUTORIALS = {
  dashboard: {
    title: "Dashboard Walkthrough",
    duration: "2:30",
    thumbnail: "https://placehold.co/320x180/1e40af/ffffff?text=Dashboard+Tour",
    videoUrl: null // Replace with Loom/YouTube embed URL
  },
  agents: {
    title: "Setting Up AI Agents",
    duration: "4:15",
    thumbnail: "https://placehold.co/320x180/7c3aed/ffffff?text=Agent+Setup",
    videoUrl: null
  },
  voiceSettings: {
    title: "Voice Tuning Masterclass",
    duration: "3:45",
    thumbnail: "https://placehold.co/320x180/059669/ffffff?text=Voice+Tuning",
    videoUrl: null
  },
  campaigns: {
    title: "Launching Your First Campaign",
    duration: "5:00",
    thumbnail: "https://placehold.co/320x180/dc2626/ffffff?text=Campaign+Launch",
    videoUrl: null
  },
  leads: {
    title: "AI Lead Discovery",
    duration: "3:20",
    thumbnail: "https://placehold.co/320x180/ca8a04/ffffff?text=Lead+Discovery",
    videoUrl: null
  }
};

// Floating Help Button Component
export const HelpButton = ({ currentPage = "dashboard" }) => {
  const [showMenu, setShowMenu] = useState(false);
  const [showVideoModal, setShowVideoModal] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState(null);

  const startTour = (tourKey) => {
    setShowMenu(false);
    const tour = TOURS[tourKey];
    if (!tour) return;

    const driverObj = driver({
      showProgress: true,
      showButtons: ['next', 'previous', 'close'],
      steps: tour.steps,
      popoverClass: 'driverjs-theme',
      onDestroyStarted: () => {
        driverObj.destroy();
      }
    });

    driverObj.drive();
  };

  const openVideo = (videoKey) => {
    const video = VIDEO_TUTORIALS[videoKey];
    if (video) {
      setSelectedVideo(video);
      setShowVideoModal(true);
      setShowMenu(false);
    }
  };

  return (
    <>
      {/* Floating Help Button */}
      <div className="fixed bottom-6 right-6 z-50">
        <Button
          onClick={() => setShowMenu(!showMenu)}
          className="w-14 h-14 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg shadow-blue-500/30"
        >
          {showMenu ? <X className="w-6 h-6" /> : <HelpCircle className="w-6 h-6" />}
        </Button>

        {/* Help Menu */}
        {showMenu && (
          <div className="absolute bottom-16 right-0 w-80 bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden animate-in slide-in-from-bottom-5 duration-200">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4">
              <h3 className="text-white font-semibold">Need Help?</h3>
              <p className="text-blue-100 text-sm">Choose a guide or video tutorial</p>
            </div>

            <div className="p-3 space-y-2 max-h-96 overflow-y-auto">
              {/* Interactive Tours */}
              <div className="mb-3">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2">
                  Interactive Walkthroughs
                </p>
                {Object.entries(TOURS).map(([key, tour]) => (
                  <button
                    key={key}
                    onClick={() => startTour(key)}
                    className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-blue-50 transition-colors text-left"
                  >
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Play className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 text-sm">{tour.name}</p>
                      <p className="text-xs text-gray-500">{tour.description}</p>
                    </div>
                  </button>
                ))}
              </div>

              {/* Video Tutorials */}
              <div className="border-t pt-3">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2">
                  Video Tutorials
                </p>
                {Object.entries(VIDEO_TUTORIALS).map(([key, video]) => (
                  <button
                    key={key}
                    onClick={() => openVideo(key)}
                    className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-purple-50 transition-colors text-left"
                  >
                    <div className="relative w-16 h-10 rounded overflow-hidden flex-shrink-0 bg-gray-200">
                      <img 
                        src={video.thumbnail} 
                        alt={video.title}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                        <Play className="w-4 h-4 text-white fill-white" />
                      </div>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 text-sm">{video.title}</p>
                      <p className="text-xs text-gray-500">{video.duration}</p>
                    </div>
                  </button>
                ))}
              </div>

              {/* Help Center Link */}
              <div className="border-t pt-3">
                <a
                  href="/help"
                  className="w-full flex items-center justify-center gap-2 p-3 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors text-gray-700 font-medium text-sm"
                >
                  View Full Help Center
                </a>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Video Modal */}
      {showVideoModal && selectedVideo && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-xl w-full max-w-3xl overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-semibold text-gray-900">{selectedVideo.title}</h3>
              <button
                onClick={() => setShowVideoModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="aspect-video bg-gray-900 flex items-center justify-center">
              {selectedVideo.videoUrl ? (
                <iframe
                  src={selectedVideo.videoUrl}
                  className="w-full h-full"
                  allowFullScreen
                  allow="autoplay; encrypted-media"
                />
              ) : (
                <div className="text-center text-white">
                  <Play className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">Video Coming Soon</p>
                  <p className="text-sm text-gray-400 mt-2">
                    Use the interactive walkthrough in the meantime!
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Hook to start a specific tour programmatically
export const useProductTour = () => {
  const startTour = (tourKey) => {
    const tour = TOURS[tourKey];
    if (!tour) return;

    const driverObj = driver({
      showProgress: true,
      showButtons: ['next', 'previous', 'close'],
      steps: tour.steps,
      popoverClass: 'driverjs-theme'
    });

    driverObj.drive();
  };

  return { startTour, tours: TOURS };
};

export default HelpButton;
