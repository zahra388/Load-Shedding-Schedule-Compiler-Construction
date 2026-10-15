/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { 
  Play, 
  RotateCcw, 
  Download, 
  BookOpen, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  FileCode, 
  Layers, 
  ListOrdered, 
  ShieldCheck, 
  Cpu, 
  Sparkles, 
  Calendar, 
  Terminal, 
  Check, 
  Copy,
  ChevronRight
} from 'lucide-react';

interface TestCase {
  id: string;
  fileName: string;
  expectedSummary: string;
  code: string;
}

interface CompilerResponse {
  success: boolean;
  rawOutput: string;
  stderr: string;
  phases: {
    tokens: string;
    ast: string;
    symbolTable: string;
    semantic: string;
    tac: string;
    optimizedTac: string;
    result: string;
  };
}

const DEFAULT_PROGRAM = `// Standard Weekday Scenario - LoadSheddingLang
// Compiler Construction Lab Project | JUW

feeder Gulberg loss 18% group A max 4 hours;
feeder ModelTown loss 35% group B max 6 hours;
feeder Services group A max 0 hours;
exempt feeder Services;

block Weekday start 08:00 end 16:00 slot 2 hours rotation A, B;
`;

export default function App() {
  const [code, setCode] = useState(DEFAULT_PROGRAM);
  const [activeTab, setActiveTab] = useState<'result' | 'tokens' | 'ast' | 'symtab' | 'semantic' | 'tac' | 'optimizedTac' | 'cli'>('result');
  const [isLoading, setIsLoading] = useState(false);
  const [compilerData, setCompilerData] = useState<CompilerResponse | null>(null);
  const [tests, setTests] = useState<TestCase[]>([]);
  const [selectedTestId, setSelectedTestId] = useState<string>('custom');
  const [showVivaModal, setShowVivaModal] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; output: string }>>({});
  const [isRunningAllTests, setIsRunningAllTests] = useState(false);
  const [copied, setCopied] = useState(false);

  // Fetch test cases on mount
  useEffect(() => {
    fetch('/api/tests')
      .then(r => r.json())
      .then(d => {
        if (d.tests) setTests(d.tests);
      })
      .catch(console.error);

    // Initial compile
    handleCompile(DEFAULT_PROGRAM);
  }, []);

  const handleCompile = async (sourceCode: string = code) => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: sourceCode })
      });
      const data: CompilerResponse = await res.json();
      setCompilerData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectTest = (test: TestCase) => {
    setSelectedTestId(test.id);
    setCode(test.code);
    handleCompile(test.code);
  };

  const handleRunAllTests = async () => {
    setIsRunningAllTests(true);
    const results: Record<string, { success: boolean; output: string }> = {};

    for (const t of tests) {
      try {
        const res = await fetch('/api/compile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: t.code })
        });
        const data: CompilerResponse = await res.json();
        // Check if output matches expected behavior
        const isExpectedSuccess = ['test01', 'test02', 'test03', 'test09'].includes(t.id);
        const passed = isExpectedSuccess ? data.success : !data.success;
        results[t.id] = {
          success: passed,
          output: data.rawOutput
        };
      } catch (e: any) {
        results[t.id] = { success: false, output: e.message };
      }
    }
    setTestResults(results);
    setIsRunningAllTests(false);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadZip = () => {
    window.location.href = '/api/download-zip';
  };

  const lines = code.split('\n');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* 1. Header Bar following Top Bar Contract */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-3.5 flex items-center justify-between gap-8 shrink-0">
        <div className="flex items-center gap-3 whitespace-nowrap shrink-0">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              Load-Shedding Schedule Compiler
            </h1>
            <p className="text-xs text-slate-400">
              JUW Compiler Construction Lab · Lexer, Parser, AST, TAC & Optimizer
            </p>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-6 text-xs text-slate-400 font-medium whitespace-nowrap shrink-0">
          <button 
            onClick={() => setShowVivaModal(true)} 
            className="hover:text-blue-400 transition-colors flex items-center gap-1.5 cursor-pointer text-slate-300"
          >
            <BookOpen className="w-4 h-4 text-blue-400" />
            <span>Viva & Lab Defense Guide (Roman Urdu)</span>
          </button>
          <span className="text-slate-700">|</span>
          <span className="text-slate-400">PLY 3.11 · Python 3.10 · Rules R1–R7</span>
        </nav>

        <div className="flex items-center gap-2.5 whitespace-nowrap shrink-0">
          <button
            onClick={downloadZip}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors flex items-center gap-1.5 cursor-pointer"
            title="Download full runnable LoadSheddingCompiler folder zipped for LMS submission"
          >
            <Download className="w-4 h-4 text-emerald-400" />
            <span>Download Project (.ZIP)</span>
          </button>

          <button
            onClick={() => handleCompile(code)}
            disabled={isLoading}
            className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow-md shadow-blue-600/30 transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <Play className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Compiling...' : 'Compile & Schedule'}</span>
          </button>
        </div>
      </header>

      {/* 2. Main Content Split Layout */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left Panel: Code Editor */}
        <div className="w-full lg:w-1/2 border-r border-slate-800 flex flex-col bg-slate-900/40">
          {/* Editor Header Toolbar */}
          <div className="border-b border-slate-800 px-4 py-2.5 bg-slate-900/60 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                Source Editor
              </span>
              <span className="text-xs text-slate-500 font-mono">LoadSheddingLang</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={copyToClipboard}
                className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs flex items-center gap-1 transition-colors cursor-pointer"
                title="Copy source code"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span className="text-[11px]">{copied ? 'Copied' : 'Copy'}</span>
              </button>

              <button
                onClick={() => {
                  setCode(DEFAULT_PROGRAM);
                  setSelectedTestId('custom');
                  handleCompile(DEFAULT_PROGRAM);
                }}
                className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs flex items-center gap-1 transition-colors cursor-pointer"
                title="Reset to standard example"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span className="text-[11px]">Reset</span>
              </button>
            </div>
          </div>

          {/* Test Case Quick Bar */}
          <div className="border-b border-slate-800 bg-slate-950/60 px-4 py-2 flex items-center gap-2 overflow-x-auto text-xs">
            <span className="text-slate-400 shrink-0 font-medium">Tests:</span>
            {tests.map(t => (
              <button
                key={t.id}
                onClick={() => handleSelectTest(t)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-all shrink-0 cursor-pointer ${
                  selectedTestId === t.id
                    ? 'bg-blue-600 text-white font-semibold'
                    : 'bg-slate-800/80 hover:bg-slate-700 text-slate-300'
                }`}
              >
                {t.id}
              </button>
            ))}
            <button
              onClick={handleRunAllTests}
              disabled={isRunningAllTests}
              className="ml-auto px-2.5 py-1 rounded bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 text-xs font-semibold shrink-0 cursor-pointer flex items-center gap-1"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{isRunningAllTests ? 'Testing...' : 'Audit All 9'}</span>
            </button>
          </div>

          {/* Editor Textarea with line numbers */}
          <div className="flex-1 flex overflow-hidden bg-slate-950 font-mono text-xs">
            {/* Line numbers */}
            <div className="w-12 py-4 select-none bg-slate-900/30 border-r border-slate-800 text-slate-600 text-right pr-3 flex flex-col font-mono text-xs leading-6">
              {lines.map((_, i) => (
                <span key={i}>{i + 1}</span>
              ))}
            </div>

            {/* Editable code */}
            <textarea
              value={code}
              onChange={(e) => {
                setCode(e.target.value);
                setSelectedTestId('custom');
              }}
              className="flex-1 p-4 bg-transparent text-slate-200 outline-none resize-none leading-6 font-mono text-xs selection:bg-blue-600"
              spellCheck={false}
              placeholder="Type LoadSheddingLang code here..."
            />
          </div>

          {/* Lexicon Quick Reference */}
          <div className="border-t border-slate-800 bg-slate-900/60 px-4 py-2.5 text-[11px] text-slate-400 flex items-center justify-between">
            <div className="flex items-center gap-2 truncate">
              <span className="font-semibold text-slate-300">Urdu Keywords:</span>
              <span className="text-slate-400 truncate">
                giroh (group) · mustasna (exempt) · shuru (start) · khatam (end) · waqfa (slot) · bari (rotation) · nuqsan (loss)
              </span>
            </div>
            <span className="text-slate-500 shrink-0 font-mono">Lines: {lines.length}</span>
          </div>
        </div>

        {/* Right Panel: Compiler Pipeline & Outputs */}
        <div className="w-full lg:w-1/2 flex flex-col bg-slate-950">
          {/* Phase Navigation Tabs */}
          <div className="border-b border-slate-800 bg-slate-900/70 px-2 py-1.5 flex items-center gap-1 overflow-x-auto shrink-0">
            {[
              { id: 'result', label: 'Result & Timetable', icon: Calendar },
              { id: 'tokens', label: 'Tokens', icon: ListOrdered },
              { id: 'ast', label: 'AST', icon: Layers },
              { id: 'symtab', label: 'Symbol Table', icon: FileCode },
              { id: 'semantic', label: 'Semantic (R1-R7)', icon: ShieldCheck },
              { id: 'tac', label: 'TAC (IR)', icon: Cpu },
              { id: 'optimizedTac', label: 'Optimized TAC', icon: Sparkles },
              { id: 'cli', label: 'Raw CLI Output', icon: Terminal },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 whitespace-nowrap shrink-0 cursor-pointer ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-sm font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Phase Content Viewport */}
          <div className="flex-1 p-5 overflow-y-auto">
            {/* Status notification banner if error occurred */}
            {compilerData && !compilerData.success && (
              <div className="mb-4 p-3.5 rounded-lg bg-red-950/60 border border-red-800/80 text-red-200 flex items-start gap-3 text-xs leading-relaxed">
                <XCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-red-100 mb-1">Compilation Stopped</div>
                  <div className="text-red-300 font-mono whitespace-pre-wrap">
                    {compilerData.rawOutput.split('Compilation stopped.')[0].split('\n').filter(l => l.includes('error') || l.includes('Error')).join('\n') || 'Errors found in code.'}
                  </div>
                </div>
              </div>
            )}

            {/* Tab: RESULT */}
            {activeTab === 'result' && (
              <div className="space-y-6">
                {compilerData?.phases.result ? (
                  <div>
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                      <div>
                        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          Generated Schedule & Timetable
                        </h2>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Evaluated by TAC Execution Engine (Zero eval() usage)
                        </p>
                      </div>

                      <div className="flex items-center gap-2 text-xs">
                        <span className="px-2.5 py-1 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800 font-medium">
                          Rules R1–R7 Verified
                        </span>
                      </div>
                    </div>

                    {/* Preformatted timetable result */}
                    <div className="mt-4 p-4 rounded-xl bg-slate-900/90 border border-slate-800 font-mono text-xs leading-relaxed whitespace-pre-wrap text-slate-200 shadow-inner">
                      {compilerData.phases.result}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-500 text-xs">
                    No result available. Correct any errors above and compile again.
                  </div>
                )}
              </div>
            )}

            {/* Tab: TOKENS */}
            {activeTab === 'tokens' && (
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                  <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Lexical Analyzer Token Stream (ply.lex)
                  </h2>
                  <span className="text-xs text-slate-500 font-mono">Phase 1 of 7</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-6">
                  {compilerData?.phases.tokens || 'No tokens generated.'}
                </div>
              </div>
            )}

            {/* Tab: AST */}
            {activeTab === 'ast' && (
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                  <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Abstract Syntax Tree (AST Hierarchy)
                  </h2>
                  <span className="text-xs text-slate-500 font-mono">Phase 2 of 7</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-blue-300 whitespace-pre-wrap leading-relaxed">
                  {compilerData?.phases.ast || 'No AST available.'}
                </div>
              </div>
            )}

            {/* Tab: SYMBOL TABLE */}
            {activeTab === 'symtab' && (
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                  <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Symbol Table Records (Scope & Declarations)
                  </h2>
                  <span className="text-xs text-slate-500 font-mono">Phase 3 of 7</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed overflow-x-auto">
                  {compilerData?.phases.symbolTable || 'Symbol table empty.'}
                </div>
              </div>
            )}

            {/* Tab: SEMANTIC */}
            {activeTab === 'semantic' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Semantic Verification Auditor (Rules R1–R7)
                  </h2>
                  <span className="text-xs text-slate-500 font-mono">Phase 4 of 7</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  {[
                    { r: 'R1', title: 'Unique Feeder & Group', desc: 'No duplicate feeders; each belongs to exactly one group.' },
                    { r: 'R2', title: 'Exempt Feeders', desc: 'Exempt feeders receive 0 hours shedding; must be declared.' },
                    { r: 'R3', title: 'Max Shedding Hours', desc: 'Calculated shedding cannot exceed permitted max hours.' },
                    { r: 'R4', title: 'Exact Slot Division', desc: 'Block duration divides evenly into slot length (e.g. 8h % 2h == 0).' },
                    { r: 'R5', title: 'Valid Group Rotation', desc: 'All rotation groups contain feeders; all feeder groups appear.' },
                    { r: 'R6', title: 'Detailed Max Diagnostics', desc: 'Names block, feeder, actual calculated hours, and limit.' },
                    { r: 'R7', title: '24-Hour Clock Validity', desc: '00:00 to 23:59 valid ranges and positive slot durations.' }
                  ].map(rule => (
                    <div key={rule.r} className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex items-start gap-2.5">
                      <span className="font-mono font-bold text-blue-400 shrink-0">{rule.r}</span>
                      <div>
                        <div className="font-semibold text-slate-200">{rule.title}</div>
                        <div className="text-slate-400 text-[11px] mt-0.5">{rule.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap">
                  {compilerData?.phases.semantic || 'Semantic status unknown.'}
                </div>
              </div>
            )}

            {/* Tab: TAC */}
            {activeTab === 'tac' && (
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                  <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Three-Address Code (TAC Intermediate Representation)
                  </h2>
                  <span className="text-xs text-slate-500 font-mono">Phase 5 of 7</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-amber-300 whitespace-pre-wrap leading-relaxed">
                  {compilerData?.phases.tac || 'No TAC code generated.'}
                </div>
              </div>
            )}

            {/* Tab: OPTIMIZED TAC */}
            {activeTab === 'optimizedTac' && (
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                  <div>
                    <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                      Optimized TAC (Constant Folding & Dead Code Elimination)
                    </h2>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Folded constant arithmetic: 960 - 480 → 480, 480 / 60 → 8, 8 / 2 → 4 slots
                    </p>
                  </div>
                  <span className="text-xs text-slate-500 font-mono">Phase 6 of 7</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-emerald-300 whitespace-pre-wrap leading-relaxed">
                  {compilerData?.phases.optimizedTac || 'No optimized TAC available.'}
                </div>
              </div>
            )}

            {/* Tab: CLI */}
            {activeTab === 'cli' && (
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                  <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Standard Terminal Output (python main.py)
                  </h2>
                  <span className="text-xs text-slate-500 font-mono">Full Trace</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {compilerData?.rawOutput || 'No output.'}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3. Viva Defense & Lab Questions Modal */}
      {showVivaModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-blue-400" />
                  Lab Viva & Defense Guide (Roman Urdu)
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  BS Computer Science & Software Engineering · JUW Compiler Construction Lab
                </p>
              </div>
              <button
                onClick={() => setShowVivaModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-5 text-xs text-slate-300 leading-relaxed">
              <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-900/50">
                <div className="font-bold text-blue-200 mb-1">Q1: Lexer ka kya kaam hai aur Urdu keywords kaise handle hotay hain?</div>
                <div>
                  Lexer source code ko character by character parh kar <strong>Tokens</strong> banata hai. Humare lexer mein English aur Roman Urdu (jaise <code>group</code> aur <code>giroh</code>, <code>slot</code> aur <code>waqfa</code>) dono ek hi reserved-word dictionary mein mapped hain, is liye dono se exact same token banta hai. Invalid characters pe lexer crash hone ke bajaye error report karta hai.
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-900/50">
                <div className="font-bold text-blue-200 mb-1">Q2: Parser aur AST Node mein kya farq hai?</div>
                <div>
                  Parser CFG grammar rules ke mutabiq check karta hai ke syntax theek hai ya nahi. Agar theek ho, toh woh <strong>Abstract Syntax Tree (AST)</strong> banata hai jahan har node (jaise <code>FeederNode</code>, <code>ExemptNode</code>, <code>ScheduleBlockNode</code>) language ke statement ka data structure hoti hai. Semicolon missing hone pe <code>error</code> recovery rule use hoti hai.
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-900/50">
                <div className="font-bold text-blue-200 mb-1">Q3: Rules R1 se R7 kaise check hote hain?</div>
                <div>
                  Semantic Analyzer phase mein check hota hai:
                  <ul className="list-disc pl-4 mt-1 space-y-0.5 text-slate-400">
                    <li><strong>R1:</strong> Feeder ka naam unique hona chahiye aur 1 hi group mein ho.</li>
                    <li><strong>R2:</strong> Hospital/Exempt feeder ko hamesha 0 ghantay shedding mile.</li>
                    <li><strong>R3 & R6:</strong> Calculated hours max permitted hours se exceed na karein.</li>
                    <li><strong>R4:</strong> Total duration slot length pe exact divide ho (e.g. 8 / 2 = 4 slots).</li>
                    <li><strong>R5:</strong> Rotation mein diye gaye sabhi groups valid hon.</li>
                    <li><strong>R7:</strong> 24-hour clock (00:00 se 23:59) valid ho.</li>
                  </ul>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-900/50">
                <div className="font-bold text-blue-200 mb-1">Q4: TAC aur Optimization (Constant Folding & DCE) kya karti hain?</div>
                <div>
                  Three-Address Code (TAC) machine-independent Intermediate Representation hai. Optimization phase mein Constant Folding compile-time pe constant arithmetic (jaise <code>960 - 480 = 480</code>, <code>480 / 60 = 8</code>, <code>8 / 2 = 4 slots</code>) ko pehle hi evaluate kar leti hai, aur Dead Code Elimination bekar temporaries ko nikal deti hai.
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-900/50">
                <div className="font-bold text-blue-200 mb-1">Q5: Timetable hardcoded hai ya execute hota hai?</div>
                <div>
                  Timetable bilkul hardcoded nahi hai! Humara <code>tac_executor.py</code> generated TAC instructions ko step-by-step interpret karta hai bina Python <code>eval()</code> use kiye, aur real calculation se final timetable table aur feeder totals print karta hai.
                </div>
              </div>
            </div>

            <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/50 flex justify-end">
              <button
                onClick={() => setShowVivaModal(false)}
                className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs cursor-pointer"
              >
                Close Guide
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4. Test Audit Results Drawer / Banner */}
      {Object.keys(testResults).length > 0 && (
        <div className="border-t border-slate-800 bg-slate-900/90 px-6 py-3 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-200">Test Suite Audit (9 Cases):</span>
            <div className="flex items-center gap-1.5 ml-2">
              {tests.map(t => {
                const res = testResults[t.id];
                if (!res) return null;
                return (
                  <span
                    key={t.id}
                    title={`${t.id}: ${res.success ? 'PASSED' : 'FAILED'}`}
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold flex items-center gap-1 ${
                      res.success
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        : 'bg-red-950 text-red-300 border border-red-800'
                    }`}
                  >
                    {res.success ? '✓' : '✗'} {t.id}
                  </span>
                );
              })}
            </div>
          </div>
          <button
            onClick={() => setTestResults({})}
            className="text-slate-400 hover:text-white text-xs cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}
