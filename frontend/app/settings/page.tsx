'use client'

import { ProviderKeyManager } from '@/components/provider-keys/provider-key-manager'

export default function SettingsPage() {
  return (
    <div className="bg-gray-950 text-gray-50 min-h-screen">
      <div className="container mx-auto max-w-5xl py-8">
        <ProviderKeyManager />
      </div>
    </div>
  )
}