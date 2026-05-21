import axios from "axios";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export default function Register() {
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await axios.post(`${BASE_URL}/auth/register/`, form);
      navigate("/login");
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data ?? {};
        setError(
          Object.values(data).flat().join(" ") || "Registration failed.",
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { key: "username", type: "text", label: "Username" },
    { key: "email", type: "email", label: "Email" },
    { key: "password", type: "password", label: "Password" },
  ] as const;

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">ReviewPulse</h1>
          <p className="text-gray-400 text-sm mt-2">Create your account</p>
        </div>
        <form
          onSubmit={handleSubmit}
          className="bg-gray-900 rounded-xl p-6 border border-gray-800 space-y-4"
        >
          {fields.map(({ key, type, label }) => (
            <div key={key}>
              <label className="text-xs text-gray-400 block mb-1.5 uppercase tracking-wider">
                {label}
              </label>
              <input
                type={type}
                value={form[key]}
                onChange={(e) =>
                  setForm((f) => ({ ...f, [key]: e.target.value }))
                }
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                required
              />
            </div>
          ))}
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg py-2.5 text-sm font-medium transition-colors"
          >
            {loading ? "Creating account…" : "Create Account"}
          </button>
          <p className="text-center text-sm text-gray-400">
            Have an account?{" "}
            <Link to="/login" className="text-indigo-400 hover:text-indigo-300">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
