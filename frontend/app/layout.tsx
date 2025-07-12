import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { cn } from "@/lib/utils"
import { PageHeader } from "@/components/page-header"

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" })

export const metadata: Metadata = {
  title: "AIdeator",
  description: "A Kubernetes-native multi-agent AI orchestration platform"
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={cn("min-h-screen bg-background font-sans antialiased flex flex-col", inter.variable)}>
        <PageHeader />
        <main className="flex-1 flex flex-col">
          {children}
        </main>
      </body>
    </html>
  )
}
