import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiGet } from "../api/client";

function useCurrentOperator() {
  const navigate = useNavigate();

  const [operator, setOperator] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    async function loadCurrentOperator() {
      try {
        const data = await apiGet("/api/v1/auth/me");
        setOperator(data);
      } catch (err) {
        setAuthError(err.message);
        navigate("/login");
      } finally {
        setAuthLoading(false);
      }
    }

    loadCurrentOperator();
  }, [navigate]);

  return {
    operator,
    authLoading,
    authError,
  };
}

export default useCurrentOperator;
