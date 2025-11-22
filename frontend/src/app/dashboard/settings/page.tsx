'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import { User, Building, Loader2, Save, Key } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/auth'
import { authApi } from '@/lib/api'

interface ProfileForm {
  full_name: string
  organization: string
}

export default function SettingsPage() {
  const { user, setUser } = useAuthStore()
  const [activeTab, setActiveTab] = useState('profile')

  const { register, handleSubmit } = useForm<ProfileForm>({
    defaultValues: {
      full_name: user?.full_name || '',
      organization: user?.organization || '',
    },
  })

  const updateProfileMutation = useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: (data) => {
      setUser(data)
      toast.success('Profile updated successfully')
    },
    onError: () => {
      toast.error('Failed to update profile')
    },
  })

  const onSubmit = (data: ProfileForm) => {
    updateProfileMutation.mutate(data)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your account and preferences</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="md:col-span-1">
          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab('profile')}
              className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                activeTab === 'profile'
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <User className="w-5 h-5 mr-3" />
              Profile
            </button>
            <button
              onClick={() => setActiveTab('api')}
              className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                activeTab === 'api'
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <Key className="w-5 h-5 mr-3" />
              API Keys
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="md:col-span-3">
          {activeTab === 'profile' && (
            <div className="card">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-900">Profile Information</h2>
                <p className="text-gray-600 mt-1">
                  Update your personal information
                </p>
              </div>
              <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="input bg-gray-50 cursor-not-allowed"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Email cannot be changed
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name
                  </label>
                  <input
                    {...register('full_name')}
                    type="text"
                    className="input"
                    placeholder="Your full name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Organization
                  </label>
                  <input
                    {...register('organization')}
                    type="text"
                    className="input"
                    placeholder="Your organization name"
                  />
                </div>

                <div className="flex justify-end pt-4 border-t">
                  <button
                    type="submit"
                    disabled={updateProfileMutation.isPending}
                    className="btn-primary"
                  >
                    {updateProfileMutation.isPending ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4 mr-2" />
                        Save Changes
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="card">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-900">API Configuration</h2>
                <p className="text-gray-600 mt-1">
                  Configure AI provider API keys (server-side only)
                </p>
              </div>
              <div className="p-6">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-yellow-800 mb-2">
                    Server Configuration Required
                  </h4>
                  <p className="text-sm text-yellow-700">
                    API keys for OpenAI and Anthropic are configured server-side for security.
                    Please update the environment variables in your backend deployment:
                  </p>
                  <ul className="text-sm text-yellow-700 mt-2 list-disc list-inside">
                    <li>OPENAI_API_KEY - For GPT models</li>
                    <li>ANTHROPIC_API_KEY - For Claude models</li>
                  </ul>
                </div>

                <div className="mt-6 space-y-4">
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                        <span className="text-lg">🤖</span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">OpenAI</p>
                        <p className="text-sm text-gray-500">GPT-4 Turbo</p>
                      </div>
                    </div>
                    <span className="badge-success">Available</span>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                        <span className="text-lg">🧠</span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">Anthropic</p>
                        <p className="text-sm text-gray-500">Claude 3</p>
                      </div>
                    </div>
                    <span className="badge-success">Available</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
