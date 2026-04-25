import { useState } from "react";
import { generateUploadUrl, uploadFileToS3 } from "../lib/api";

const REQUIRED_DOCS = [
  { label: "ID Proof", value: "id-proof" },
  { label: "Degree Certificate", value: "degree" },
  { label: "Offer Letter", value: "offer-letter" },
];

export default function UploadDocs({ user }) {
  const [docType, setDocType] = useState(REQUIRED_DOCS[0].value);
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleUpload(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!file) {
      setError("Select a file to upload");
      return;
    }

    const extension = file.name.split(".").pop()?.toLowerCase();
    const uploadFileName = `${docType}.${extension}`;
    const employeeId = user.employeeId || localStorage.getItem("employee_id");
    if (!employeeId) {
      setError("Missing employee_id in local storage");
      return;
    }

    setLoading(true);
    try {
      const urlResult = await generateUploadUrl(
        {
          employee_id: employeeId,
          file_name: uploadFileName,
          file_size: file.size,
          content_type: file.type,
        },
        user.token
      );
      await uploadFileToS3(urlResult.upload_url, file);
      setMessage(`${uploadFileName} uploaded successfully`);
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <h1>Upload Onboarding Documents</h1>
      <form className="card" onSubmit={handleUpload}>
        <label>Document Type</label>
        <select value={docType} onChange={(e) => setDocType(e.target.value)}>
          {REQUIRED_DOCS.map((doc) => (
            <option key={doc.value} value={doc.value}>
              {doc.label}
            </option>
          ))}
        </select>

        <label>Choose File</label>
        <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => setFile(e.target.files?.[0])} />

        <button type="submit" disabled={loading}>
          {loading ? "Uploading..." : "Upload File"}
        </button>
      </form>
      {message && <p className="success">{message}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
