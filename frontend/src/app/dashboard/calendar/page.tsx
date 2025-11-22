'use client';

import { GrantCalendar } from '@/components/calendar/GrantCalendar';

export default function CalendarPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Grant Calendar</h1>
      <GrantCalendar />
    </div>
  );
}
