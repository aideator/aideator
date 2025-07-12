"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { 
  Key, 
  User, 
  Settings as SettingsIcon, 
  Shield,
  CreditCard,
  Bell
} from "lucide-react";

import { ProviderKeyManager } from "@/components/settings/ProviderKeyManager";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("api-keys");

  return (
    <div className="min-h-screen bg-neutral-white">
      <div className="container mx-auto px-lg py-xl">
        {/* Header */}
        <div className="mb-xl">
          <div className="flex items-center gap-sm mb-sm">
            <SettingsIcon className="h-6 w-6 text-ai-primary" />
            <h1 className="text-display font-bold">Settings</h1>
          </div>
          <p className="text-body-lg text-neutral-shadow">
            Manage your account, API keys, and AIdeator preferences
          </p>
        </div>

        {/* Settings Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 lg:grid-cols-6 mb-xl">
            <TabsTrigger value="api-keys" className="gap-xs">
              <Key className="h-4 w-4" />
              <span className="hidden sm:inline">API Keys</span>
            </TabsTrigger>
            <TabsTrigger value="account" className="gap-xs">
              <User className="h-4 w-4" />
              <span className="hidden sm:inline">Account</span>
            </TabsTrigger>
            <TabsTrigger value="security" className="gap-xs">
              <Shield className="h-4 w-4" />
              <span className="hidden sm:inline">Security</span>
            </TabsTrigger>
            <TabsTrigger value="billing" className="gap-xs">
              <CreditCard className="h-4 w-4" />
              <span className="hidden sm:inline">Billing</span>
            </TabsTrigger>
            <TabsTrigger value="notifications" className="gap-xs">
              <Bell className="h-4 w-4" />
              <span className="hidden sm:inline">Notifications</span>
            </TabsTrigger>
            <TabsTrigger value="preferences" className="gap-xs">
              <SettingsIcon className="h-4 w-4" />
              <span className="hidden sm:inline">Preferences</span>
            </TabsTrigger>
          </TabsList>

          {/* API Keys Tab */}
          <TabsContent value="api-keys">
            <ProviderKeyManager />
          </TabsContent>

          {/* Account Tab */}
          <TabsContent value="account">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-sm">
                  <User className="h-5 w-5" />
                  Account Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-lg">
                  <div className="bg-neutral-paper rounded-md p-lg text-center">
                    <User className="h-12 w-12 text-neutral-shadow mx-auto mb-md" />
                    <h3 className="text-h3 font-semibold mb-sm">Account Management</h3>
                    <p className="text-body text-neutral-shadow">
                      Account settings and profile management coming soon.
                    </p>
                    <Badge variant="secondary" className="mt-md">
                      Coming Soon
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-sm">
                  <Shield className="h-5 w-5" />
                  Security Settings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-lg">
                  <div className="bg-neutral-paper rounded-md p-lg text-center">
                    <Shield className="h-12 w-12 text-neutral-shadow mx-auto mb-md" />
                    <h3 className="text-h3 font-semibold mb-sm">Security Features</h3>
                    <p className="text-body text-neutral-shadow">
                      Two-factor authentication, session management, and security logs coming soon.
                    </p>
                    <Badge variant="secondary" className="mt-md">
                      Coming Soon
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Billing Tab */}
          <TabsContent value="billing">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-sm">
                  <CreditCard className="h-5 w-5" />
                  Billing & Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-lg">
                  <div className="bg-neutral-paper rounded-md p-lg text-center">
                    <CreditCard className="h-12 w-12 text-neutral-shadow mx-auto mb-md" />
                    <h3 className="text-h3 font-semibold mb-sm">Cost Tracking</h3>
                    <p className="text-body text-neutral-shadow">
                      Model usage costs, billing history, and usage analytics coming soon.
                    </p>
                    <Badge variant="secondary" className="mt-md">
                      Coming Soon
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-sm">
                  <Bell className="h-5 w-5" />
                  Notifications
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-lg">
                  <div className="bg-neutral-paper rounded-md p-lg text-center">
                    <Bell className="h-12 w-12 text-neutral-shadow mx-auto mb-md" />
                    <h3 className="text-h3 font-semibold mb-sm">Notification Preferences</h3>
                    <p className="text-body text-neutral-shadow">
                      Email notifications, push notifications, and alert settings coming soon.
                    </p>
                    <Badge variant="secondary" className="mt-md">
                      Coming Soon
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Preferences Tab */}
          <TabsContent value="preferences">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-sm">
                  <SettingsIcon className="h-5 w-5" />
                  AIdeator Preferences
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-lg">
                  <div className="bg-neutral-paper rounded-md p-lg text-center">
                    <SettingsIcon className="h-12 w-12 text-neutral-shadow mx-auto mb-md" />
                    <h3 className="text-h3 font-semibold mb-sm">Application Preferences</h3>
                    <p className="text-body text-neutral-shadow">
                      Theme settings, default models, comparison preferences, and more coming soon.
                    </p>
                    <Badge variant="secondary" className="mt-md">
                      Coming Soon
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}