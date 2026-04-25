export default function Navbar({ user, onLogout, onNavigate, page }) {
  return (
    <header className="navbar">
      <h2>Smart Onboarding</h2>
      <nav className="nav-links">
        {user?.role === "employee" && (
          <>
            <button
              className={page === "employee" ? "active" : ""}
              onClick={() => onNavigate("employee")}
            >
              Dashboard
            </button>
            <button
              className={page === "upload" ? "active" : ""}
              onClick={() => onNavigate("upload")}
            >
              Upload Docs
            </button>
          </>
        )}
        {user?.role === "admin" && (
          <button
            className={page === "admin" ? "active" : ""}
            onClick={() => onNavigate("admin")}
          >
            HR Dashboard
          </button>
        )}
        <button onClick={onLogout}>Logout</button>
      </nav>
    </header>
  );
}
