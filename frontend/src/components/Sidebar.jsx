import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import {
  Phone, Users, Target, Calendar, Settings, LayoutDashboard,
  History, Search, Package, LogOut, BarChart3, X, TrendingUp,
  Database, Shield, Rocket, User, Filter, Star
} from "lucide-react";

const Sidebar = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const navItems = [
    { path: "/app/getting-started", icon: Rocket, label: "Getting Started" },
    { path: "/app", icon: Filter, label: "Funnel" },
    { path: "/app/usage", icon: BarChart3, label: "Usage" },
    { path: "/app/leads", icon: Search, label: "Lead Discovery" },
    { path: "/app/campaigns", icon: Target, label: "Campaigns" },
    { path: "/app/agents", icon: Users, label: "Agents" },
    { path: "/app/bookings", icon: Calendar, label: "Bookings" },
    { path: "/app/calls", icon: History, label: "Call History" },
    { path: "/app/reviews", icon: Star, label: "Review Requests" },
    { path: "/app/analytics", icon: TrendingUp, label: "Analytics" },
    { path: "/app/integrations", icon: Database, label: "CRM Integrations" },
    { path: "/app/compliance", icon: Shield, label: "Compliance" },
    { path: "/app/packs", icon: Package, label: "Credit Packs" },
    { path: "/app/settings", icon: Settings, label: "Settings" },
  ];

  const handleLogout = async () => {
    await logout();
    window.location.href = "/";
  };

  // Close mobile menu when route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const SidebarContent = () => (
    <>
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
            <Phone className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              IntentBrain.ai
            </h1>
            <p className="text-xs text-gray-500">AI Sales Automation</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-4 overflow-y-auto">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || 
              (item.path === "/app" && location.pathname === "/app/");
            const Icon = item.icon;
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-blue-50 text-blue-600 border border-blue-100"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      
      {/* User Info & Credits */}
      {user && (
        <div className="p-4 border-t border-gray-100">
          <div className="bg-gradient-to-r from-cyan-50 to-teal-50 border border-cyan-200 rounded-lg p-3 mb-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-full flex items-center justify-center">
                {user.picture ? (
                  <img src={user.picture} alt="" className="w-8 h-8 rounded-full" />
                ) : (
                  <User className="w-4 h-4 text-white" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user.name}</p>
                <p className="text-xs text-gray-500 truncate">{user.email}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-center">
              <div className="bg-white/60 rounded-md p-2">
                <p className="text-lg font-bold text-cyan-600">{user.lead_credits_remaining || 0}</p>
                <p className="text-[10px] text-gray-500">Lead Credits</p>
              </div>
              <div className="bg-white/60 rounded-md p-2">
                <p className="text-lg font-bold text-teal-600">{user.call_credits_remaining || 0}</p>
                <p className="text-[10px] text-gray-500">Call Credits</p>
              </div>
            </div>
          </div>
          
          <Button 
            onClick={handleLogout}
            variant="ghost"
            className="w-full justify-start text-gray-600 hover:text-red-600 hover:bg-red-50"
            data-testid="logout-btn"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Sign Out
          </Button>
        </div>
      )}
    </>
  );

  return (
    <>
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Phone className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
            IntentBrain.ai
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setMobileMenuOpen(prev => !prev);
          }}
          data-testid="mobile-menu-toggle"
          className="p-2"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <LayoutDashboard className="w-6 h-6" />}
        </Button>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside className={`
        lg:hidden fixed top-0 left-0 h-full w-72 bg-white z-50 transform transition-transform duration-300 ease-in-out flex flex-col
        ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <SidebarContent />
      </aside>

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-64 bg-white border-r border-gray-200 min-h-screen flex-col">
        <SidebarContent />
      </aside>
    </>
  );
};

export default Sidebar;
