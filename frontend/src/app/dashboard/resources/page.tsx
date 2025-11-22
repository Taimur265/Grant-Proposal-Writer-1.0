'use client';

import { ResourceLibrary } from '@/components/resources/ResourceLibrary';

export default function ResourcesPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Resource Library</h1>
      <p className="text-gray-600 mb-6">
        Access templates, guides, and resources for grant writing.
      </p>
      <ResourceLibrary />
    </div>
  );
}
