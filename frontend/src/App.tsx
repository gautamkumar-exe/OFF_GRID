import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import ThreatMapPage from './pages/ThreatMapPage';
import LiveFeedsPage from './pages/LiveFeedsPage';
import CamerasPage from './pages/CamerasPage';
import IncidentsPage from './pages/IncidentsPage';
import SupportPage from './pages/SupportPage';
import EmergencyOperationsPage from './pages/EmergencyOperationsPage';
import LogExplorerPage from './pages/LogExplorerPage';
import VideoAnalysisPage from './pages/VideoAnalysisPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<Navigate to="/threat-map" replace />} />
          <Route path="/threat-map" element={<ThreatMapPage />} />
          <Route path="/live-feeds" element={<LiveFeedsPage />} />
          <Route path="/cameras" element={<CamerasPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/support" element={<SupportPage />} />
          <Route path="/emergency" element={<EmergencyOperationsPage />} />
          <Route path="/video-analysis" element={<VideoAnalysisPage />} />
          <Route path="/logs" element={<LogExplorerPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
