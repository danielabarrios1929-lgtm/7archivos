"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
    BrainCircuit,
    Loader2,
    FolderSync,
    AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface UploaderProps {
    onAnalysisStart: (data: FormData, useLocalFolder?: boolean) => void;
    isAnalyzing: boolean;
}

export const Uploader = ({ onAnalysisStart, isAnalyzing }: UploaderProps) => {
    const [institutionName, setInstitutionName] = useState("");
    const [tutorName, setTutorName] = useState("");

    const handleSubmitLocal = () => {
        if (!institutionName || !tutorName) return;

        const formData = new FormData();
        formData.append("institution_name", institutionName);
        formData.append("tutor_name", tutorName);

        // Envía el flag "true" para indicarle que lea desde la carpeta en el backend automáticamente.
        onAnalysisStart(formData, true);
    };

    const isReady = institutionName && tutorName;

    return (
        <div className="max-w-xl mx-auto space-y-8 pb-20 mt-8">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-white/[0.03] border border-white/10 rounded-3xl p-8 space-y-8 shadow-2xl shadow-black/50 relative overflow-hidden"
            >
                {/* Background glow decoration */}
                <div className="absolute -top-24 -right-24 w-64 h-64 bg-blue-500/10 blur-3xl rounded-full pointer-events-none" />

                <div className="space-y-4 text-center relative z-10">
                    <div className="w-20 h-20 bg-gradient-to-br from-blue-500/20 to-emerald-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-emerald-500/20 shadow-lg shadow-emerald-500/10">
                        <BrainCircuit className="w-10 h-10 text-emerald-400" />
                    </div>
                    <h2 className="text-3xl font-black text-white px-4 leading-tight">Orquestador IA PTAFI</h2>
                    <p className="text-gray-400 text-sm">Escanea y audita automáticamente los 7 documentos ubicados en tu carpeta local.</p>
                </div>

                <div className="space-y-5 pt-6 relative z-10">
                    <div className="space-y-1.5">
                        <label className="text-[10px] font-black text-emerald-400/80 uppercase tracking-widest ml-1">Institución Educativa</label>
                        <input
                            type="text"
                            value={institutionName}
                            onChange={(e) => setInstitutionName(e.target.value)}
                            placeholder="Ej. Institución Educativa Técnica del Agro"
                            className="w-full bg-black/20 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-emerald-500/50 transition-colors placeholder:text-gray-700 shadow-inner"
                        />
                    </div>
                    <div className="space-y-1.5">
                        <label className="text-[10px] font-black text-emerald-400/80 uppercase tracking-widest ml-1">Tutor Pedagógico</label>
                        <input
                            type="text"
                            value={tutorName}
                            onChange={(e) => setTutorName(e.target.value)}
                            placeholder="Nombre del Auditor Senior"
                            className="w-full bg-black/20 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-emerald-500/50 transition-colors placeholder:text-gray-700 shadow-inner"
                        />
                    </div>
                </div>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center gap-6 pt-4"
            >
                <button
                    disabled={!isReady || isAnalyzing}
                    onClick={handleSubmitLocal}
                    className={cn(
                        "relative px-12 py-5 rounded-3xl font-black text-lg uppercase tracking-[0.1em] transition-all duration-500 w-full",
                        isReady && !isAnalyzing
                            ? "bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-[0_0_40px_-5px_var(--tw-shadow-color)] shadow-emerald-500/30 hover:scale-105 active:scale-95"
                            : "bg-white/5 text-gray-600 cursor-not-allowed border border-white/5"
                    )}
                >
                    <div className="flex items-center justify-center gap-4">
                        {isAnalyzing ? <Loader2 className="w-6 h-6 animate-spin" /> : <FolderSync className="w-6 h-6" />}
                        Escanear los 7 Archivos "De Una"
                    </div>
                </button>

                {!isReady && !isAnalyzing && (
                    <p className="text-rose-500/60 text-xs font-bold uppercase tracking-widest animate-pulse flex items-center gap-2">
                        <AlertCircle className="w-3 h-3" />
                        Completa los datos arriba para activar el escáner
                    </p>
                )}
            </motion.div>
        </div>
    );
};
