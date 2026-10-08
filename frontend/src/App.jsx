import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import Home from './pages/Home.jsx';
import ReportLost from './pages/ReportLost.jsx';
import ReportFound from './pages/ReportFound.jsx';
import ItemDetails from './pages/ItemDetails.jsx';
import MyItems from './pages/MyItems.jsx';

function AppLayout() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="main-content" id="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/report-lost" element={<ReportLost />} />
          <Route path="/report-found" element={<ReportFound />} />
          <Route path="/items/:id" element={<ItemDetails />} />
          <Route path="/my-items" element={<MyItems />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <footer className="app-footer">
          <span><span className="footer-signal" /> CampusFind demo board</span>
          <span>Saved only in this browser · Not an official campus verification service</span>
        </footer>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
