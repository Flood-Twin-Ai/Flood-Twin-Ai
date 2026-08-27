import { Routes, Route } from "react-router-dom";
import AuthorityDashboard from "./pages/AuthorityDashboard.jsx";
import CitizenDashboard from "./pages/CitizenDashboard.jsx";
import Alerts from "./pages/Alerts.jsx";
import Shelters from "./pages/Shelters.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AuthorityDashboard />} />
      <Route path="/citizen" element={<CitizenDashboard />} />
      <Route path="/alerts" element={<Alerts />} />
      <Route path="/shelters" element={<Shelters />} />
    </Routes>
  );
}
