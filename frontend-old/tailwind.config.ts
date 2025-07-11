import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // aideator Brand Colors
        'ai-primary': 'hsl(var(--color-ai-primary))',
        'ai-secondary': 'hsl(var(--color-ai-secondary))',
        'ai-accent': 'hsl(var(--color-ai-accent))',
        
        // Agent Stream Colors
        'agent-1': 'hsl(var(--color-agent-1))',
        'agent-2': 'hsl(var(--color-agent-2))',
        'agent-3': 'hsl(var(--color-agent-3))',
        'agent-4': 'hsl(var(--color-agent-4))',
        'agent-5': 'hsl(var(--color-agent-5))',
        
        // Neutral Palette
        'neutral-white': 'hsl(var(--color-neutral-white))',
        'neutral-paper': 'hsl(var(--color-neutral-paper))',
        'neutral-fog': 'hsl(var(--color-neutral-fog))',
        'neutral-shadow': 'hsl(var(--color-neutral-shadow))',
        'neutral-charcoal': 'hsl(var(--color-neutral-charcoal))',
        
        // Semantic Colors
        'semantic-success': 'hsl(var(--color-semantic-success))',
        'semantic-warning': 'hsl(var(--color-semantic-warning))',
        'semantic-error': 'hsl(var(--color-semantic-error))',
        'semantic-info': 'hsl(var(--color-semantic-info))',
        
        // Legacy compatibility (for shadcn/ui components)
        'primary': 'hsl(var(--color-primary))',
        'primary-foreground': 'hsl(var(--color-primary-foreground))',
        'secondary': 'hsl(var(--color-secondary))',
        'secondary-foreground': 'hsl(var(--color-secondary-foreground))',
        'background': 'hsl(var(--color-background))',
        'foreground': 'hsl(var(--color-foreground))',
        'card': 'hsl(var(--color-card))',
        'card-foreground': 'hsl(var(--color-card-foreground))',
        'muted': 'hsl(var(--color-muted))',
        'muted-foreground': 'hsl(var(--color-muted-foreground))',
        'accent': 'hsl(var(--color-accent))',
        'accent-foreground': 'hsl(var(--color-accent-foreground))',
        'destructive': 'hsl(var(--color-destructive))',
        'destructive-foreground': 'hsl(var(--color-destructive-foreground))',
        'border': 'hsl(var(--color-border))',
        'input': 'hsl(var(--color-input))',
        'ring': 'hsl(var(--color-ring))',
      },
      fontSize: {
        'display': ['var(--font-size-display)', { lineHeight: 'var(--line-height-display)' }],
        'h1': ['var(--font-size-h1)', { lineHeight: 'var(--line-height-h1)' }],
        'h2': ['var(--font-size-h2)', { lineHeight: 'var(--line-height-h2)' }],
        'h3': ['var(--font-size-h3)', { lineHeight: 'var(--line-height-h3)' }],
        'body-lg': ['var(--font-size-body-lg)', { lineHeight: 'var(--line-height-body-lg)' }],
        'body': ['var(--font-size-body)', { lineHeight: 'var(--line-height-body)' }],
        'body-sm': ['var(--font-size-body-sm)', { lineHeight: 'var(--line-height-body-sm)' }],
        'label': ['var(--font-size-label)', { lineHeight: 'var(--line-height-label)' }],
        'caption': ['var(--font-size-caption)', { lineHeight: 'var(--line-height-caption)' }],
      },
      spacing: {
        'xs': 'var(--spacing-xs)',
        'sm': 'var(--spacing-sm)',
        'md': 'var(--spacing-md)',
        'lg': 'var(--spacing-lg)',
        'xl': 'var(--spacing-xl)',
      },
      borderRadius: {
        'lg': 'var(--radius)',
        'md': 'calc(var(--radius) - 2px)',
        'sm': 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),
  ],
}

export default config