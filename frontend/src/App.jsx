import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import Home from './pages/Home.jsx';
import ReportLost from './pages/ReportLost.jsx';
import ReportFound from './pages/ReportFound.jsx';
import ItemDetails from './pages/ItemDetails.jsx';
import MyItems from './pages/MyItems.jsx';
import SignIn from './pages/SignIn.jsx';
import SignUp from './pages/SignUp.jsx';
import { getStoredAuth } from './services/api.js';

function ProtectedRoute({ children }) {
  const location = useLocation();
  if (!getStoredAuth()) {
    return <Navigate to="/sign-in" replace state={{ from: location }} />;
  }
  return children;
}

function AppLayout() {
  const location = useLocation();
  if (location.pathname === '/sign-in') {
    return <SignIn />;
  }
  if (location.pathname === '/sign-up') {
    return <SignUp />;
  }

  return (
    <div className="app-shell">
      <Navbar />
      <main className="main-content" id="main-content">
        <Routes>
          <Route path="/sign-in" element={<SignIn />} />
          <Route path="/sign-up" element={<SignUp />} />
          <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
          <Route path="/report-lost" element={<ProtectedRoute><ReportLost /></ProtectedRoute>} />
          <Route path="/report-found" element={<ProtectedRoute><ReportFound /></ProtectedRoute>} />
          <Route path="/items/:id" element={<ProtectedRoute><ItemDetails /></ProtectedRoute>} />
          <Route path="/my-items" element={<ProtectedRoute><MyItems /></ProtectedRoute>} />
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

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}

export default App;

