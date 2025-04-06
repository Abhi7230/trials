import React, { useState } from "react";
import { createDigioRequest } from "./api";

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleCreateRequest = async () => {
    setLoading(true);
    try {
      const response = await createDigioRequest(
        "https://example.com/document.pdf",
        ["user1@email.com", "user2@email.com"]
      );
      setResult({ success: true, data: response.data });
    } catch (error) {
      setResult({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Digio API Integration</h1>
      <button onClick={handleCreateRequest} disabled={loading}>
        {loading ? "Processing..." : "Create Digio Request"}
      </button>
      {result && (
        <div style={{ color: result.success ? "green" : "red" }}>
          {result.success ? "Success!" : `Error: ${result.error}`}
        </div>
      )}
    </div>
  );
}

export default App;