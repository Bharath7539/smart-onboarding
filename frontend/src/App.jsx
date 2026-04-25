import { useEffect, useState } from "react";
import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import EmployeeDashboard from "./pages/EmployeeDashboard";
import UploadDocs from "./pages/UploadDocs";
import AdminDashboard from "./pages/AdminDashboard";
import { getStoredAuth, logout } from "./lib/auth";

export default function App() {
  const [user, setUser] = useState(getStoredAuth());
  const [page, setPage] = useState("employee");

  useEffect(() => {
    if (!user) return;
    setPage(user.role === "admin" ? "admin" : "employee");
  }, [user]);

  if (!user) {
    return <Login onLogin={setUser} />;
  }

  return (
    <div>
      <Navbar
        user={user}
        page={page}
        onNavigate={setPage}
        onLogout={() => {
          logout();
          setUser(null);
        }}
      />
      {user.role === "admin" && <AdminDashboard user={user} />}
      {user.role === "employee" && page === "employee" && <EmployeeDashboard user={user} />}
      {user.role === "employee" && page === "upload" && <UploadDocs user={user} />}
    </div>
  );
}
