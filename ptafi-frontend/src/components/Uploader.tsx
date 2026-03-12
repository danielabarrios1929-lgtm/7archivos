"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
    Upload,
    X,
    FileText,
    CheckCircle2,
    AlertCircle,
    BrainCircuit,
    Loader2,
    ChevronRight,
    Play,
    FolderSync
} from 'lucide-react';
import { cn } from '@/lib/utils';


interface FileSlotProps {
    id: string;
    label: string;
    file: File | null;
    onUpload: (file: File) => void;
    onRemove: () => void;
}

const FileSlot = ({ id, label, file, onUpload, onRemove }: FileSlotProps) => {
    const [isDragOver, setIsDragOver] = useState(false);

    return (
        <div
            className={cn(
                "relative group p-4 rounded-2xl border transition-all duration-300",
                file
                    ? "bg-emerald-500/5 border-emerald-500/20"
                    : isDragOver
                        ? "bg-blue-500/10 border-blue-500/50 scale-102"
                        : "bg-white/[0.02] border-white/10 hover:border-white/30"
            )}
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={(e) => {
                e.preventDefault();
                setIsDragOver(false);
                const droppedFile = e.dataTransfer.files[0];
                if (droppedFile) onUpload(droppedFile);
            }}
        >
            <div className="flex items-center gap-4">
                <div className={cn(
                    "w-12 h-12 rounded-xl flex items-center justify-center transition-colors",
                    file ? "bg-emerald-500/20 text-emerald-400" : "bg-white/5 text-gray-500 group-hover:text-blue-400"
                )}>
                    {file ? <CheckCircle2 className="w-6 h-6" /> : <FileText className="w-6 h-6" />}
                </div>

                <div className="flex-1 min-w-0">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest">{label}</h4>
                    <p className="text-sm font-medium text-gray-100 truncate">
                        {file ? file.name : "Subir archivo (PDF, Word, Excel, etc.)"}
                    </p>
                </div>

                {file ? (
                    <button
                        onClick={onRemove}
                        className="w-8 h-8 rounded-full hover:bg-rose-500/20 text-gray-500 hover:text-rose-400 flex items-center justify-center transition-colors"
                    >
                        <X className="w-4 h-4" />
                    </button>
                ) : (
                    <label className="cursor-pointer">
                        <input
                            type="file"
                            accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt,.jpg,.jpeg,.png,.webp"
                            className="hidden"
                            onChange={(e) => {
                                const selectedFile = e.target.files?.[0];
                                if (selectedFile) onUpload(selectedFile);
                            }}
                        />
                        <div className="w-8 h-8 rounded-full bg-blue-500/10 text-blue-400 hover:bg-blue-500 hover:text-white flex items-center justify-center transition-all">
                            <Upload className="w-4 h-4" />
                        </div>
                    </label>
                )}
            </div>
        </div>
    );
};

interface UploaderProps {
    onAnalysisStart: (data: FormData, useLocalFolder?: boolean) => void;
    isAnalyzing: boolean;
}


const MANDATORY_FILES = [
    { id: 'PEI', label: 'PEI (Proyecto Educativo)' },
    { id: 'MC', label: 'Manual de Convivencia' },
    { id: 'PMI', label: 'PMI (Plan Mejoramiento)' },
    { id: 'POA', label: 'POA (Plan Operativo)' },
    { id: 'PFI', label: 'PFI (Plan Formación)' },
    { id: 'SIEE', label: 'SIEE (Evaluación)' },
    { id: 'LC', label: 'Lectura de Contexto' },
    { id: 'OTRO_1', label: 'Otro Documento' },
    { id: 'OTRO_2', label: 'Otro Documento' },
];

export const Uploader = ({ onAnalysisStart, isAnalyzing }: UploaderProps) => {
    const [files, setFiles] = useState<Record<string, File | null>>({
        PEI: null,
        MC: null,
        PMI: null,
        POA: null,
        PFI: null,
        SIEE: null,
        LC: null,
        OTRO_1: null,
        OTRO_2: null,
    });

    const [institutionName, setInstitutionName] = useState("");
    const [tutorName, setTutorName] = useState("");
    const [isDemoLoading, setIsDemoLoading] = useState(false);

    // Función para activar el Modo Demo (Con contenido REAL de Guaimaral)
    const activateDemoMode = async () => {
        setIsDemoLoading(true);
        setInstitutionName("I.E. Guaimaral (Modo Demo Real)");
        setTutorName("Auditor Especialista PTAFI");

        const demoFiles: Record<string, File> = {};

        // Mapeo de contenidos reales que ya tenemos en test_pdfs
        const demoDocs = [
            { id: 'PEI', name: 'PEI_REAL.txt', content: "PROYECTO EDUCATIVO INSTITUCIONAL (PEI) - I.E. GUAIMARAL\n\nModelo Pedagógico: Constructivismo Social con enfoque territorial.\nIdentidad: Formación integral de jóvenes rurales en Tubará, Atlántico.\nEjes Transversales: Agroecología, Tecnología, Emprendimiento Local y Valores Ciudadanos." },
            { id: 'MC', name: 'MANUAL_CONVIVENCIA_REAL.txt', content: "MANUAL DE CONVIVENCIA - I.E. GUAIMARAL\n\nPrincipios: Respeto por la diversidad cultural (indígena y afro), solidaridad y diálogo.\nResolución de Conflictos: Se prioriza la mediación escolar." },
            { id: 'PMI', name: 'PMI_REAL.txt', content: "PLAN DE MEJORAMIENTO INSTITUCIONAL (PMI) - I.E. GUAIMARAL\n\nObjetivo: Mejorar los resultados en matemáticas y lectura. Meta: Implementar estrategias de nivelación para el tercer periodo." },
            { id: 'POA', name: 'POA_REAL.txt', content: "PLAN OPERATIVO ANUAL (POA) - 2026\n\nMetas: 1. Implementación al 100% de los CI de robótica y agroecología. 2. Capacitación docente en PTAFI 3.0." },
            { id: 'SIEE', name: 'SIEE_REAL.txt', content: "SISTEMA INSTITUCIONAL DE EVALUACIÓN DE ESTUDIANTES (SIEE) - I.E. GUAIMARAL\n\nCriterios: Evaluaciones Sumativas 60%, Formativas 40%. Se detecta evaluación tradicional." },
            { id: 'LC', name: 'LECTURA_DE_CONTEXTO_REAL.txt', content: "INFORME DE DIAGNÓSTICO PARTICIPATIVO - I.E. GUAIMARAL\nUbicación: Tubará, Atlántico. Predomina actividad agrícola familiar y comercio informal." },
            { id: 'PFI', name: 'PFI_GUAIMARAL.txt', content: "PLAN DE FORMACIÓN INTEGRAL (PFI) 2026 - I.E. GUAIMARAL\nCI: Agro-Tec, Guardianes de la Memoria, Matemáticas en la Tierra." }
        ];

        demoDocs.forEach(doc => {
            const blob = new Blob([doc.content], { type: 'text/plain' });
            const file = new File([blob], doc.name, { type: 'text/plain' });
            demoFiles[doc.id] = file;
        });

        setFiles(prev => ({ ...prev, ...demoFiles }));
        setIsDemoLoading(false);
    };

    const hasFiles = Object.values(files).some(f => f !== null);
    const isReady = institutionName && tutorName && hasFiles;

    const handleSubmit = () => {
        if (!isReady) return;

        const formData = new FormData();
        formData.append("institution_name", institutionName);
        formData.append("tutor_name", tutorName);

        Object.entries(files).forEach(([id, file]) => {
            if (file) formData.append("files", file);
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

    return (
        <div className="max-w-4xl mx-auto space-y-8 pb-20">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="bg-white/[0.03] border border-white/10 rounded-3xl p-8 space-y-6"
                >
                    <div className="space-y-2">
                        <h2 className="text-2xl font-black text-white flex items-center gap-3">
                            <BrainCircuit className="text-blue-500" />
                            Configurar Auditoría
                        </h2>
                        <p className="text-gray-400 text-sm">Ingresa los metadatos de la institución.</p>
                    </div>

                    <div className="space-y-4">
                        <div className="space-y-1.5">
                            <label className="text-[10px] font-black text-blue-400 uppercase tracking-widest ml-1">Institución Educativa</label>
                            <input
                                type="text"
                                value={institutionName}
                                onChange={(e) => setInstitutionName(e.target.value)}
                                placeholder="Ej. Institución Educativa Técnica del Agro"
                                className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-white focus:outline-none focus:border-blue-500/50 transition-colors placeholder:text-gray-600"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[10px] font-black text-blue-400 uppercase tracking-widest ml-1">Tutor Pedagógico</label>
                            <input
                                type="text"
                                value={tutorName}
                                onChange={(e) => setTutorName(e.target.value)}
                                placeholder="Nombre del Auditor Senior"
                                className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-white focus:outline-none focus:border-blue-500/50 transition-colors placeholder:text-gray-600"
                            />
                        </div>

                        {/* Motor fijo: Groq */}
                        <div className="pt-4 p-4 bg-purple-500/5 border border-purple-500/20 rounded-2xl flex items-center gap-3">
                            <div className="w-8 h-8 rounded-xl bg-purple-500/20 flex items-center justify-center">
                                <BrainCircuit className="w-4 h-4 text-purple-400" />
                            </div>
                            <div>
                                <div className="text-xs font-bold text-white">Motor: Groq · Llama 3.3</div>
                                <div className="text-[10px] text-gray-400">Velocidad Extrema · Activo</div>
                            </div>
                            <div className="ml-auto w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                        </div>
                    </div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="space-y-4"
                >
                    <div className="flex items-center justify-between px-2">
                        <h3 className="text-lg font-bold text-gray-200 uppercase tracking-tighter">Documentos de Auditoría</h3>
                        <button
                            onClick={activateDemoMode}
                            disabled={isDemoLoading || isAnalyzing}
                            className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 rounded-full text-[10px] font-black uppercase tracking-widest text-blue-400 transition-all font-bold shadow-lg shadow-blue-500/10"
                        >
                            {isDemoLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                            MODO DEMO GUAIMARAL (REAL)
                        </button>
                    </div>

                    <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                        {MANDATORY_FILES.map(slot => (
                            <FileSlot
                                key={slot.id}
                                id={slot.id}
                                label={slot.label}
                                file={files[slot.id]}
                                onUpload={(file) => setFiles(prev => ({ ...prev, [slot.id]: file }))}
                                onRemove={() => setFiles(prev => ({ ...prev, [slot.id]: null }))}
                            />
                        ))}
                    </div>
                </motion.div>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center gap-4 pt-8"
            >
                <button
                    disabled={!isReady || isAnalyzing}
                    onClick={handleSubmit}
                    className={cn(
                        "relative px-12 py-5 rounded-3xl font-black text-lg uppercase tracking-[0.2em] transition-all duration-500",
                        isReady && !isAnalyzing
                            ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-2xl shadow-blue-500/40 hover:scale-105 active:scale-95"
                            : "bg-white/5 text-gray-600 cursor-not-allowed opacity-50"
                    )}
                >
                    {isAnalyzing ? (
                        <div className="flex items-center gap-3">
                            <Loader2 className="w-5 h-5 animate-spin" />
                            Ejecutando Auditoría...
                        </div>
                    ) : (
                        <div className="flex items-center gap-3">
                            Iniciar Gran Auditoría
                            <ChevronRight className="w-5 h-5" />
                        </div>
                    )}
                </button>

                <button
                    disabled={(!institutionName || !tutorName) || isAnalyzing}
                    onClick={handleSubmitLocal}
                    className={cn(
                        "relative px-10 py-4 rounded-3xl font-bold text-xs uppercase tracking-widest transition-all duration-300 w-full max-w-sm",
                        (institutionName && tutorName) && !isAnalyzing
                            ? "bg-white/5 border border-white/10 text-emerald-400 hover:bg-emerald-500/10 hover:border-emerald-500/30 shadow-lg shadow-emerald-500/5 hover:-translate-y-1"
                            : "bg-white/5 border border-white/5 text-gray-600 cursor-not-allowed hidden"
                    )}
                >
                    <div className="flex items-center justify-center gap-3">
                        <FolderSync className="w-4 h-4" />
                        TEST: Escanear carpeta '7 archivos'
                    </div>
                </button>

                {!isReady && !isAnalyzing && (
                    <p className="text-rose-500/60 text-xs font-bold uppercase tracking-widest animate-pulse flex items-center gap-2">
                        <AlertCircle className="w-3 h-3" />
                        Ingresa los metadatos y al menos un documento para activar el motor
                    </p>
                )}
            </motion.div>
        </div>
    );
};
