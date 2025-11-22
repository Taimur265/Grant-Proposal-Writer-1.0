'use client';

import { StakeholderManager } from '@/components/stakeholders/StakeholderManager';

export default function StakeholdersPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Stakeholder Management</h1>
      <StakeholderManager />
    </div>
  );
}
