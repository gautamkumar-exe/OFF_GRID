import { useEffect, useState } from 'react';

export interface EdgeStats {
    total_alerts: number;
    weapon_alerts: number;
    violence_alerts: number;
    active_dashboards: number;
    avg_confidence: number;
}

export const useEdgeStats = () => {
    const [stats, setStats] = useState<EdgeStats | null>(null);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/v1/stats');
                const data = await response.json();
                setStats(data);
            } catch (err) {
                console.error('[!] Failed to fetch system stats:', err);
            }
        };

        fetchStats();
        const interval = setInterval(fetchStats, 5000); // Poll every 5s

        return () => clearInterval(interval);
    }, []);

    return stats;
};
