const express = require("express");
const axios = require("axios");
const mongoose = require("mongoose");
const cors = require("cors");
require("dotenv").config();

const app = express();
app.use(express.json());
app.use(cors());

// MongoDB Connection
mongoose.connect(process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/digio_logs", {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});
const db = mongoose.connection;
db.on("error", console.error.bind(console, "MongoDB connection error:"));
db.once("open", () => console.log("Connected to MongoDB"));

// Digio Request Schema
const digioRequestSchema = new mongoose.Schema({
  request_id: String,
  document_id: String,
  status: String,
  response_data: Object,
  created_at: { type: Date, default: Date.now }
});
const DigioRequest = mongoose.model("DigioRequest", digioRequestSchema);

// Digio Sandbox API Config
const DIGIO_BASE_URL = "https://ext.digio.in:444";
const CLIENT_ID = "ACK25030511375911186LKWJDXERYTXQ";
const CLIENT_SECRET = "CGYGOZKNCMHN8I8GSA5HH2DFKRSR732L";

// API Endpoints
app.post("/api/digio/create-request", async (req, res) => {
  try {
    const { document_url, signers } = req.body;

    const response = await axios.post(
      `${DIGIO_BASE_URL}/v2/client/document/create_request`,
      {
        document_id: `DOC_${Date.now()}`,
        document_url,
        signers,
        expiry_days: 7,
      },
      {
        headers: {
          Authorization: `Bearer ${CLIENT_ID}:${CLIENT_SECRET}`,
          "Content-Type": "application/json",
        },
      }
    );

    // Save to MongoDB
    const newRequest = new DigioRequest({
      request_id: response.data.request_id,
      document_id: response.data.document_id,
      status: "success",
      response_data: response.data
    });
    await newRequest.save();

    res.json({ success: true, data: response.data });
  } catch (error) {
    console.error(error);
    
    // Save failed attempt
    if (error.response) {
      const failedRequest = new DigioRequest({
        status: "failed",
        response_data: error.response.data
      });
      await failedRequest.save();
    }

    res.status(500).json({ 
      success: false, 
      error: error.response?.data?.message || error.message 
    });
  }
});

// Get all requests (for testing)
app.get("/api/digio/requests", async (req, res) => {
  try {
    const requests = await DigioRequest.find().sort({ created_at: -1 });
    res.json({ success: true, data: requests });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Start Server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));