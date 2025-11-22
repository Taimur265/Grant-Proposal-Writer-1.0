'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  event_type: string;
  start_date: string;
  end_date?: string;
  all_day: boolean;
  project_id?: string;
  location?: string;
  color?: string;
  is_completed: boolean;
}

interface Deadline {
  id: string;
  deadline_name: string;
  deadline_type: string;
  deadline_date: string;
  days_until: number;
  status: string;
  priority: string;
  is_urgent: boolean;
  is_critical: boolean;
}

const EVENT_TYPES = [
  { value: 'deadline', label: 'Deadline' },
  { value: 'milestone', label: 'Milestone' },
  { value: 'meeting', label: 'Meeting' },
  { value: 'reminder', label: 'Reminder' },
  { value: 'submission', label: 'Submission' },
  { value: 'custom', label: 'Custom' },
];

export function GrantCalendar() {
  const queryClient = useQueryClient();
  const [view, setView] = useState<'calendar' | 'deadlines' | 'list'>('deadlines');
  const [showAddEvent, setShowAddEvent] = useState(false);
  const [newEvent, setNewEvent] = useState({
    title: '',
    event_type: 'deadline',
    start_date: '',
    description: '',
  });

  const { data: overviewData, isLoading: overviewLoading } = useQuery({
    queryKey: ['calendar-overview'],
    queryFn: async () => {
      const response = await api.get('/calendar/overview?days=30');
      return response.data;
    },
  });

  const { data: deadlinesData, isLoading: deadlinesLoading } = useQuery({
    queryKey: ['upcoming-deadlines'],
    queryFn: async () => {
      const response = await api.get('/calendar/deadlines/upcoming?days=60');
      return response.data;
    },
  });

  const createEventMutation = useMutation({
    mutationFn: async (eventData: typeof newEvent) => {
      const response = await api.post('/calendar/events', eventData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-overview'] });
      setShowAddEvent(false);
      setNewEvent({ title: '', event_type: 'deadline', start_date: '', description: '' });
    },
  });

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getUrgencyBadge = (deadline: Deadline) => {
    if (deadline.is_critical) {
      return <span className="px-2 py-0.5 bg-red-600 text-white text-xs rounded-full animate-pulse">Critical</span>;
    }
    if (deadline.is_urgent) {
      return <span className="px-2 py-0.5 bg-orange-500 text-white text-xs rounded-full">Urgent</span>;
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Header with tabs */}
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <Button
            variant={view === 'deadlines' ? 'primary' : 'secondary'}
            onClick={() => setView('deadlines')}
          >
            Deadlines
          </Button>
          <Button
            variant={view === 'calendar' ? 'primary' : 'secondary'}
            onClick={() => setView('calendar')}
          >
            Calendar
          </Button>
          <Button
            variant={view === 'list' ? 'primary' : 'secondary'}
            onClick={() => setView('list')}
          >
            All Events
          </Button>
        </div>
        <Button onClick={() => setShowAddEvent(true)}>Add Event</Button>
      </div>

      {/* Overview Stats */}
      {overviewData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">{overviewData.summary.total_deadlines}</p>
              <p className="text-sm text-gray-500">Deadlines</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-orange-600">{overviewData.summary.urgent_deadlines}</p>
              <p className="text-sm text-gray-500">Urgent</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-green-600">{overviewData.summary.total_events}</p>
              <p className="text-sm text-gray-500">Events</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-purple-600">{overviewData.summary.total_reminders}</p>
              <p className="text-sm text-gray-500">Reminders</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Deadlines View */}
      {view === 'deadlines' && (
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Deadlines</CardTitle>
          </CardHeader>
          <CardContent>
            {deadlinesLoading ? (
              <div className="animate-pulse space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-16 bg-gray-200 rounded" />
                ))}
              </div>
            ) : deadlinesData?.deadlines?.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No upcoming deadlines</p>
            ) : (
              <div className="space-y-3">
                {deadlinesData?.deadlines?.map((deadline: Deadline) => (
                  <div
                    key={deadline.id}
                    className={`p-4 rounded-lg border ${getPriorityColor(deadline.priority)}`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium">{deadline.deadline_name}</h4>
                          {getUrgencyBadge(deadline)}
                        </div>
                        <p className="text-sm mt-1">
                          Type: {deadline.deadline_type} | Due: {new Date(deadline.deadline_date).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className={`text-lg font-bold ${deadline.days_until <= 3 ? 'text-red-600' : deadline.days_until <= 7 ? 'text-orange-600' : 'text-gray-700'}`}>
                          {deadline.days_until} days
                        </span>
                        <p className="text-xs text-gray-500">remaining</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Calendar View */}
      {view === 'calendar' && (
        <Card>
          <CardHeader>
            <CardTitle>Calendar</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-7 gap-1 text-center text-sm">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                <div key={day} className="p-2 font-medium text-gray-600">{day}</div>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-1 mt-2">
              {Array.from({ length: 35 }, (_, i) => {
                const date = new Date();
                date.setDate(date.getDate() - date.getDay() + i);
                const dayEvents = overviewData?.events?.filter((e: any) =>
                  new Date(e.date).toDateString() === date.toDateString()
                ) || [];
                const dayDeadlines = overviewData?.deadlines?.filter((d: any) =>
                  new Date(d.date).toDateString() === date.toDateString()
                ) || [];

                return (
                  <div
                    key={i}
                    className={`min-h-[80px] p-1 border rounded ${
                      date.toDateString() === new Date().toDateString()
                        ? 'bg-blue-50 border-blue-300'
                        : 'border-gray-200'
                    }`}
                  >
                    <p className="text-xs text-gray-500">{date.getDate()}</p>
                    {dayDeadlines.slice(0, 2).map((d: any) => (
                      <div key={d.id} className="text-xs p-0.5 mt-0.5 bg-red-100 rounded truncate">
                        {d.title}
                      </div>
                    ))}
                    {dayEvents.slice(0, 2).map((e: any) => (
                      <div key={e.id} className="text-xs p-0.5 mt-0.5 bg-blue-100 rounded truncate">
                        {e.title}
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* List View */}
      {view === 'list' && overviewData && (
        <Card>
          <CardHeader>
            <CardTitle>All Events (Next 30 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[...overviewData.events, ...overviewData.deadlines, ...overviewData.reminders]
                .sort((a: any, b: any) => new Date(a.date).getTime() - new Date(b.date).getTime())
                .map((item: any, index: number) => (
                  <div key={`${item.type}-${item.id}-${index}`} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-1 text-xs rounded ${
                        item.type === 'deadline' ? 'bg-red-100 text-red-700' :
                        item.type === 'event' ? 'bg-blue-100 text-blue-700' :
                        'bg-purple-100 text-purple-700'
                      }`}>
                        {item.type}
                      </span>
                      <span className="font-medium">{item.title}</span>
                    </div>
                    <span className="text-sm text-gray-500">
                      {new Date(item.date).toLocaleDateString()}
                    </span>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Event Modal */}
      {showAddEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add Event</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <Input
                  value={newEvent.title}
                  onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                  placeholder="Event title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select
                  value={newEvent.event_type}
                  onChange={(e) => setNewEvent({ ...newEvent, event_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {EVENT_TYPES.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Date</label>
                <Input
                  type="datetime-local"
                  value={newEvent.start_date}
                  onChange={(e) => setNewEvent({ ...newEvent, start_date: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                  placeholder="Optional description"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setShowAddEvent(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => createEventMutation.mutate(newEvent)}
                  disabled={!newEvent.title || !newEvent.start_date}
                >
                  Create Event
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
