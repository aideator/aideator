"use client"

import { User, LogOut, Settings } from "lucide-react"
import { useAuth } from "@/lib/auth-context"
import { useRouter } from "next/navigation"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

export function AccountDropdown() {
  const { user, signOut } = useAuth()
  const router = useRouter()

  if (!user) return null

  // Get initials for avatar fallback
  const initials = user.full_name
    ?.split(" ")
    .map((name) => name[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || user.email[0].toUpperCase()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="rounded-full hover:ring-2 hover:ring-gray-600 hover:ring-offset-2 hover:ring-offset-gray-950 transition-all">
          <Avatar className="h-8 w-8">
            <AvatarImage src={user.github_avatar_url} alt={user.full_name || user.email} />
            <AvatarFallback className="bg-gray-700 text-gray-200 text-sm">
              {user.github_avatar_url ? initials : <User className="h-4 w-4" />}
            </AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56 bg-gray-900 border-gray-800" align="end">
        <DropdownMenuLabel className="text-gray-200">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user.full_name || "User"}</p>
            <p className="text-xs leading-none text-gray-400">{user.email}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-gray-800" />
        <DropdownMenuItem 
          className="text-gray-200 hover:bg-gray-800 hover:text-gray-100 cursor-pointer"
          onClick={() => router.push('/settings')}
        >
          <Settings className="mr-2 h-4 w-4" />
          <span>Account Settings</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator className="bg-gray-800" />
        <DropdownMenuItem 
          className="text-gray-200 hover:bg-gray-800 hover:text-gray-100 cursor-pointer"
          onClick={signOut}
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Sign Out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}