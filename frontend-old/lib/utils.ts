import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Agent color utility functions for Tailwind CSS v4
export const getAgentColorClasses = (agentColor: string) => {
  // Map of agent colors to their Tailwind classes
  const colorMap: Record<string, {
    bg: string;
    text: string;
    border: string;
    borderL: string;
    ring: string;
    bgOpacity90: string;
    hoverBg10: string;
    hoverBg90: string;
  }> = {
    'agent-1': {
      bg: 'bg-agent-1',
      text: 'text-agent-1',
      border: 'border-agent-1',
      borderL: 'border-l-agent-1',
      ring: 'ring-agent-1',
      bgOpacity90: 'bg-agent-1/90',
      hoverBg10: 'hover:bg-agent-1/10',
      hoverBg90: 'hover:bg-agent-1/90',
    },
    'agent-2': {
      bg: 'bg-agent-2',
      text: 'text-agent-2',
      border: 'border-agent-2',
      borderL: 'border-l-agent-2',
      ring: 'ring-agent-2',
      bgOpacity90: 'bg-agent-2/90',
      hoverBg10: 'hover:bg-agent-2/10',
      hoverBg90: 'hover:bg-agent-2/90',
    },
    'agent-3': {
      bg: 'bg-agent-3',
      text: 'text-agent-3',
      border: 'border-agent-3',
      borderL: 'border-l-agent-3',
      ring: 'ring-agent-3',
      bgOpacity90: 'bg-agent-3/90',
      hoverBg10: 'hover:bg-agent-3/10',
      hoverBg90: 'hover:bg-agent-3/90',
    },
    'agent-4': {
      bg: 'bg-agent-4',
      text: 'text-agent-4',
      border: 'border-agent-4',
      borderL: 'border-l-agent-4',
      ring: 'ring-agent-4',
      bgOpacity90: 'bg-agent-4/90',
      hoverBg10: 'hover:bg-agent-4/10',
      hoverBg90: 'hover:bg-agent-4/90',
    },
    'agent-5': {
      bg: 'bg-agent-5',
      text: 'text-agent-5',
      border: 'border-agent-5',
      borderL: 'border-l-agent-5',
      ring: 'ring-agent-5',
      bgOpacity90: 'bg-agent-5/90',
      hoverBg10: 'hover:bg-agent-5/10',
      hoverBg90: 'hover:bg-agent-5/90',
    },
  };

  return colorMap[agentColor] || colorMap['agent-1'];
}
