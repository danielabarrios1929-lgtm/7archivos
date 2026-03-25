"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Uploader } from '@/components/Uploader';
import { MatrixSuprema } from '@/components/MatrixSuprema';
import { Sparkles, Database, FileSearch, ShieldCheck, AlertCircle, BrainCircuit, Cpu, Layers, GitMerge, CheckCircle2 } from 'lucide-react';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "");
const API_URL = `${BACKEND_URL}/api/v1/analysis/process`;


const PROCESSING_PHASES = [
  { icon: FileSearch, text: "Extrayendo texto de los documentos...", detail: "Procesando PDFs, Word y Excel" },
  { icon: Layers, text: "Dividiendo en fragmentos inteligentes...", detail: "Partiendo en partes manejables para la IA" },
  { icon: BrainCircuit, text: "Gemini analizando fragmento 1...", detail: "Motor principal: Gemini 2.5 Flash" },
  { icon: BrainCircuit, text: "Gemini analizando fragmentos en paralelo...", detail: "Procesando todas las partes simultáneamente" },
  { icon: Cpu, text: "Groq sintetizando resultados...", detail: "Fusionando hallazgos de todos los fragmentos" },
  { icon: GitMerge, text: "Construyendo matriz pedagógica final...", detail: "Integrando categorías y pilares de calidad" },
  { icon: CheckCircle2, text: "Casi listo...", detail: "Generando reporte final en PDF" },
];

function ProcessingScreen() {
  const [phaseIdx, setPhaseIdx] = useState(0);
  const [progress, setProgress] = useState(0);
  const [dots, setDots] = useState('');

  useEffect(() => {
    const iv = setInterval(() => setPhaseIdx(p => (p + 1) % PROCESSING_PHASES.length), 4000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    const iv = setInterval(() => setProgress(p => p < 90 ? p + Math.random() * 2 : p), 800);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    const iv = setInterval(() => setDots(d => d.length >= 3 ? '' : d + '.'), 500);
    return () => clearInterval(iv);
  }, []);

  const Phase = PROCESSING_PHASES[phaseIdx];
  const PhaseIcon = Phase.icon;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#020205]"
    >
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/10 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 blur-[120px] rounded-full animate-pulse" style={{ animationDelay: '1.5s' }} />
      </div>

      <div className="relative z-10 max-w-lg w-full mx-6 text-center space-y-10">
        {/* Icono animado */}
        <div className="relative mx-auto w-28 h-28">
          <svg className="absolute inset-0 w-full h-full animate-spin" style={{ animationDuration: '3s' }} viewBox="0 0 112 112">
            <circle cx="56" cy="56" r="52" fill="none" stroke="url(#g1)" strokeWidth="2" strokeDasharray="50 280" strokeLinecap="round" />
            <defs>
              <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#3b82f6" />
                <stop offset="100%" stopColor="#8b5cf6" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-4 bg-gradient-to-br from-blue-600/20 to-purple-600/20 border border-white/10 rounded-full flex items-center justify-center backdrop-blur-xl">
            <AnimatePresence mode="wait">
              <motion.div key={phaseIdx} initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 1.5 }} transition={{ duration: 0.3 }}>
                <PhaseIcon className="w-9 h-9 text-blue-400" />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/* Texto */}
        <div className="space-y-3">
          <p className="text-[10px] font-black tracking-[0.3em] uppercase text-blue-400">IA Procesando{dots}</p>
          <AnimatePresence mode="wait">
            <motion.h2 key={phaseIdx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="text-xl font-black text-white">
              {Phase.text}
            </motion.h2>
          </AnimatePresence>
          <AnimatePresence mode="wait">
            <motion.p key={phaseIdx + 'd'} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-gray-500 text-sm">
              {Phase.detail}
            </motion.p>
          </AnimatePresence>
        </div>

        {/* Barra de progreso */}
        <div className="space-y-2">
          <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
            <motion.div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full" animate={{ width: `${progress}%` }} transition={{ duration: 0.8, ease: 'easeOut' }} />
          </div>
          <p className="text-[10px] text-gray-600 font-mono">{Math.round(progress)}% completado</p>
        </div>

        {/* Puntos de progreso */}
        <div className="flex justify-center gap-1.5">
          {PROCESSING_PHASES.map((_, i) => (
            <div key={i} className={`h-1 rounded-full transition-all duration-500 ${i === phaseIdx ? 'w-6 bg-blue-400' : i < phaseIdx ? 'w-2 bg-blue-700' : 'w-2 bg-white/10'}`} />
          ))}
        </div>

        <p className="text-[10px] text-gray-600 uppercase tracking-widest">
          Los documentos grandes se dividen en partes y se procesan en paralelo
        </p>
      </div>
    </motion.div>
  );
}

export default function Home() {
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const startAnalysis = async (formData: FormData, useLocalFolder: boolean = false) => {
    setIsAnalyzing(true);
    setError(null);
    try {
      const endpoint = useLocalFolder ? `${BACKEND_URL}/api/v1/analysis/process-local-folder` : API_URL;
      const response = await fetch(endpoint, { method: 'POST', body: formData });
      if (!response.ok) {
        let msg = "Fallo crítico en el motor de auditoría.";
        try {
          const e = await response.json();
          msg = e?.detail?.error || e?.detail || msg;
        } catch { msg = `Error ${response.status}: ${response.statusText}`; }
        throw new Error(msg);
      }
      setAnalysisData(await response.json());
    } catch (err: any) {
      setError(err.message === "Failed to fetch"
        ? "Error de conexión: No se pudo contactar con el servidor."
        : err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#020205] text-white selection:bg-blue-500/30 selection:text-white">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 -left-[10%] w-[60%] h-[60%] bg-blue-600/5 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-0 -right-[10%] w-[60%] h-[60%] bg-purple-600/5 blur-[120px] rounded-full animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-150 contrast-150 mix-blend-overlay" />
      </div>

      {mounted && (
        <>
          {/* Pantalla de procesamiento */}
          <AnimatePresence>
            {isAnalyzing && <ProcessingScreen />}
          </AnimatePresence>

          <AnimatePresence mode="wait">
            {!analysisData ? (
              <motion.div key="uploader" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }} className="relative z-10 pt-24 px-6">
                <div className="max-w-4xl mx-auto text-center space-y-6 mb-16">
                  <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} className="inline-flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full mb-8">
                    <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                    <span className="text-[10px] font-black tracking-widest uppercase text-blue-300">PTAFI-AI v2.0 · Gemini 2.5 Flash + Groq Llama 3.3</span>
                  </motion.div>

                  <h1 className="text-6xl md:text-8xl font-black tracking-tight leading-[0.85] text-white drop-shadow-2xl">
                    Auditoría <br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-600">Multidocumental</span>
                  </h1>

                  <div className="flex items-center justify-center gap-8 pt-4">
                    <div className="flex items-center gap-2 text-gray-500"><FileSearch className="w-4 h-4" /><span className="text-xs font-bold uppercase tracking-widest">Cruces Semánticos</span></div>
                    <div className="flex items-center gap-2 text-gray-500"><Database className="w-4 h-4" /><span className="text-xs font-bold uppercase tracking-widest">Chunking Paralelo</span></div>
                    <div className="flex items-center gap-2 text-gray-500"><ShieldCheck className="w-4 h-4" /><span className="text-xs font-bold uppercase tracking-widest">Síntesis con IA</span></div>
                  </div>
                </div>

                {error && (
                  <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="max-w-xl mx-auto mb-10 bg-rose-500/10 border border-rose-500/20 p-5 rounded-3xl flex items-center gap-4 text-rose-400">
                    <div className="p-2 bg-rose-500/20 rounded-xl"><AlertCircle className="w-6 h-6" /></div>
                    <div className="flex-1">
                      <h4 className="font-black text-sm uppercase tracking-widest">Error de Integridad</h4>
                      <p className="text-xs font-medium opacity-80">{error}</p>
                    </div>
                  </motion.div>
                )}

                <Uploader onAnalysisStart={startAnalysis} isAnalyzing={isAnalyzing} />
              </motion.div>
            ) : (
              <motion.div key="results" initial={{ opacity: 0, scale: 1.05 }} animate={{ opacity: 1, scale: 1 }} className="relative z-10">
                <MatrixSuprema analysis={analysisData} />
                <div className="fixed bottom-10 left-10 z-50">
                  <button onClick={() => setAnalysisData(null)} className="bg-white/5 hover:bg-white/10 border border-white/10 px-6 py-3 rounded-2xl text-xs font-black uppercase tracking-widest backdrop-blur-xl transition-all">
                    Nueva Auditoría
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <footer className="fixed bottom-0 left-0 w-full p-4 text-center text-[10px] text-gray-600 uppercase font-black tracking-[0.3em] pointer-events-none z-0">
            Engine: Gemini 2.5 Flash + Groq Llama 3.3 · PTAFI-AI v2.0
          </footer>
        </>
      )}
    </main>
  );
}
