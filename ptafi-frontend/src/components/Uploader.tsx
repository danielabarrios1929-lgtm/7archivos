"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
    BrainCircuit,
    Loader2,
    FolderSync,
    AlertCircle,
    Upload,
    FileText,
    X,
    CheckCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface UploaderProps {
    onAnalysisStart: (data: FormData, useLocalFolder?: boolean) => void;
    isAnalyzing: boolean;
}

export const Uploader = ({ onAnalysisStart, isAnalyzing }: UploaderProps) => {
    const [institutionName, setInstitutionName] = useState("");
    const [tutorName, setTutorName] = useState("");
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [dragActive, setDragActive] = useState(false);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const filesArray = Array.from(e.target.files);
            setSelectedFiles(prev => [...prev, ...filesArray]);
        }
    };

    const removeFile = (index: number) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const filesArray = Array.from(e.dataTransfer.files);
            setSelectedFiles(prev => [...prev, ...filesArray]);
        }
    };

    const handleSubmitManual = () => {
        if (!institutionName || !tutorName || selectedFiles.length === 0) return;

        const formData = new FormData();
        formData.append("institution_name", institutionName);
        formData.append("tutor_name", tutorName);
        selectedFiles.forEach(file => {
            formData.append("files", file);
        });

        onAnalysisStart(formData, false);
    };

    const handleSubmitLocal = () => {
        if (!institutionName || !tutorName) return;

        const formData = new FormData();
        formData.append("institution_name", institutionName);
        formData.append("tutor_name", tutorName);

        onAnalysisStart(formData, true);
    };

    const isReadyManual = institutionName && tutorName && selectedFiles.length > 0;
    const isReadyLocal = institutionName && tutorName;

    return (
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8 pb-20 mt-8 px-6">
            {/* Sección de Datos */}
            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-white/[0.03] border border-white/10 rounded-3xl p-8 space-y-6 shadow-2xl shadow-black/50"
            >
                <div className="space-y-2">
                    <h3 className="text-xl font-black text-white flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                        Datos del Proyecto
                    </h3>
                    <p className="text-gray-500 text-xs uppercase tracking-widest font-bold">Información para el reporte final</p>
                </div>

                <div className="space-y-5">
                    <div className="space-y-1.5">
                        <label className="text-[10px] font-black text-emerald-400/80 uppercase tracking-widest ml-1">Institución Educativa</label>
                        <input
                            type="text"
                            value={institutionName}
                            onChange={(e) => setInstitutionName(e.target.value)}
                            placeholder="Ej. I.E. Guaimaral"
                            className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-emerald-500/50 transition-colors placeholder:text-gray-700 shadow-inner"
                        />
                    </div>
                    <div className="space-y-1.5">
                        <label className="text-[10px] font-black text-emerald-400/80 uppercase tracking-widest ml-1">Tutor/Auditor</label>
                        <input
                            type="text"
                            value={tutorName}
                            onChange={(e) => setTutorName(e.target.value)}
                            placeholder="Nombre del responsable"
                            className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-emerald-500/50 transition-colors placeholder:text-gray-700 shadow-inner"
                        />
                    </div>
                </div>

                <div className="pt-4 border-t border-white/5">
                    <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-4">Atajo: Carpeta Local</h4>
                    <button
                        onClick={handleSubmitLocal}
                        disabled={!isReadyLocal || isAnalyzing}
                        className={cn(
                            "w-full py-4 rounded-2xl flex items-center justify-center gap-3 text-xs font-black uppercase tracking-widest transition-all",
                            isReadyLocal && !isAnalyzing
                                ? "bg-white/5 hover:bg-white/10 border border-white/10 text-white"
                                : "bg-white/[0.02] text-gray-700 border border-transparent cursor-not-allowed"
                        )}
                    >
                        <FolderSync className="w-4 h-4" />
                        Cargar Auto de 7 archivos
                    </button>
                </div>
            </motion.div>

            {/* Sección de Archivos Manuales */}
            <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
            >
                <div
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    className={cn(
                        "relative border-2 border-dashed rounded-3xl p-10 transition-all group flex flex-col items-center justify-center gap-4 text-center min-h-[250px]",
                        dragActive 
                            ? "border-blue-500 bg-blue-500/10" 
                            : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"
                    )}
                >
                    <input
                        type="file"
                        multiple
                        onChange={handleFileChange}
                        className="absolute inset-0 opacity-0 cursor-pointer"
                    />
                    <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-2 border border-blue-500/20 group-hover:scale-110 transition-transform">
                        <Upload className="w-8 h-8 text-blue-400" />
                    </div>
                    <div>
                        <p className="text-white font-black uppercase tracking-widest text-sm">Sube tus archivos</p>
                        <p className="text-gray-500 text-xs mt-1">Arrastra y suelta o haz clic para seleccionar</p>
                    </div>
                </div>

                {/* Lista de archivos seleccionados */}
                <AnimatePresence>
                    {selectedFiles.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="bg-white/[0.03] border border-white/10 rounded-3xl overflow-hidden"
                        >
                            <div className="p-4 bg-white/5 flex items-center justify-between border-b border-white/5">
                                <span className="text-[10px] font-black text-blue-400 uppercase tracking-widest">
                                    {selectedFiles.length} Archivos Seleccionados
                                </span>
                                <button onClick={() => setSelectedFiles([])} className="text-[10px] text-rose-500 p-1 hover:bg-rose-500/10 rounded">Limpiar</button>
                            </div>
                            <div className="max-h-[180px] overflow-y-auto custom-scrollbar p-2">
                                {selectedFiles.map((file, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-2 hover:bg-white/5 rounded-xl group">
                                        <div className="flex items-center gap-3">
                                            <FileText className="w-4 h-4 text-gray-500" />
                                            <span className="text-xs text-gray-300 truncate max-w-[150px]">{file.name}</span>
                                        </div>
                                        <button onClick={() => removeFile(idx)} className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-500 transition-all">
                                            <X className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <button
                    disabled={!isReadyManual || isAnalyzing}
                    onClick={handleSubmitManual}
                    className={cn(
                        "w-full py-5 rounded-3xl font-black text-lg uppercase tracking-widest transition-all shadow-2xl",
                        isReadyManual && !isAnalyzing
                            ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-blue-500/20 hover:scale-[1.02] active:scale-[0.98]"
                            : "bg-white/5 text-gray-700 border border-white/5 cursor-not-allowed"
                    )}
                >
                    <div className="flex items-center justify-center gap-4">
                        {isAnalyzing ? <Loader2 className="w-6 h-6 animate-spin" /> : <BrainCircuit className="w-6 h-6" />}
                        Iniciar Auditoría con mis archivos
                    </div>
                </button>
            </motion.div>
        </div>
    );
};
