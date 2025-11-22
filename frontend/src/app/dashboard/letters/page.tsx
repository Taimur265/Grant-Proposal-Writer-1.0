'use client';

import { LetterGenerator } from '@/components/letters/LetterGenerator';

export default function LettersPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Letter Generator</h1>
      <p className="text-gray-600 mb-6">
        Generate professional letters including support letters, inquiry letters, and thank-you notes.
      </p>
      <LetterGenerator />
    </div>
  );
}
