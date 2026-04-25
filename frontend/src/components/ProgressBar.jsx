export default function ProgressBar({ value = 0 }) {
  const normalized = Math.max(0, Math.min(100, Number(value)));
  return (
    <div>
      <p>Progress: {normalized}%</p>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${normalized}%` }} />
      </div>
    </div>
  );
}
