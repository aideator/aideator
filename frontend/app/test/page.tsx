export default function TestPage() {
  return (
    <div className="min-h-screen bg-gradient-neural-twilight p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <h1 className="text-4xl font-bold text-neutral-white mb-8">
          Neural Spectrum Design System
        </h1>
        
        {/* Basic Colors Test */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-neutral-white">Basic Colors</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-red-500 text-white p-4 rounded">Red 500</div>
            <div className="bg-blue-500 text-white p-4 rounded">Blue 500</div>
            <div className="bg-green-500 text-white p-4 rounded">Green 500</div>
            <div className="bg-yellow-500 text-black p-4 rounded">Yellow 500</div>
          </div>
        </section>

        {/* Neural Spectrum Brand Colors */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-neutral-white">Neural Spectrum Brand Colors</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-ai-primary text-white p-6 rounded-lg">
              <h3 className="font-semibold">Neural Blue</h3>
              <p className="text-sm opacity-90">Intelligent, trustworthy</p>
            </div>
            <div className="bg-ai-secondary text-white p-6 rounded-lg">
              <h3 className="font-semibold">Quantum Purple</h3>
              <p className="text-sm opacity-90">Innovative, creative</p>
            </div>
            <div className="bg-ai-accent text-white p-6 rounded-lg">
              <h3 className="font-semibold">Synthesis Teal</h3>
              <p className="text-sm opacity-90">Harmony, integration</p>
            </div>
          </div>
        </section>

        {/* Agent Model Colors */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-neutral-white">Agent Model Colors</h2>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="bg-agent-1 text-white p-4 rounded-lg text-center">
              <div className="font-semibold">Crimson Edge</div>
              <div className="text-sm opacity-90">Bold, confident</div>
            </div>
            <div className="bg-agent-2 text-white p-4 rounded-lg text-center">
              <div className="font-semibold">Amber Insight</div>
              <div className="text-sm opacity-90">Warm, approachable</div>
            </div>
            <div className="bg-agent-3 text-white p-4 rounded-lg text-center">
              <div className="font-semibold">Emerald Logic</div>
              <div className="text-sm opacity-90">Growth, accuracy</div>
            </div>
            <div className="bg-agent-4 text-white p-4 rounded-lg text-center">
              <div className="font-semibold">Sapphire Depth</div>
              <div className="text-sm opacity-90">Trust, reliability</div>
            </div>
            <div className="bg-agent-5 text-white p-4 rounded-lg text-center">
              <div className="font-semibold">Violet Innovation</div>
              <div className="text-sm opacity-90">Creative, advanced</div>
            </div>
          </div>
        </section>

        {/* Neural Spectrum Neutrals */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-neutral-white">Neural Spectrum Neutrals</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-neutral-white border-2 border-neutral-fog p-4 rounded-lg">
              <div className="font-semibold text-neutral-charcoal">Quantum White</div>
              <div className="text-sm text-neutral-shadow">Pure, clean</div>
            </div>
            <div className="bg-neutral-paper p-4 rounded-lg">
              <div className="font-semibold text-neutral-charcoal">Neural Mist</div>
              <div className="text-sm text-neutral-shadow">Subtle backgrounds</div>
            </div>
            <div className="bg-neutral-fog p-4 rounded-lg">
              <div className="font-semibold text-neutral-charcoal">Data Fog</div>
              <div className="text-sm text-neutral-shadow">Gentle borders</div>
            </div>
            <div className="bg-neutral-charcoal text-neutral-white p-4 rounded-lg">
              <div className="font-semibold">Deep Matter</div>
              <div className="text-sm opacity-90">Primary text</div>
            </div>
          </div>
        </section>

        {/* Neural Spectrum Semantic States */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-neutral-white">Neural Spectrum Semantic States</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-semantic-success text-white p-4 rounded-lg text-center">
              <div className="font-semibold">Success Pulse</div>
              <div className="text-sm opacity-90">Achievements</div>
            </div>
            <div className="bg-semantic-warning text-white p-4 rounded-lg text-center">
              <div className="font-semibold">Warning Flux</div>
              <div className="text-sm opacity-90">Attention</div>
            </div>
            <div className="bg-semantic-error text-white p-4 rounded-lg text-center">
              <div className="font-semibold">Error Signal</div>
              <div className="text-sm opacity-90">Problems</div>
            </div>
            <div className="bg-semantic-info text-white p-4 rounded-lg text-center">
              <div className="font-semibold">Info Stream</div>
              <div className="text-sm opacity-90">Information</div>
            </div>
          </div>
        </section>

        {/* Typography Test */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-neutral-white">Typography</h2>
          <div className="space-y-4 bg-neutral-paper p-6 rounded-lg">
            <div className="text-display font-bold text-neutral-charcoal">Display Text (3rem)</div>
            <div className="text-h1 font-bold text-neutral-charcoal">H1 Text (2.25rem)</div>
            <div className="text-h2 font-semibold text-neutral-charcoal">H2 Text (1.5rem)</div>
            <div className="text-h3 font-semibold text-neutral-charcoal">H3 Text (1.25rem)</div>
            <div className="text-body-lg text-neutral-charcoal">Body Large (1.125rem)</div>
            <div className="text-body text-neutral-charcoal">Body Text (1rem)</div>
            <div className="text-body-sm text-neutral-shadow">Body Small (0.875rem)</div>
            <div className="text-caption text-neutral-shadow">Caption Text (0.75rem)</div>
          </div>
        </section>

        {/* Spacing Test */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-neutral-white">Spacing</h2>
          <div className="bg-neutral-paper p-6 rounded-lg">
            <div className="space-y-xs">
              <div className="bg-ai-primary text-white p-xs rounded">XS Padding (0.25rem)</div>
              <div className="bg-ai-primary text-white p-sm rounded">SM Padding (0.5rem)</div>
              <div className="bg-ai-primary text-white p-md rounded">MD Padding (1rem)</div>
              <div className="bg-ai-primary text-white p-lg rounded">LG Padding (1.5rem)</div>
              <div className="bg-ai-primary text-white p-xl rounded">XL Padding (3rem)</div>
            </div>
          </div>
        </section>

        {/* Interactive Elements */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-neutral-white">Interactive Elements</h2>
          <div className="flex flex-wrap gap-4">
            <button className="bg-ai-primary text-white px-lg py-md rounded-lg font-semibold hover:bg-ai-primary/90 transition-colors">
              Primary Button
            </button>
            <button className="border-2 border-ai-secondary text-ai-secondary px-lg py-md rounded-lg font-semibold hover:bg-ai-secondary/10 transition-colors">
              Secondary Button
            </button>
            <button className="bg-semantic-error text-white px-lg py-md rounded-lg font-semibold hover:opacity-90 transition-opacity">
              Error Button
            </button>
          </div>
        </section>

        {/* Background Gradient Options - Rich, Non-White */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-neutral-white">Rich Background Gradients (No White)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gradient-neural-twilight p-6 rounded-lg border border-neutral-shadow">
              <h3 className="font-semibold text-neutral-white mb-2">Neural Twilight</h3>
              <p className="text-sm text-neutral-white opacity-90">Deep gray gradient (current)</p>
            </div>
            <div className="bg-gradient-quantum-aurora p-6 rounded-lg border border-neutral-shadow">
              <h3 className="font-semibold text-neutral-white mb-2">Quantum Aurora</h3>
              <p className="text-sm text-neutral-white opacity-90">Dark base with AI color hints</p>
            </div>
            <div className="bg-gradient-neural-ocean p-6 rounded-lg border border-neutral-shadow">
              <h3 className="font-semibold text-neutral-white mb-2">Neural Ocean</h3>
              <p className="text-sm text-neutral-white opacity-90">Deep blue-teal gradient</p>
            </div>
            <div className="bg-gradient-ai-spectrum p-6 rounded-lg border border-neutral-shadow">
              <h3 className="font-semibold text-neutral-white mb-2">AI Spectrum</h3>
              <p className="text-sm text-neutral-white opacity-90">Full brand color spectrum</p>
            </div>
            <div className="bg-gradient-neural-slate p-6 rounded-lg border border-neutral-shadow">
              <h3 className="font-semibold text-neutral-white mb-2">Neural Slate</h3>
              <p className="text-sm text-neutral-white opacity-90">Professional slate gradient</p>
            </div>
          </div>
        </section>

        {/* Status Check */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-neutral-white">Status Check</h2>
          <div className="bg-neutral-paper p-6 rounded-lg space-y-2">
            <div className="text-neutral-charcoal">
              <strong>✅ If you can see the Neural Spectrum colors above:</strong> Design system is working correctly
            </div>
            <div className="text-neutral-charcoal">
              <strong>❌ If everything is black/white/gray:</strong> CSS is not loading properly
            </div>
            <div className="text-neutral-shadow">
              Check browser console (F12) for any CSS loading errors
            </div>
            <div className="text-sm text-neutral-shadow mt-4 p-4 bg-neutral-fog rounded-lg">
              <strong>aideator Neural Spectrum:</strong> A sophisticated design system for multi-model AI comparison platforms. Colors reflect intelligence, innovation, and trust - perfect for professional yet approachable AI interfaces.
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}