import { useEffect, useState } from "react";
import { getEmployeeStatus } from "../lib/api";
import ProgressBar from "../components/ProgressBar";
import StatusCard from "../components/StatusCard";

export default function EmployeeDashboard({ user }) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const employeeId = user.employeeId || localStorage.getItem("employee_id");
        if (!employeeId) return;
        const result = await getEmployeeStatus(employeeId, user.token);
        setStatus(result);
      } catch (err) {
        setError(err.message);
      }
    }
    load();
  }, [user.token]);

  const overall = status?.overall_status
    ? Number(String(status.overall_status).replace("%", ""))
    : 0;

  return (
    <div className="page">
      <h1>Welcome {status?.name || user.email} 👋</h1>
      <p>Joining Date: {status?.joining_date || "Not available"}</p>
      <ProgressBar value={overall} />
      {error && <p className="error">{error}</p>}

      <div className="grid">
        <StatusCard label="Docs" status={status?.documents_status || "Pending"} />
        <StatusCard label="IT Setup" status={status?.it_stage || "Pending"} />
        <StatusCard
          label="Laptop"
          status={status?.asset_assigned ? `Assigned (${status?.asset_id})` : "Pending"}
        />
        <StatusCard label="Manager Intro" status={status?.manager_stage || "Pending"} />
        <StatusCard label="Day 1 Ready" status={status?.day1_ready ? "Complete" : "Pending"} />
      </div>
    </div>
  );
}
