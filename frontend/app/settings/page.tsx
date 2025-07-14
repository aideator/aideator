'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { ProviderKeyManager } from '@/components/provider-keys/provider-key-manager'

export default function SettingsPage() {
  return (
    <div className="bg-gray-950 text-gray-50 min-h-screen">
      <div className="container mx-auto max-w-5xl py-8">
        <Link href="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-gray-300 mb-4">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to home</span>
        </Link>
        
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-gray-400 mb-8">Manage your account settings and preferences</p>
        
        <ProviderKeyManager />
      </div>
    </div>
  )
}