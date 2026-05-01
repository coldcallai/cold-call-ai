import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Users, Trash2, Mail, Shield, Crown, UserCheck, AlertCircle, RefreshCw, UserPlus, Clock
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TeamsPage = () => {
  const { user } = useAuth();
  const [teamMembers, setTeamMembers] = useState([]);
  const [pendingInvites, setPendingInvites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviting, setInviting] = useState(false);
  const [teamInfo, setTeamInfo] = useState({ max_seats: 1, used_seats: 1 });

  const fetchTeam = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("session_token");
      const res = await axios.get(`${API}/team`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTeamMembers(res.data.members || []);
      setPendingInvites(res.data.pending_invites || []);
      setTeamInfo({
        max_seats: res.data.max_seats || 1,
        used_seats: res.data.used_seats || 1
      });
    } catch (err) {
      console.error("Failed to fetch team:", err);
      toast.error("Failed to load team data");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) fetchTeam();
  }, [user, fetchTeam]);

  const handleInvite = async () => {
    if (!inviteEmail.trim()) {
      toast.error("Please enter an email address");
      return;
    }
    try {
      setInviting(true);
      const token = localStorage.getItem("session_token");
      await axios.post(`${API}/team/invite`, {
        email: inviteEmail.trim().toLowerCase(),
        role: inviteRole
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Invitation sent to " + inviteEmail);
      setInviteEmail("");
      setInviteRole("member");
      setShowInviteModal(false);
      fetchTeam();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to send invitation");
    } finally {
      setInviting(false);
    }
  };

  const handleRemoveMember = async (memberId, memberEmail) => {
    if (!window.confirm("Remove " + memberEmail + " from your team?")) return;
    try {
      const token = localStorage.getItem("session_token");
      await axios.delete(`${API}/team/members/${memberId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(memberEmail + " removed from team");
      fetchTeam();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to remove member");
    }
  };

  const handleUpdateRole = async (memberId, newRole) => {
    try {
      const token = localStorage.getItem("session_token");
      await axios.put(`${API}/team/members/${memberId}/role`, {
        role: newRole
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Role updated");
      fetchTeam();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to update role");
    }
  };

  const handleCancelInvite = async (inviteId) => {
    try {
      const token = localStorage.getItem("session_token");
      await axios.delete(`${API}/team/invites/${inviteId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Invitation cancelled");
      fetchTeam();
    } catch (err) {
      toast.error("Failed to cancel invitation");
    }
  };

  const getRoleBadge = (role) => {
    switch (role) {
      case "owner":
        return <Badge className="bg-purple-100 text-purple-700 border-purple-200"><Crown className="w-3 h-3 mr-1" />Owner</Badge>;
      case "admin":
        return <Badge className="bg-blue-100 text-blue-700 border-blue-200"><Shield className="w-3 h-3 mr-1" />Admin</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-700 border-gray-200"><UserCheck className="w-3 h-3 mr-1" />Member</Badge>;
    }
  };

  const seatsRemaining = teamInfo.max_seats - teamInfo.used_seats;
  const seatPercentage = Math.round((teamInfo.used_seats / teamInfo.max_seats) * 100);

  if (loading) {
    return (
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="w-6 h-6 text-blue-600" />
            Team Management
          </h1>
          <p className="text-gray-500 mt-1">Manage your team members and their access levels</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchTeam}>
            <RefreshCw className="w-4 h-4 mr-1" /> Refresh
          </Button>
          <Button
            onClick={() => setShowInviteModal(true)}
            disabled={seatsRemaining <= 0}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <UserPlus className="w-4 h-4 mr-2" /> Invite Member
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm font-medium text-gray-600">Team Seats</p>
              <p className="text-2xl font-bold text-gray-900">
                {teamInfo.used_seats} <span className="text-gray-400 text-lg font-normal">/ {teamInfo.max_seats}</span>
              </p>
            </div>
            <div className="text-right">
              {seatsRemaining > 0 ? (
                <Badge className="bg-green-100 text-green-700 border-green-200">
                  {seatsRemaining} seat{seatsRemaining !== 1 ? "s" : ""} available
                </Badge>
              ) : (
                <Badge className="bg-red-100 text-red-700 border-red-200">No seats available</Badge>
              )}
            </div>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${seatPercentage >= 90 ? "bg-red-500" : seatPercentage >= 70 ? "bg-yellow-500" : "bg-blue-500"}`}
              style={{ width: Math.min(seatPercentage, 100) + "%" }}
            />
          </div>
          {seatsRemaining <= 0 && (
            <p className="text-sm text-red-600 mt-2 flex items-center gap-1">
              <AlertCircle className="w-4 h-4" />
              Upgrade your plan to add more team members
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Team Members</CardTitle>
          <CardDescription>Active members with access to your workspace</CardDescription>
        </CardHeader>
        <CardContent>
          {teamMembers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Users className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="font-medium">No team members yet</p>
              <p className="text-sm mt-1">Invite your first team member to get started</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Member</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teamMembers.map((member) => (
                  <TableRow key={member._id || member.email}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-semibold text-sm">
                          {(member.name || member.email || "?").charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{member.name || "\u2014"}</p>
                          <p className="text-sm text-gray-500">{member.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{getRoleBadge(member.role)}</TableCell>
                    <TableCell className="text-gray-500 text-sm">
                      {member.joined_at ? new Date(member.joined_at).toLocaleDateString() : "\u2014"}
                    </TableCell>
                    <TableCell className="text-right">
                      {member.role !== "owner" && (
                        <div className="flex items-center justify-end gap-2">
                          <Select
                            value={member.role}
                            onValueChange={(val) => handleUpdateRole(member._id, val)}
                          >
                            <SelectTrigger className="w-28 h-8 text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="admin">Admin</SelectItem>
                              <SelectItem value="member">Member</SelectItem>
                            </SelectContent>
                          </Select>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-500 hover:text-red-700 hover:bg-red-50"
                            onClick={() => handleRemoveMember(member._id, member.email)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {pendingInvites.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="w-5 h-5 text-yellow-500" />
              Pending Invitations
            </CardTitle>
            <CardDescription>Invitations waiting to be accepted</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Sent</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingInvites.map((invite) => (
                  <TableRow key={invite._id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-700">{invite.email}</span>
                      </div>
                    </TableCell>
                    <TableCell>{getRoleBadge(invite.role)}</TableCell>
                    <TableCell className="text-gray-500 text-sm">
                      {invite.invited_at ? new Date(invite.invited_at).toLocaleDateString() : "\u2014"}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        onClick={() => handleCancelInvite(invite._id)}
                      >
                        <Trash2 className="w-4 h-4 mr-1" /> Cancel
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Dialog open={showInviteModal} onOpenChange={setShowInviteModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invite Team Member</DialogTitle>
            <DialogDescription>
              Send an invitation to join your workspace.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Email Address</label>
              <Input
                type="email"
                placeholder="colleague@company.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleInvite()}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Role</label>
              <Select value={inviteRole} onValueChange={setInviteRole}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin - Full access, can manage team</SelectItem>
                  <SelectItem value="member">Member - Standard access</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInviteModal(false)}>Cancel</Button>
            <Button
              onClick={handleInvite}
              disabled={inviting || !inviteEmail.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {inviting ? "Sending..." : "Send Invitation"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TeamsPage;
