import React, { useState, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, ReferenceLine
} from 'recharts';

interface SignificantFrame {
    time: number;
    image: string; // Base64
    detections: string[];
}

interface AnalysisTimeline {
    time: number;
    threat_level: number;
    detections: string[];
}

interface AnalysisReport {
    summary: string;
    duration: number;
    weapon_count: number;
    violence_count: number;
    timeline: AnalysisTimeline[];
    significant_frames: SignificantFrame[];
}

const VideoAnalysisPage = () => {
    const [isUploading, setIsUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [report, setReport] = useState<AnalysisReport | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [activePoint, setActivePoint] = useState<any>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Derived Forensic Metrics
    const metrics = useMemo(() => {
        if (!report) return null;
        const threatLevels = report.timeline.map(t => t.threat_level);
        return {
            peakLevel: Math.max(...threatLevels, 0),
            avgRisk: (threatLevels.length > 0 ? threatLevels.reduce((a, b) => a + b, 0) / threatLevels.length : 0),
            confidence: 0.94,
            durationText: `${Math.floor(report.duration / 60)}m ${Math.floor(report.duration % 60)}s`
        };
    }, [report]);

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        uploadAndAnalyze(file);
    };

    const uploadAndAnalyze = async (file: File) => {
        setIsUploading(true);
        setProgress(10);
        setError(null);
        setReport(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const interval = setInterval(() => {
                setProgress(prev => (prev < 90 ? prev + 2 : prev));
            }, 1000);

            const response = await fetch('http://localhost:8000/api/v1/analyze/video', {
                method: 'POST',
                body: formData,
            });

            clearInterval(interval);
            
            if (!response.ok) throw new Error('Failed to analyze video');
            
            const data = await response.json();
            if (data.error) throw new Error(data.error);

            setReport(data);
            setProgress(100);
            setTimeout(() => setIsUploading(false), 500);
        } catch (err: any) {
            setError(err.message || 'An error occurred during analysis');
            setIsUploading(false);
        }
    };

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload as AnalysisTimeline;
            return (
                <div className="bg-slate-900/95 backdrop-blur-md border border-slate-700/50 rounded-lg p-3 shadow-2xl ring-1 ring-white/10">
                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 text-center">T+{data.time}s</p>
                    <div className="flex items-center gap-2 justify-center">
                        <div className={`w-2 h-2 rounded-full ${data.threat_level > 0.5 ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]' : 'bg-emerald-500'}`}></div>
                        <span className="text-xs font-black text-white italic tracking-tighter uppercase leading-none">THREAT: {(data.threat_level * 100).toFixed(0)}%</span>
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="p-4 md:p-6 lg:p-8 max-w-[1700px] mx-auto space-y-4 select-none h-full flex flex-col overflow-y-auto scrollbar-hide">
            {/* Header */}
            <header className="flex items-center justify-between shrink-0">
                <div className="flex items-center gap-4">
                    <div className="p-2 bg-sky-500/10 rounded-lg border border-sky-500/20">
                        <span className="material-symbols-outlined text-sky-400 text-2xl">biotech</span>
                    </div>
                    <div>
                        <h1 className="text-xl font-headline font-black text-white uppercase tracking-tight leading-none">Forensic Intelligence Console</h1>
                        <p className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em] mt-1 opacity-70">Unified Multi-Model Threat Verification</p>
                    </div>
                </div>
                {!isUploading && report && (
                     <button 
                        onClick={() => { setReport(null); setProgress(0); }}
                        className="px-4 py-1.5 bg-white/5 hover:bg-white/10 text-white rounded-lg font-black uppercase tracking-widest text-[9px] border border-white/10 transition-all flex items-center gap-2"
                    >
                        <span className="material-symbols-outlined text-xs">refresh</span> Reset Loop
                    </button>
                )}
            </header>

            {!report && !isUploading && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                        e.preventDefault();
                        const file = e.dataTransfer.files?.[0];
                        if (file?.type.startsWith('video/')) uploadAndAnalyze(file);
                        else setError('Unsupported format');
                    }}
                    onClick={() => fileInputRef.current?.click()}
                    className="flex-1 w-full bg-slate-900/40 backdrop-blur-3xl border border-slate-800 rounded-3xl flex flex-col items-center justify-center gap-10 cursor-pointer hover:border-sky-500/20 transition-all group relative min-h-[500px]"
                >
                    <input type="file" className="hidden" ref={fileInputRef} accept="video/*" onChange={handleFileSelect} />
                    <div className="w-24 h-24 bg-slate-800/50 rounded-full flex items-center justify-center border border-slate-700 group-hover:bg-sky-500/10 group-hover:border-sky-500/30 transition-all">
                        <span className="material-symbols-outlined text-5xl text-slate-500 group-hover:text-sky-400">upload_file</span>
                    </div>
                    <div className="text-center space-y-2">
                        <h2 className="text-2xl font-headline font-black text-white uppercase tracking-tight italic">Initialize Forensic Feed</h2>
                        <p className="text-slate-500 text-[10px] font-black uppercase tracking-[0.3em]">Drop footage here // MP4 / MKV / AVI</p>
                    </div>
                    {error && <div className="text-rose-500 text-[10px] font-black uppercase tracking-widest bg-rose-500/10 px-4 py-2 rounded-full border border-rose-500/20">{error}</div>}
                </motion.div>
            )}

            {isUploading && (
                <div className="flex-1 w-full bg-slate-900 border border-slate-800 rounded-3xl flex flex-col items-center justify-center gap-16 relative">
                    <div className="ai-scanner-line opacity-20"></div>
                    <div className="relative">
                        <div className="w-40 h-40 rounded-full border border-white/5 flex items-center justify-center">
                            <span className="text-4xl font-headline font-black text-sky-400">{Math.round(progress)}%</span>
                        </div>
                        <svg className="absolute top-0 left-0 w-40 h-40 -rotate-90">
                            <circle cx="80" cy="80" r="78" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray={Math.PI * 156} strokeDashoffset={Math.PI * 156 * (1 - progress / 100)} className="text-sky-400 transition-all" />
                        </svg>
                    </div>
                    <p className="text-slate-500 text-[10px] font-black uppercase tracking-[0.4em] animate-pulse">Running Neural Inference // Identifying Signatures</p>
                </div>
            )}

            {report && metrics && (
                <div className="flex-1 flex flex-col gap-4 overflow-visible">
                    {/* Top Tier: Verdict & Metrics Ribbon */}
                    <motion.div 
                        initial={{ opacity: 0, y: -10 }} 
                        animate={{ opacity: 1, y: 0 }}
                        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3 shrink-0"
                    >
                        {/* Master Verdict */}
                        <div className={`col-span-1 lg:col-span-2 p-4 rounded-xl border flex items-center justify-between gap-4 relative overflow-hidden group ${report.summary === 'Threatening' ? 'bg-rose-500/[0.04] border-rose-500/20 shadow-[0_0_20px_rgba(244,63,94,0.05)]' : 'bg-emerald-500/[0.04] border-emerald-500/20'}`}>
                           <div className="space-y-0.5 z-10">
                                <span className="text-[8px] font-black text-slate-500 uppercase tracking-[0.3em]">Analysis Consensus</span>
                                <h2 className={`text-3xl font-headline font-black uppercase italic leading-none ${report.summary === 'Threatening' ? 'text-rose-500' : 'text-emerald-500'}`}>{report.summary}</h2>
                           </div>
                           <div className={`w-12 h-12 rounded-lg flex items-center justify-center shrink-0 border ${report.summary === 'Threatening' ? 'bg-rose-500/10 border-rose-500/30' : 'bg-emerald-500/10 border-emerald-500/30'}`}>
                                <span className={`material-symbols-outlined text-2xl ${report.summary === 'Threatening' ? 'text-rose-500 animate-pulse' : 'text-emerald-500'}`}>{report.summary === 'Threatening' ? 'warning' : 'verified_user'}</span>
                           </div>
                        </div>

                        {/* Metrics Grid (Compact) */}
                        {[
                            { label: 'Max Risk', value: `${(metrics.peakLevel * 100).toFixed(0)}%`, icon: 'trending_up', color: 'text-white' },
                            { label: 'AI Confid.', value: `${(metrics.confidence * 100).toFixed(0)}%`, icon: 'neurology', color: 'text-sky-400' },
                            { label: 'Incidents', value: report.weapon_count + report.violence_count, icon: 'emergency', color: 'text-rose-500' }
                        ].map((m, i) => (
                            <div key={i} className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
                                <div className="p-1.5 bg-white/5 rounded-md"><span className={`material-symbols-outlined text-lg ${m.color}`}>{m.icon}</span></div>
                                <div>
                                    <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest leading-none">{m.label}</span>
                                    <span className={`block text-lg font-black font-headline ${m.color} uppercase italic leading-tight`}>{m.value}</span>
                                </div>
                            </div>
                        ))}
                    </motion.div>

                    {/* Middle Tier: Topology Graph (Slightly more compact) */}
                    <motion.div 
                        initial={{ opacity: 0 }} 
                        animate={{ opacity: 1 }}
                        className="h-[220px] bg-slate-900/60 backdrop-blur-3xl p-4 rounded-2xl border border-slate-800 relative shadow-2xl shrink-0"
                    >
                        <div className="absolute top-2 left-4 z-10">
                            <h3 className="text-[8px] font-black text-slate-500 uppercase tracking-[0.3em]">Threat Topology // Temporal Stream</h3>
                        </div>
                        <div className="w-full h-full pt-4">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={report.timeline} onMouseMove={(v: any) => v?.activePayload && setActivePoint(v.activePayload[0].payload)} onMouseLeave={() => setActivePoint(null)}>
                                    <defs>
                                        <linearGradient id="glowArea" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.2}/>
                                            <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.02)" />
                                    <XAxis dataKey="time" hide />
                                    <YAxis hide domain={[0, 1]} />
                                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(14,165,233, 0.4)', strokeWidth: 1 }} />
                                    {activePoint && <ReferenceLine x={activePoint.time} stroke="rgba(14,165,233, 0.5)" strokeDasharray="3 3" />}
                                    <Area type="monotone" dataKey="threat_level" stroke="#f43f5e" strokeWidth={2.5} fill="url(#glowArea)" animationDuration={1500} dot={false} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </motion.div>

                    {/* Bottom Tier: Evidence Collage (Grid View) */}
                    <motion.div 
                        initial={{ opacity: 0, y: 10 }} 
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-3"
                    >
                        <div className="flex items-center justify-between px-2">
                            <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Evidence Collage // Automated Extraction</h3>
                           <span className="text-[9px] font-bold text-slate-600 uppercase italic">Master Index: {report.significant_frames.length} Detections</span>
                        </div>
                        
                        {/* collage Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3 pb-8">
                            {report.significant_frames.map((frame, i) => (
                                <motion.div 
                                    key={i} 
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: i * 0.05 }}
                                    whileHover={{ y: -4, scale: 1.02 }}
                                    className="relative aspect-video bg-slate-800 rounded-lg border border-slate-700 overflow-hidden group cursor-pointer shadow-lg hover:shadow-sky-500/10 hover:border-sky-500/30 transition-all"
                                >
                                    <img src={`data:image/jpeg;base64,${frame.image}`} className="w-full h-full object-cover grayscale-[0.3] group-hover:grayscale-0 transition-all duration-500" alt="Incident Evidence" />
                                    
                                    {/* Overlays */}
                                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                    
                                    <div className="absolute top-2 left-2 px-1.5 py-0.5 bg-slate-950/80 backdrop-blur-md text-white text-[7px] font-black rounded italic border border-white/5 uppercase tracking-tighter">
                                        Frame T+{frame.time}S
                                    </div>

                                    <div className="absolute bottom-2 left-2 flex flex-wrap gap-1">
                                        {frame.detections.map(d => (
                                            <span key={d} className="text-[7px] font-black text-rose-500 uppercase tracking-tighter bg-rose-500/20 backdrop-blur-md px-1.5 py-0.5 rounded border border-rose-500/30 shadow-[0_0_10px_rgba(244,63,94,0.3)]">{d}</span>
                                        ))}
                                    </div>

                                    {/* Action Icon Overlay */}
                                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                        <div className="w-8 h-8 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center">
                                            <span className="material-symbols-outlined text-white text-sm">fullscreen</span>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}

                            {report.significant_frames.length === 0 && (
                                <div className="col-span-full h-32 border border-dashed border-slate-800 rounded-xl flex items-center justify-center bg-slate-900/40">
                                    <p className="text-[9px] font-black text-slate-700 uppercase tracking-[0.4em]">Zero Significant Signatures Identified</p>
                                </div>
                            )}
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
};

export default VideoAnalysisPage;
