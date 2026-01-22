import React, { useState } from 'react';
import { Menu, X, Copy, Check, Terminal, ArrowRight, Github } from 'lucide-react';
import { CommandExample } from './types';

// --- Components ---

const Navbar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-50">
      <div className="h-16 flex items-center justify-between px-6 md:px-10">
        <div className="flex items-center gap-2 font-bold text-xl tracking-tighter">
          <Terminal className="w-6 h-6" />
          <span>nlsh</span>
        </div>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8 text-sm">
          <a href="#install" className="hover:text-white text-muted transition-colors">Install</a>
          <a href="#usage" className="hover:text-white text-muted transition-colors">Usage</a>
          <a href="#commands" className="hover:text-white text-muted transition-colors">Commands</a>
          <a href="https://github.com/junaid-mahmood/nlsh" target="_blank" rel="noopener noreferrer" className="hover:text-white text-muted transition-colors">GitHub</a>
        </div>

        {/* Mobile Toggle */}
        <button className="md:hidden p-2" onClick={() => setIsOpen(!isOpen)}>
          {isOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Mobile Nav */}
      {isOpen && (
        <div className="md:hidden border-t border-border bg-background absolute w-full left-0 px-6 py-4 border-b">
          <div className="flex flex-col gap-4 text-sm">
            <a href="#install" onClick={() => setIsOpen(false)}>Install</a>
            <a href="#usage" onClick={() => setIsOpen(false)}>Usage</a>
            <a href="#commands" onClick={() => setIsOpen(false)}>Commands</a>
            <a href="https://github.com/junaid-mahmood/nlsh" target="_blank" rel="noopener noreferrer">GitHub</a>
          </div>
        </div>
      )}
    </nav>
  );
};

const InstallSection: React.FC = () => {
  const [mode, setMode] = useState<'install' | 'uninstall'>('install');

  const installCmd = `curl -fsSL https://raw.githubusercontent.com/junaid-mahmood/nlsh/main/install.sh | bash`;
  const uninstallCmd = `curl -fsSL https://raw.githubusercontent.com/junaid-mahmood/nlsh/main/uninstall.sh | bash`;

  return (
    <div className="w-full mt-8">
      <div className="flex border border-border border-b-0 w-fit rounded-t-sm overflow-hidden">
        <button
          onClick={() => setMode('install')}
          className={`px-6 py-2 text-sm font-medium transition-colors ${mode === 'install' ? 'bg-surface text-white' : 'bg-transparent text-muted hover:text-white hover:bg-white/5'}`}
        >
          Install
        </button>
        <button
          onClick={() => setMode('uninstall')}
          className={`px-6 py-2 text-sm font-medium transition-colors border-l border-border ${mode === 'uninstall' ? 'bg-surface text-white' : 'bg-transparent text-muted hover:text-white hover:bg-white/5'}`}
        >
          Uninstall
        </button>
      </div>
      <div className="bg-surface border border-border p-6 rounded-b-sm rounded-tr-sm relative group shadow-[0_0_50px_-12px_rgba(168,85,247,0.25)]">
        <code className="text-sm break-all text-neutral-300 font-mono leading-relaxed block pr-8">
          {mode === 'install' ? installCmd : uninstallCmd}
        </code>
        <button
          onClick={() => {
            navigator.clipboard.writeText(mode === 'install' ? installCmd : uninstallCmd);
          }}
          className="absolute right-3 top-3 p-2 hover:bg-white/10 rounded-sm transition-colors text-muted hover:text-white opacity-0 group-hover:opacity-100 focus:opacity-100"
        >
          <Copy size={16} />
        </button>
      </div>
      <p className="mt-4 text-xs text-muted flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse"></span>
        macOS or Linux required. Windows not currently supported.
      </p>
    </div>
  );
};

const TerminalDemo: React.FC = () => {
  return (
    <div className="w-full relative group">
      <img src="/demo.gif" alt="nlsh demo" className="w-full rounded-lg shadow-2xl border border-[#333]" />
    </div>
  );
};

const FeatureItem: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="flex gap-4 mb-8 items-start group hover:bg-surface/50 p-4 rounded-lg transition-colors -ml-4">
    <div>
      <h3 className="text-white font-bold mb-1 font-mono">{title}</h3>
      <p className="text-muted leading-relaxed text-sm">
        {children}
      </p>
    </div>
  </div>
);

export default function App() {
  const examples: CommandExample[] = [
    { natural: "list all python files", command: 'find . -name "*.py"' },
    { natural: "git commit with message fixed bug", command: 'git commit -m "fixed bug"' },
    { natural: "count lines in main.go", command: 'wc -l main.go' },
    { natural: "kill process running on port 3000", command: 'lsof -t -i:3000 | xargs kill' },
  ];

  return (
    <div className="min-h-screen bg-[#050505] text-text font-mono flex flex-col items-center">
      {/* Main Container with borders (The Lines) */}
      <div className="w-full max-w-[1400px] border-l border-r border-border min-h-screen bg-background relative shadow-2xl flex flex-col">

        <Navbar />

        <main className="flex-grow">

          {/* Hero Section - Split Layout */}
          <section className="border-b border-border" id="install">
            <div className="grid lg:grid-cols-2">
              {/* Left: Content */}
              <div className="p-8 md:p-16 lg:p-20 xl:p-24 flex flex-col justify-center border-b lg:border-b-0 lg:border-r border-border">
                <div className="inline-flex items-center gap-2 px-3 py-1 w-fit bg-white/10 text-white border border-white/20 text-xs font-bold uppercase tracking-widest mb-8 rounded-full">
                  Open Source
                </div>

                <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tighter mb-8 text-white leading-[1.1]">
                  Talk to your shell.
                </h1>

                <p className="text-lg text-muted leading-relaxed mb-10 max-w-lg">
                  A terminal interface that translates plain English into shell commands. Stop memorizing flags. Just type what you want.
                </p>

                <InstallSection />
              </div>

              {/* Right: Demo */}
              <div className="bg-[#0f0f0f] p-8 md:p-16 lg:p-20 flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
                <div className="relative z-10 w-full max-w-lg">
                  <TerminalDemo />
                </div>
              </div>
            </div>
          </section>

          {/* Usage Section */}
          <section className="border-b border-border" id="usage">
            <div className="p-8 md:p-16 lg:p-24">
              <div className="max-w-4xl mx-auto">
                <div className="grid md:grid-cols-12 gap-12 md:gap-24">
                  <div className="md:col-span-4">
                    <h2 className="text-2xl font-bold text-white mb-6 tracking-tight">Usage</h2>
                    <p className="text-muted mb-8 text-sm leading-loose">
                      Start the session by typing <code className="text-white bg-surface border border-border px-1.5 py-0.5 rounded text-xs mx-1">nlsh</code>.
                      <br /><br />
                      The shell will interpret your natural language and convert it to the appropriate bash command.
                    </p>

                    <div className="border-l-2 border-border pl-6 py-2 space-y-4">
                      <div>
                        <div className="text-xs text-muted uppercase tracking-widest mb-1">Platform</div>
                        <div className="text-white flex items-center gap-2"><Check size={14} className="text-green-500" /> macOS / Linux</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted uppercase tracking-widest mb-1">Runtime</div>
                        <div className="text-white flex items-center gap-2"><Check size={14} className="text-green-500" /> Python 3.8+</div>
                      </div>
                    </div>
                  </div>

                  <div className="md:col-span-8">
                    <div className="mb-8 flex items-center gap-3 text-white border-b border-border pb-4">
                      <Terminal size={20} />
                      <span className="font-bold">Command Examples</span>
                    </div>

                    <div className="space-y-4">
                      {examples.map((ex, i) => (
                        <div key={i} className="group p-4 bg-surface/40 hover:bg-surface border border-transparent hover:border-border transition-all rounded-lg">
                          <div className="text-neutral-300 font-medium mb-2">{ex.natural}</div>
                          <div className="flex items-center gap-3 text-muted">
                            <ArrowRight size={14} className="text-purple-500" />
                            <code className="text-green-400 font-mono text-xs md:text-sm bg-black/40 px-3 py-1.5 rounded w-full md:w-auto block overflow-x-auto">
                              {ex.command}
                            </code>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Commands Grid */}
          <section className="border-b border-border" id="commands">
            <div className="p-8 md:p-16 lg:p-24">
              <div className="max-w-4xl mx-auto">
                <h2 className="text-2xl font-bold text-white mb-12 tracking-tight">System Commands</h2>

                <div className="grid md:grid-cols-2 gap-x-12 gap-y-8">
                  <div>
                    <FeatureItem title="!api">
                      Change your LLM provider API key securely. We currently support Gemini.
                    </FeatureItem>
                    <FeatureItem title="!help">
                      Show the help menu listing all available special commands and keyboard shortcuts.
                    </FeatureItem>
                  </div>
                  <div>
                    <FeatureItem title="!cmd">
                      Run a raw shell command directly without natural language processing. Useful for mixing workflows.
                    </FeatureItem>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Privacy / Source */}
          <section className="p-8 md:p-16 lg:p-24 bg-surface/10">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="text-2xl font-bold text-white mb-6">Open Source & Private</h2>
              <p className="text-muted leading-relaxed max-w-2xl mx-auto mb-10">
                Your privacy matters. nlsh operates locally and only sends your prompts to the AI provider you choose.
                We do not store your history. The code is 100% open source.
              </p>
              <a href="https://github.com/junaid-mahmood/nlsh" className="inline-flex items-center gap-2 bg-white text-black px-6 py-3 rounded-full font-bold hover:bg-gray-200 transition-colors">
                <span className="w-5 h-5"><Github size={20} /></span>
                Star on GitHub
              </a>
            </div>
          </section>
        </main>

        <footer className="border-t border-border p-8 md:p-12 text-center text-sm text-muted">
          <div className="flex justify-center gap-6 mb-4">
            <a href="#" className="hover:text-white transition-colors">License</a>
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Contact</a>
          </div>
          <div className="opacity-50">© 2024 nlsh Project. Built for developers. By Junaid :)</div>
        </footer>
      </div>
    </div>
  );
}