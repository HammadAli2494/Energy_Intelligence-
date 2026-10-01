import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Analytics from './pages/Analytics'
import Anomalies from './pages/Anomalies'
import AnomalyDetail from './pages/AnomalyDetail'
import Contact from './pages/Contact'
import Dashboard from './pages/Dashboard'
import Forecast from './pages/Forecast'
import Methodology from './pages/Methodology'
import ModelPerformance from './pages/ModelPerformance'
import NotFound from './pages/NotFound'
import Privacy from './pages/Privacy'
import Terms from './pages/Terms'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Navigate to="/" replace />} />
        <Route path="/forecast" element={<Forecast />} />
        <Route path="/anomalies" element={<Anomalies />} />
        <Route path="/anomalies/:anomalyId" element={<AnomalyDetail />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/model" element={<ModelPerformance />} />
        <Route path="/about" element={<Methodology />} />
        <Route path="/methodology" element={<Methodology />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/terms" element={<Terms />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}

export default App
