"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Uploader } from '@/components/Uploader';
import { MatrixSuprema } from '@/components/MatrixSuprema';
import { Sparkles, Database, FileSearch, ShieldCheck, AlertCircle } from 'lucide-react';

const API_URL = "/api/v1/analysis/process";

export default function Home() {
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startAnalysis = async (formData: FormData) => {
    setIsAnalyzing(true);
    setError(null);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = "Fallo crítico en el motor de auditoría.";
        try {
          const errData = await response.json();
          errorMessage = errData?.detail?.error || errData?.detail || errorMessage;
        } catch (e) {
          // Si no es JSON, usamos el statusText
          errorMessage = `Error ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setAnalysisData(data);
    } catch (err: any) {
      setError(err.message === "Failed to fetch" ? "Error de conexión: No se pudo contactar con el servidor. Verifica que el backend esté corriendo." : err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#020205] text-white selection:bg-blue-500/30 selection:text-white">
      {/* Dynamic Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 -left-[10%] w-[60%] h-[60%] bg-blue-600/5 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-0 -right-[10%] w-[60%] h-[60%] bg-purple-600/5 blur-[120px] rounded-full animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-150 contrast-150 mix-blend-overlay" />
      </div>

      <AnimatePresence mode="wait">
        {!analysisData ? (
          <motion.div
            key="uploader"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="relative z-10 pt-24 px-6"
          >
            <div className="max-w-4xl mx-auto text-center space-y-6 mb-16">
              <motion.div
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
                className="inline-flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full mb-8"
              >
                <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-[10px] font-black tracking-widest uppercase text-blue-300">Inteligencia Artificial PTAFI-AI v1.5</span>
              </motion.div>

              <h1 className="text-6xl md:text-8xl font-black tracking-tight leading-[0.85] text-white drop-shadow-2xl">
                Auditoría <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-600">Multidocumental</span>
              </h1>

              <div className="flex items-center justify-center gap-8 pt-4">
                <div className="flex items-center gap-2 text-gray-500">
                  <FileSearch className="w-4 h-4" />
                  <span className="text-xs font-bold uppercase tracking-widest">Cruces Semánticos</span>
                </div>
                <div className="flex items-center gap-2 text-gray-500">
                  <Database className="w-4 h-4" />
                  <span className="text-xs font-bold uppercase tracking-widest">Persistencia Grupal</span>
                </div>
                <div className="flex items-center gap-2 text-gray-500">
                  <ShieldCheck className="w-4 h-4" />
                  <span className="text-xs font-bold uppercase tracking-widest">Checklist Blindado</span>
                </div>
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-xl mx-auto mb-10 bg-rose-500/10 border border-rose-500/20 p-5 rounded-3xl flex items-center gap-4 text-rose-400 shadow-xl shadow-rose-500/5"
              >
                <div className="p-2 bg-rose-500/20 rounded-xl">
                  <AlertCircle className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <h4 className="font-black text-sm uppercase tracking-widest">Error de Integridad</h4>
                  <p className="text-xs font-medium opacity-80">{error}</p>
                </div>
              </motion.div>
            )}

            <Uploader onAnalysisStart={startAnalysis} isAnalyzing={isAnalyzing} />
          </motion.div>
        ) : (
          <motion.div
            key="results"
            initial={{ opacity: 0, scale: 1.05 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative z-10"
          >
            <MatrixSuprema analysis={analysisData} />
            <div className="fixed bottom-10 left-10 z-50">
              <button
                onClick={() => setAnalysisData(null)}
                className="bg-white/5 hover:bg-white/10 border border-white/10 px-6 py-3 rounded-2xl text-xs font-black uppercase tracking-widest backdrop-blur-xl transition-all"
              >
                Nueva Auditoría
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <footer className="fixed bottom-0 left-0 w-full p-4 text-center text-[10px] text-gray-600 uppercase font-black tracking-[0.3em] pointer-events-none z-0">
        Engine: Groq Llama 3.3-70b · Analysis Protocol v1.5
      </footer>
    </main>
  );
}
