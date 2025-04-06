import axios from "axios";

const API_BASE_URL = "http://localhost:5000";

export const createDigioRequest = async (document_url, signers) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/digio/create-request`, {
      document_url,
      signers,
    });
    return response.data;
  } catch (error) {
    throw error.response.data;
  }
};