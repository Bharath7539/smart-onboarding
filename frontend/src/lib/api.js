import { config } from "../config";

async function request(path, options = {}) {
  const url = `${config.apiBaseUrl}${path}`;
  const response = await fetch(url, options);
  const raw = await response.text();
  const data = raw ? JSON.parse(raw) : {};

  if (!response.ok) {
    throw new Error(data.message || "Request failed");
  }
  return data;
}

export async function getEmployeeStatus(employeeId, token) {
  return request(`/employee/${employeeId}/status`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function generateUploadUrl(payload, token) {
  return request("/generate-upload-url", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function uploadFileToS3(uploadUrl, file) {
  const response = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": file.type || "application/octet-stream" },
    body: file,
  });
  if (!response.ok) {
    throw new Error("S3 upload failed");
  }
}

export async function getAllEmployees(token) {
  return request("/admin/employees", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}
