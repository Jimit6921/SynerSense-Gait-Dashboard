let apiData = null;

// ================= UPLOAD FILES =================
async function upload() {
  try {
    const fd = new FormData();

    const ids = ["pre_report", "post_report", "pre_csv", "post_csv"];

    for (const id of ids) {
      const el = document.getElementById(id);

      if (!el || !el.files || !el.files[0]) {
        alert("❗ Please upload all 4 files (2 PDFs + 2 CSVs)");
        return;
      }

      fd.append(id, el.files[0]);
    }

    const res = await fetch("/upload", {
      method: "POST",
      body: fd
    });

    if (!res.ok) {
      alert("❌ Upload failed. Backend error.");
      return;
    }

    apiData = await res.json();

    if (apiData.error) {
      alert("❌ " + apiData.error);
      return;
    }

    // show UI sections
    document.getElementById("patientBox").classList.remove("hidden");
    document.getElementById("tables").classList.remove("hidden");

    showPatient("pre");
    loadTables();

  } catch (err) {
    console.error("UPLOAD ERROR:", err);
    alert("❌ Unexpected upload error. Check console.");
  }
}

// ================= SHOW PATIENT =================
function showPatient(type) {
  if (!apiData) return;

  const p = type === "pre"
    ? apiData.pre_patient
    : apiData.post_patient;

  const box = document.getElementById("patientDetails");

  if (!p) {
    box.innerHTML = "<p>No patient data available</p>";
    return;
  }

  let html = "";
  for (const k in p) {
    html += `<p><b>${k}</b>: ${p[k] ?? "N/A"}</p>`;
  }

  box.innerHTML = html;
}

// ================= LOAD TABLES =================
function loadTables() {
  if (!apiData) return;

  // ---------- TEMPORAL & SPATIAL ----------
  let t =
    "<tr><th>Description</th><th>Unit</th><th>Side</th><th>Pre</th><th>Post</th></tr>";

  if (Array.isArray(apiData.temporal) && apiData.temporal.length > 0) {
    apiData.temporal.forEach(r => {
      t += `<tr>${r.map(x => `<td>${x ?? "N/A"}</td>`).join("")}</tr>`;
    });
  } else {
    t += `<tr><td colspan="5">No temporal data available</td></tr>`;
  }

  document.getElementById("temporal").innerHTML = t;

  // ---------- KINEMATIC ----------
  let k =
    "<tr><th>Joint</th><th>Pre Min</th><th>Pre Max</th><th>Post Min</th><th>Post Max</th></tr>";

  if (Array.isArray(apiData.kinematic) && apiData.kinematic.length > 0) {
    apiData.kinematic.forEach(r => {
      k += `<tr>${r.map(x => `<td>${x ?? "N/A"}</td>`).join("")}</tr>`;
    });
  } else {
    k += `<tr><td colspan="5">No kinematic data available</td></tr>`;
  }

  document.getElementById("kinematic").innerHTML = k;
}
