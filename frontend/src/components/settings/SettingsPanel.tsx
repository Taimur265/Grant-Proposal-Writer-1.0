'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface UserSettings {
  theme: string;
  language: string;
  timezone: string;
  email_notifications: boolean;
  email_deadline_reminders: boolean;
  email_comment_notifications: boolean;
  auto_save: boolean;
  spell_check: boolean;
  ai_suggestions_enabled: boolean;
  ai_provider: string;
  default_grant_type: string;
  default_indirect_rate: string;
}

interface OrganizationProfile {
  name: string;
  legal_name: string;
  organization_type: string;
  ein: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  phone: string;
  website: string;
  executive_director: string;
  mission_statement: string;
  annual_budget: string;
  focus_areas: string[];
  indirect_cost_rate: string;
}

export function SettingsPanel() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'preferences' | 'organization' | 'notifications'>('preferences');

  const { data: settings, isLoading: settingsLoading } = useQuery({
    queryKey: ['user-settings'],
    queryFn: async () => {
      const response = await api.get<UserSettings>('/settings');
      return response.data;
    },
  });

  const { data: orgProfile, isLoading: orgLoading } = useQuery({
    queryKey: ['organization-profile'],
    queryFn: async () => {
      const response = await api.get('/settings/organization');
      return response.data;
    },
  });

  const updateSettingsMutation = useMutation({
    mutationFn: async (data: Partial<UserSettings>) => {
      const response = await api.patch('/settings', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-settings'] });
    },
  });

  const updateOrgMutation = useMutation({
    mutationFn: async (data: Partial<OrganizationProfile>) => {
      const response = await api.post('/settings/organization', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organization-profile'] });
    },
  });

  const [orgFormData, setOrgFormData] = useState<Partial<OrganizationProfile>>({});

  const handleOrgSave = () => {
    updateOrgMutation.mutate(orgFormData);
  };

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex gap-4 border-b">
        {(['preferences', 'organization', 'notifications'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 px-1 border-b-2 transition-colors capitalize ${
              activeTab === tab
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Preferences Tab */}
      {activeTab === 'preferences' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Display Preferences</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Theme</label>
                  <select
                    value={settings?.theme || 'light'}
                    onChange={(e) => updateSettingsMutation.mutate({ theme: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                    <option value="system">System</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
                  <select
                    value={settings?.language || 'en'}
                    onChange={(e) => updateSettingsMutation.mutate({ language: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Editor Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={settings?.auto_save ?? true}
                    onChange={(e) => updateSettingsMutation.mutate({ auto_save: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-gray-700">Enable auto-save</span>
                </label>
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={settings?.spell_check ?? true}
                    onChange={(e) => updateSettingsMutation.mutate({ spell_check: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-gray-700">Enable spell check</span>
                </label>
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={settings?.ai_suggestions_enabled ?? true}
                    onChange={(e) => updateSettingsMutation.mutate({ ai_suggestions_enabled: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-gray-700">Enable AI suggestions</span>
                </label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Default Project Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Default Grant Type</label>
                  <select
                    value={settings?.default_grant_type || 'federal'}
                    onChange={(e) => updateSettingsMutation.mutate({ default_grant_type: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="federal">Federal</option>
                    <option value="foundation">Foundation</option>
                    <option value="corporate">Corporate</option>
                    <option value="international">International</option>
                    <option value="research">Research</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Indirect Rate (%)
                  </label>
                  <Input
                    type="number"
                    step="0.01"
                    value={parseFloat(settings?.default_indirect_rate || '0.54') * 100}
                    onChange={(e) => updateSettingsMutation.mutate({
                      default_indirect_rate: (parseFloat(e.target.value) / 100).toString()
                    })}
                    placeholder="54"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Organization Tab */}
      {activeTab === 'organization' && (
        <Card>
          <CardHeader>
            <CardTitle>Organization Profile</CardTitle>
          </CardHeader>
          <CardContent>
            {orgLoading ? (
              <div className="animate-pulse space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-10 bg-gray-200 rounded" />
                ))}
              </div>
            ) : (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Organization Name *</label>
                    <Input
                      value={orgFormData.name ?? orgProfile?.name ?? ''}
                      onChange={(e) => setOrgFormData({ ...orgFormData, name: e.target.value })}
                      placeholder="Your Organization"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Legal Name</label>
                    <Input
                      value={orgFormData.legal_name ?? orgProfile?.legal_name ?? ''}
                      onChange={(e) => setOrgFormData({ ...orgFormData, legal_name: e.target.value })}
                      placeholder="Legal entity name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Organization Type</label>
                    <select
                      value={orgFormData.organization_type ?? orgProfile?.organization_type ?? ''}
                      onChange={(e) => setOrgFormData({ ...orgFormData, organization_type: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                    >
                      <option value="">Select type...</option>
                      <option value="nonprofit">Non-Profit 501(c)(3)</option>
                      <option value="government">Government Agency</option>
                      <option value="academic">Academic Institution</option>
                      <option value="ngo">NGO</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">EIN (Tax ID)</label>
                    <Input
                      value={orgFormData.ein ?? orgProfile?.ein ?? ''}
                      onChange={(e) => setOrgFormData({ ...orgFormData, ein: e.target.value })}
                      placeholder="XX-XXXXXXX"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                    <Input
                      value={orgFormData.phone ?? orgProfile?.phone ?? ''}
                      onChange={(e) => setOrgFormData({ ...orgFormData, phone: e.target.value })}
                      placeholder="(555) 555-5555"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Website</label>
                    <Input
                      value={orgFormData.website ?? orgProfile?.website ?? ''}
                      onChange={(e) => setOrgFormData({ ...orgFormData, website: e.target.value })}
                      placeholder="https://example.org"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
                  <Input
                    value={orgFormData.address ?? orgProfile?.address ?? ''}
                    onChange={(e) => setOrgFormData({ ...orgFormData, address: e.target.value })}
                    placeholder="Street address"
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">City</label>
                    <Input
                      value={orgFormData.city ?? orgProfile?.city ?? ''}
                      onChange={(e) => setOrgFormData({ ...orgFormData, city: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">State</label>
                    <Input
                      value={orgFormData.state ?? orgProfile?.state ?? ''}
                      onChange={(e) => setOrgFormData({ ...orgFormData, state: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">ZIP</label>
                    <Input
                      value={orgFormData.zip_code ?? orgProfile?.zip_code ?? ''}
                      onChange={(e) => setOrgFormData({ ...orgFormData, zip_code: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Indirect Rate</label>
                    <Input
                      value={orgFormData.indirect_cost_rate ?? orgProfile?.indirect_cost_rate ?? ''}
                      onChange={(e) => setOrgFormData({ ...orgFormData, indirect_cost_rate: e.target.value })}
                      placeholder="54%"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Mission Statement</label>
                  <textarea
                    value={orgFormData.mission_statement ?? orgProfile?.mission_statement ?? ''}
                    onChange={(e) => setOrgFormData({ ...orgFormData, mission_statement: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                    rows={4}
                    placeholder="Your organization's mission..."
                  />
                </div>

                <div className="flex justify-end">
                  <Button onClick={handleOrgSave} disabled={updateOrgMutation.isPending}>
                    {updateOrgMutation.isPending ? 'Saving...' : 'Save Profile'}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <Card>
          <CardHeader>
            <CardTitle>Email Notifications</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={settings?.email_notifications ?? true}
                  onChange={(e) => updateSettingsMutation.mutate({ email_notifications: e.target.checked })}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <div>
                  <span className="text-gray-900 font-medium">Enable email notifications</span>
                  <p className="text-sm text-gray-500">Receive email updates about your projects</p>
                </div>
              </label>
              <label className="flex items-center gap-3 pl-7">
                <input
                  type="checkbox"
                  checked={settings?.email_deadline_reminders ?? true}
                  onChange={(e) => updateSettingsMutation.mutate({ email_deadline_reminders: e.target.checked })}
                  className="w-4 h-4 text-blue-600 rounded"
                  disabled={!settings?.email_notifications}
                />
                <div>
                  <span className="text-gray-900">Deadline reminders</span>
                  <p className="text-sm text-gray-500">Get reminders for upcoming grant deadlines</p>
                </div>
              </label>
              <label className="flex items-center gap-3 pl-7">
                <input
                  type="checkbox"
                  checked={settings?.email_comment_notifications ?? true}
                  onChange={(e) => updateSettingsMutation.mutate({ email_comment_notifications: e.target.checked })}
                  className="w-4 h-4 text-blue-600 rounded"
                  disabled={!settings?.email_notifications}
                />
                <div>
                  <span className="text-gray-900">Comment notifications</span>
                  <p className="text-sm text-gray-500">Get notified when someone comments on your proposals</p>
                </div>
              </label>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
