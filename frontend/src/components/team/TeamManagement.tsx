'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

interface Team {
  id: string;
  name: string;
  description?: string;
  role: string;
  member_count: number;
}

interface TeamMember {
  id: string;
  user_id: string;
  email: string;
  name?: string;
  role: string;
  joined_at?: string;
}

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Admin', description: 'Can manage team and projects' },
  { value: 'editor', label: 'Editor', description: 'Can edit proposals and documents' },
  { value: 'reviewer', label: 'Reviewer', description: 'Can comment and review' },
  { value: 'viewer', label: 'Viewer', description: 'Read-only access' },
];

export function TeamManagement() {
  const queryClient = useQueryClient();
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [showCreateTeam, setShowCreateTeam] = useState(false);
  const [showInvite, setShowInvite] = useState(false);
  const [newTeam, setNewTeam] = useState({ name: '', description: '' });
  const [inviteData, setInviteData] = useState({ email: '', role: 'viewer', message: '' });

  const { data: teamsData, isLoading: teamsLoading } = useQuery({
    queryKey: ['teams'],
    queryFn: async () => {
      const response = await api.get('/teams');
      return response.data;
    },
  });

  const { data: teamDetails, isLoading: teamLoading } = useQuery({
    queryKey: ['team', selectedTeam],
    queryFn: async () => {
      const response = await api.get(`/teams/${selectedTeam}`);
      return response.data;
    },
    enabled: !!selectedTeam,
  });

  const createTeamMutation = useMutation({
    mutationFn: async (data: typeof newTeam) => {
      const response = await api.post('/teams', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      setShowCreateTeam(false);
      setNewTeam({ name: '', description: '' });
    },
  });

  const inviteMutation = useMutation({
    mutationFn: async (data: typeof inviteData) => {
      const response = await api.post(`/teams/${selectedTeam}/invite`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['team', selectedTeam] });
      setShowInvite(false);
      setInviteData({ email: '', role: 'viewer', message: '' });
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: async ({ memberId, role }: { memberId: string; role: string }) => {
      const response = await api.patch(`/teams/${selectedTeam}/members/${memberId}/role`, { role });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['team', selectedTeam] });
    },
  });

  const removeMemberMutation = useMutation({
    mutationFn: async (memberId: string) => {
      const response = await api.delete(`/teams/${selectedTeam}/members/${memberId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['team', selectedTeam] });
    },
  });

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner': return 'bg-purple-100 text-purple-800';
      case 'admin': return 'bg-blue-100 text-blue-800';
      case 'editor': return 'bg-green-100 text-green-800';
      case 'reviewer': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Team Management</h2>
        <Button onClick={() => setShowCreateTeam(true)}>Create Team</Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Teams List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Your Teams</CardTitle>
            </CardHeader>
            <CardContent>
              {teamsLoading ? (
                <div className="animate-pulse space-y-2">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-16 bg-gray-200 rounded" />
                  ))}
                </div>
              ) : teamsData?.teams?.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No teams yet</p>
              ) : (
                <div className="space-y-2">
                  {teamsData?.teams?.map((team: Team) => (
                    <button
                      key={team.id}
                      onClick={() => setSelectedTeam(team.id)}
                      className={`w-full p-3 rounded-lg text-left transition ${
                        selectedTeam === team.id
                          ? 'bg-blue-50 border-2 border-blue-500'
                          : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{team.name}</p>
                          <p className="text-sm text-gray-500">{team.member_count} members</p>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-xs ${getRoleBadgeColor(team.role)}`}>
                          {team.role}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Team Details */}
        <div className="lg:col-span-2">
          {selectedTeam && teamDetails ? (
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>{teamDetails.name}</CardTitle>
                  <Button size="sm" onClick={() => setShowInvite(true)}>
                    Invite Member
                  </Button>
                </div>
                {teamDetails.description && (
                  <p className="text-gray-600 text-sm mt-1">{teamDetails.description}</p>
                )}
              </CardHeader>
              <CardContent>
                <h4 className="font-medium mb-3">Team Members</h4>
                {teamLoading ? (
                  <div className="animate-pulse space-y-2">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="h-12 bg-gray-200 rounded" />
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {teamDetails.members?.map((member: TeamMember) => (
                      <div
                        key={member.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                            <span className="text-blue-600 font-medium">
                              {(member.name || member.email)[0].toUpperCase()}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium">{member.name || member.email}</p>
                            {member.name && <p className="text-sm text-gray-500">{member.email}</p>}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {member.role !== 'owner' ? (
                            <>
                              <select
                                value={member.role}
                                onChange={(e) => updateRoleMutation.mutate({
                                  memberId: member.id,
                                  role: e.target.value,
                                })}
                                className="text-sm border rounded px-2 py-1"
                              >
                                {ROLE_OPTIONS.map(opt => (
                                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                                ))}
                              </select>
                              <button
                                onClick={() => removeMemberMutation.mutate(member.id)}
                                className="text-red-500 hover:text-red-700 p-1"
                              >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </>
                          ) : (
                            <span className={`px-2 py-1 rounded text-xs ${getRoleBadgeColor('owner')}`}>
                              Owner
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                Select a team to view details
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Create Team Modal */}
      {showCreateTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Create Team</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Team Name</label>
                <Input
                  value={newTeam.name}
                  onChange={(e) => setNewTeam({ ...newTeam, name: e.target.value })}
                  placeholder="Enter team name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={newTeam.description}
                  onChange={(e) => setNewTeam({ ...newTeam, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                  placeholder="Optional team description"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setShowCreateTeam(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => createTeamMutation.mutate(newTeam)}
                  disabled={!newTeam.name}
                >
                  Create
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Invite Modal */}
      {showInvite && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Invite Team Member</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <Input
                  type="email"
                  value={inviteData.email}
                  onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
                  placeholder="Enter email address"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Role</label>
                <select
                  value={inviteData.role}
                  onChange={(e) => setInviteData({ ...inviteData, role: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {ROLE_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label} - {opt.description}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Message (optional)</label>
                <textarea
                  value={inviteData.message}
                  onChange={(e) => setInviteData({ ...inviteData, message: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={2}
                  placeholder="Add a personal message"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setShowInvite(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => inviteMutation.mutate(inviteData)}
                  disabled={!inviteData.email}
                >
                  Send Invite
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
