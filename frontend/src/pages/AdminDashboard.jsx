import { useEffect, useMemo, useState } from "react";
import { getAllEmployees } from "../lib/api";

export default function AdminDashboard({ user }) {
  const [employees, setEmployees] = useState([]);
  const [search, setSearch] = useState("");
  const [pendingOnly, setPendingOnly] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const result = await getAllEmployees(user.token);
        setEmployees(result.items || result.employees || []);
      } catch (err) {
        setError(err.message || "Failed to load employees");
      }
    }
    load();
  }, [user.token]);

  const filtered = useMemo(() => {
    return employees
      .filter((emp) =>
        `${emp.name || ""} ${emp.department || ""}`.toLowerCase().includes(search.toLowerCase())
      )
      .filter((emp) => !pendingOnly || emp.status !== "Ready for Joining");
  }, [employees, pendingOnly, search]);

  return (
    <div className="page">
      <h1>HR Admin Dashboard</h1>
      <div className="filters">
        <input
          placeholder="Search employee"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <label>
          <input
            type="checkbox"
            checked={pendingOnly}
            onChange={(e) => setPendingOnly(e.target.checked)}
          />
          Pending only
        </label>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Employee</th>
              <th>Dept</th>
              <th>DOJ</th>
              <th>Progress</th>
              <th>Blocker</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((emp) => (
              <tr key={emp.employee_id}>
                <td>{emp.name}</td>
                <td>{emp.department}</td>
                <td>{emp.joining_date}</td>
                <td>{emp.overall_status || "0%"}</td>
                <td>{emp.missing_docs?.join(", ") || "None"}</td>
                <td>{emp.status || "Pending"}</td>
              </tr>
            ))}
            {!filtered.length && (
              <tr>
                <td colSpan={6}>No employees found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
