import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function randomCost(): number {
  // Generate a random cost between 0.00 and 0.50
  return Math.random() * 0.25
}
