from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import pandas as pd
import re

app = Flask(__name__)
CORS(app)


# ================= HELPERS =================

def clean_text(text):
    return " ".join(text.replace("\n", " ").split()) if text else ""


def extract_patient_from_pdf(pdf_file):
    lines = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                lines.extend(txt.split("\n"))

    patient = {
        "Name": "N/A",
        "Patient ID": "N/A",
        "Gender": "N/A",
        "Age": "N/A",
        "Height": "N/A",
        "Weight": "N/A",
        "DOB": "N/A",
        "Diagnosis": "N/A",
        "Department": "N/A",
        "Study Type": "N/A",
        "Study Date": "N/A",
        "Study Time": "N/A",
        "Consulting Doctor": "N/A"
    }

    for line in lines:
        l = clean_text(line)

        if "Patient Name" in l:
            patient["Name"] = l.split("Patient Name")[-1].replace(":", "").strip()

        if "Patient ID" in l:
            patient["Patient ID"] = (
                l.split("Patient ID")[-1]
                .replace(":", "")
                .strip()
                .split()[0]
            )

        # Gender / Age line: "Gender / :Male / 39 Study Protocol"
        if "Gender" in l and "/" in l:
            temp = l.split("Gender")[-1]
            temp = temp.split("Study")[0]
            temp = temp.replace(":", "").strip()
            parts = [p.strip() for p in temp.split("/") if p.strip()]

            for p in parts:
                if p.lower() in ["male", "female"]:
                    patient["Gender"] = p
                if p.isdigit():
                    patient["Age"] = p

        # Height / Weight line: "Height (cm) / :170 / 90 Study Date"
        if "Height" in l and "/" in l:
            temp = l.split("Height")[-1]
            temp = temp.split("Study")[0]
            temp = temp.replace(":", "").strip()
            nums = [p.strip() for p in temp.split("/") if p.strip().isdigit()]

            if len(nums) >= 2:
                patient["Height"] = nums[0]
                patient["Weight"] = nums[1]

        if "DOB" in l:
            m = re.search(r"\d{2}-\d{2}-\d{4}", l)
            if m:
                patient["DOB"] = m.group()

        if "Study Date" in l:
            m = re.search(r"\d{2}-\d{2}-\d{4}", l)
            if m:
                patient["Study Date"] = m.group()

        if "Study Time" in l:
            m = re.search(r"(\d{1,2})\s*:\s*(\d{2})", l)
            if m:
                patient["Study Time"] = f"{m.group(1)}:{m.group(2)}"

        if "Study Type" in l:
            patient["Study Type"] = (
                l.split("Study Type")[-1]
                .replace(":", "")
                .strip()
            )

        if "Diagnosis" in l:
            diag = l.split("Diagnosis")[-1]
            diag = diag.replace(":", "").replace("/", "").strip()
            patient["Diagnosis"] = diag

        if "Department" in l:
            patient["Department"] = (
                l.split("Department")[-1]
                .split("Consulting")[0]
                .replace(":", "")
                .strip()
            )

        if "Consulting" in l and "Dr" in l:
            patient["Consulting Doctor"] = (
                l.split("Consulting")[-1]
                .replace(":", "")
                .strip()
            )

    return patient


def load_csv_safe(file):
    file.seek(0)
    try:
        df = pd.read_csv(file)
        if not df.empty:
            return df
    except:
        pass

    file.seek(0)
    try:
        df = pd.read_csv(file, sep=";")
        return df
    except:
        return pd.DataFrame()


# ================= ROUTE =================

@app.route("/upload", methods=["POST"])
def upload():
    print("FILES RECEIVED:", request.files)

    pre_report = request.files.get("pre_report")
    post_report = request.files.get("post_report")
    pre_csv = request.files.get("pre_csv")
    post_csv = request.files.get("post_csv")

    if not all([pre_report, post_report, pre_csv, post_csv]):
        return jsonify({"error": "All 4 files required"}), 400

    try:
        pre_patient = extract_patient_from_pdf(pre_report)
        post_patient = extract_patient_from_pdf(post_report)

        pre_df = load_csv_safe(pre_csv)
        post_df = load_csv_safe(post_csv)

        # -------- TEMPORAL (SAFE MEAN) --------
        def val(df, col):
            if col in df.columns:
                s = pd.to_numeric(df[col], errors="coerce").dropna()
                if not s.empty:
                    return round(float(s.mean()), 2)
            return None

        temporal = [
            ["Stride Length", "m", "Left", val(pre_df, "Left_Stride_Length"), val(post_df, "Left_Stride_Length")],
            ["Stride Length", "m", "Right", val(pre_df, "Right_Stride_Length"), val(post_df, "Right_Stride_Length")],
            ["Cadence", "steps/min", "-", val(pre_df, "Cadence"), val(post_df, "Cadence")],
            ["Speed", "m/s", "-", val(pre_df, "Speed"), val(post_df, "Speed")],
        ]

        # -------- KINEMATIC (MIN/MAX) --------
        def krow(label, col):
            return [
                label,
                round(float(pre_df[col].min()), 2),
                round(float(pre_df[col].max()), 2),
                round(float(post_df[col].min()), 2),
                round(float(post_df[col].max()), 2),
            ]

        kinematic = []
        for col in ["LHipAngles_Sag_Z", "LKneeAngles_Sag_Z", "LAnkleAngles_Sag_X"]:
            if col in pre_df.columns and col in post_df.columns:
                kinematic.append(krow(col, col))

        return jsonify({
            "status": "success",
            "pre_patient": pre_patient,
            "post_patient": post_patient,
            "temporal": temporal,
            "kinematic": kinematic
        })

    except Exception as e:
        print("BACKEND ERROR:", e)
        return jsonify({"error": "Processing failed"}), 500


# ================= MAIN =================

if __name__ == "__main__":
    print("🚀 Backend running at http://127.0.0.1:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)
