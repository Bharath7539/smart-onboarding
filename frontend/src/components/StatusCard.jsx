export default function StatusCard({ label, status }) {
  const statusText = status || "Pending";
  const tone =
    statusText === "Complete"
      ? "complete"
      : statusText === "In Progress"
        ? "progress"
        : statusText === "Blocked"
          ? "blocked"
          : "pending";

  return (
    <div className={`status-card ${tone}`}>
      <span>{label}</span>
      <strong>{statusText}</strong>
    </div>
  );
}
