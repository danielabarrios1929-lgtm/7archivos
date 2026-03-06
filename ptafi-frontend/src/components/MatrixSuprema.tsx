"use client";

import React from 'react';
import { motion } from 'framer-motion';
import {
    FileText,
    Search,
    MapPin,
    Users,
    TrendingUp,
    Dna,
    Building2,
    CheckCircle2,
    AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Finding {
    category_name: string;
    hallazgo: string;
    evidencia: {
        text: string;
        document_name: string;
        page: number;
    };
    interpretacion: string;
    implicacion_pfi: string;
}

export interface QualityPillar {
    pillar_name: string;
    score: number;
    analysis: string;
    recommendations: string[];
}

interface MatrixSupremaProps {
    analysis: {
        institution_info: {
            name: string;
            tutor: string;
        };
        matrix: Finding[];
        quality_report: QualityPillar[];
        pdf_base64?: string;
    };
}

const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
        case 'contexto territorial': return <MapPin className="w-5 h-5" />;
        case 'intereses estudiantiles': return <Users className="w-5 h-5" />;
        case 'fortalezas institucionales': return <TrendingUp className="w-5 h-5" />;
        case 'problemáticas educativas': return <AlertTriangle className="w-5 h-5" />;
        case 'cultura y saberes locales': return <Dna className="w-5 h-5" />;
        case 'infraestructura': return <Building2 className="w-5 h-5" />;
        default: return <FileText className="w-5 h-5" />;
    }
};

const MatrixCategory = ({ title, data, index }: { title: string; data: Finding; index: number }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 }}
        className="bg-white/[0.03] backdrop-blur-xl border border-white/10 p-6 rounded-3xl shadow-2xl hover:border-blue-500/50 transition-all duration-500 group relative overflow-hidden"
    >
        <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-[80px] -z-10 group-hover:bg-blue-500/10 transition-all" />

        <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
                    {getCategoryIcon(title)}
                </div>
                <h3 className="text-xl font-bold text-gray-100 group-hover:text-blue-200">{title}</h3>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 bg-green-500/10 text-green-400 rounded-full text-[10px] font-bold uppercase tracking-widest border border-green-500/20">
                <CheckCircle2 className="w-3 h-3" /> Auditado
            </div>
        </div>

        <div className="space-y-5">
            <div className="space-y-2">
                <h4 className="text-[10px] font-black text-blue-500/60 uppercase tracking-[0.2em]">Hallazgo Principal</h4>
                <p className="text-gray-200 text-sm italic font-medium leading-relaxed">"{data.hallazgo}"</p>
            </div>

            <div className="bg-black/40 p-4 rounded-2xl border border-white/5 space-y-3">
                <div className="flex items-center justify-between">
                    <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Evidencia Textual</h4>
                    <span className="text-[9px] font-mono text-blue-400/80 bg-blue-400/5 px-2 py-0.5 rounded border border-blue-400/10">
                        {data.evidencia.document_name} · Pág. {data.evidencia.page}
                    </span>
                </div>
                <p className="text-gray-400 text-xs leading-relaxed line-clamp-3 group-hover:line-clamp-none transition-all duration-300 italic">
                    "{data.evidencia.text}"
                </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="space-y-1">
                    <h4 className="text-[10px] font-black text-purple-400/60 uppercase tracking-[0.2em]">Interpretación</h4>
                    <p className="text-gray-300 text-[13px] leading-relaxed">{data.interpretacion}</p>
                </div>
                <div className="p-3 bg-emerald-500/[0.03] rounded-xl border border-emerald-500/10 space-y-1">
                    <h4 className="text-[10px] font-black text-emerald-400/60 uppercase tracking-[0.2em]">Implicación PFI</h4>
                    <p className="text-gray-200 text-[13px] leading-relaxed font-semibold">{data.implicacion_pfi}</p>
                </div>
            </div>
        </div>
    </motion.div>
);

const QualityPillarCard = ({ pillar, index }: { pillar: QualityPillar; index: number }) => (
    <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.5 + index * 0.1 }}
        className="bg-white/[0.02] border border-white/5 p-5 rounded-2xl hover:bg-white/[0.04] transition-colors"
    >
        <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-bold text-gray-300">{pillar.pillar_name}</h4>
            <div className="flex items-baseline gap-1">
                <span className={cn(
                    "text-2xl font-black",
                    pillar.score >= 8 ? "text-emerald-400" : pillar.score >= 5 ? "text-amber-400" : "text-rose-400"
                )}>{pillar.score}</span>
                <span className="text-[10px] text-gray-500">/10</span>
            </div>
        </div>
        <p className="text-xs text-gray-400 mb-4 leading-relaxed">{pillar.analysis}</p>
        <div className="space-y-2">
            <h5 className="text-[9px] font-black text-blue-400 uppercase tracking-widest">Recomendaciones</h5>
            <ul className="space-y-1.5">
                {pillar.recommendations.map((rec, i) => (
                    <li key={i} className="flex gap-2 text-[11px] text-gray-300">
                        <span className="text-blue-500 mt-1">•</span>
                        {rec}
                    </li>
                ))}
            </ul>
        </div>
    </motion.div>
);

export const MatrixSuprema = ({ analysis }: MatrixSupremaProps) => {
    const handleDownloadPDF = () => {
        if (!analysis.pdf_base64) {
            alert("El informe PDF no está listo o hubo un error generándolo.");
            return;
        }

        const linkSource = `data:application/pdf;base64,${analysis.pdf_base64}`;
        const downloadLink = document.createElement("a");
        const fileName = `Informe_Auditoria_${analysis.institution_info.name.replace(/\s+/g, '_')}.pdf`;

        downloadLink.href = linkSource;
        downloadLink.download = fileName;
        downloadLink.click();
    };

    return (
        <div className="min-h-screen bg-[#020205] text-white selection:bg-blue-500/30 selection:text-white">
            {/* Background elements */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 -left-[10%] w-[50%] h-[50%] bg-blue-600/10 blur-[120px] rounded-full" />
                <div className="absolute bottom-0 -right-[10%] w-[50%] h-[50%] bg-purple-600/10 blur-[120px] rounded-full" />
            </div>

            <div className="max-w-[1600px] mx-auto px-6 py-12 relative z-10">
                <header className="mb-16">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="inline-flex items-center gap-2 px-4 py-1.5 mb-8 bg-blue-500/10 border border-blue-500/20 rounded-full"
                    >
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                        <span className="text-blue-400 text-[10px] font-black tracking-[0.2em] uppercase">
                            Procesamiento Analítico PTAFI-AI v1.5
                        </span>
                    </motion.div>

                    <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-8">
                        <div className="max-w-2xl">
                            <motion.h1
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="text-5xl md:text-7xl font-black mb-6 tracking-tight leading-[0.9] text-white"
                            >
                                Matriz Suprema de <br />
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-600">Sistematización</span>
                            </motion.h1>
                            <motion.p
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                                className="text-gray-400 text-lg max-w-xl border-l border-white/10 pl-6"
                            >
                                Auditoría concurrente multidocumental para la <span className="text-white font-bold">{analysis.institution_info.name}</span>.
                                Sistematización generada por motor de inferencia avanzada.
                            </motion.p>
                        </div>

                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.3 }}
                            className="bg-white/5 border border-white/10 p-6 rounded-3xl backdrop-blur-md"
                        >
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center font-black text-xl shadow-lg shadow-blue-500/20">
                                    {analysis.institution_info.tutor[0].toUpperCase()}
                                </div>
                                <div>
                                    <h4 className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Tutor Asignado</h4>
                                    <p className="text-white font-bold text-lg">{analysis.institution_info.tutor}</p>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </header>

                <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
                    <div className="xl:col-span-3">
                        <div className="flex items-center gap-4 mb-8">
                            <Search className="text-blue-500" />
                            <h2 className="text-2xl font-black text-white tracking-tight uppercase">Hallazgos Estratégicos</h2>
                            <div className="h-px flex-1 bg-white/10" />
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {analysis.matrix.map((cat, idx) => (
                                <MatrixCategory key={idx} title={cat.category_name} data={cat} index={idx} />
                            ))}
                        </div>
                    </div>

                    <aside className="space-y-8">
                        <div className="flex items-center gap-4 mb-2">
                            <CheckCircle2 className="text-emerald-500" />
                            <h2 className="text-2xl font-black text-white tracking-tight uppercase">Calidad</h2>
                            <div className="h-px flex-1 bg-white/10" />
                        </div>

                        <div className="space-y-4">
                            {analysis.quality_report.map((pillar, idx) => (
                                <QualityPillarCard key={idx} pillar={pillar} index={idx} />
                            ))}
                        </div>

                        <button
                            onClick={handleDownloadPDF}
                            className="w-full relative group"
                        >
                            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-500"></div>
                            <div className="relative px-8 py-5 bg-[#020205] border border-white/10 rounded-2xl flex items-center justify-center gap-3 font-bold text-sm tracking-widest uppercase transition-all duration-300 group-hover:bg-black/80">
                                <FileText className="w-4 h-4 text-blue-400" />
                                Descargar Informe PDF Editorial
                            </div>
                        </button>
                    </aside>
                </div>
            </div>
        </div>
    );
};
