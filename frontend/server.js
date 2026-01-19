const express = require("express");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const FormData = require("form-data");
const axios = require("axios");

const app = express();
const upload = multer({ dest: "uploads/" });

app.use(express.static(path.join(__dirname, "public")));

app.post(
  "/upload",
  upload.fields([
    { name: "pre_report", maxCount: 1 },
    { name: "post_report", maxCount: 1 },
    { name: "pre_csv", maxCount: 1 },
    { name: "post_csv", maxCount: 1 }
  ]),
  async (req, res) => {
    try {
      if (!req.files) {
        return res.status(400).json({ error: "No files received by Node server" });
      }

      console.log("FILES RECEIVED BY NODE:", Object.keys(req.files));

      const form = new FormData();

      for (const key in req.files) {
        const file = req.files[key][0];
        form.append(key, fs.createReadStream(file.path));
      }

      // 👉 Send to Flask backend
      const response = await axios.post(
        "http://127.0.0.1:8000/upload",
        form,
        { headers: form.getHeaders() }
      );

      res.json(response.data);

    } catch (err) {
      console.error("UPLOAD ERROR:", err.message);
      res.status(500).json({ error: "Backend connection failed" });
    }
  }
);

app.listen(3000, () => {
  console.log("🌐 Frontend running on http://localhost:3000");
});
