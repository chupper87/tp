import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { Clock, Eye, EyeOff, AlertCircle, Loader2 } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

export default function Login() {
  const { isAuthenticated, login, loginError, isLoggingIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  if (isAuthenticated) return <Navigate to="/" replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await login({ email, password });
    } catch {
      // error is captured in loginError
    }
  }

  return (
    <div className="ocean-bg min-h-screen flex items-center justify-center px-4">
      {/* Subtle radial glow behind the card */}
      <div className="fixed inset-0 pointer-events-none">
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-[0.04]"
          style={{
            background:
              "radial-gradient(circle, var(--color-glow) 0%, transparent 70%)",
          }}
        />
      </div>

      <div className="w-full max-w-[400px] animate-fade-up relative">
        {/* Brand */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-ocean/80 border border-reef mb-6">
            <Clock className="w-7 h-7 text-glow" strokeWidth={1.5} />
          </div>
          <h1 className="font-display text-[2rem] font-800 tracking-[0.2em] text-moon uppercase">
            Timepiece
          </h1>
          <p className="mt-2 text-sm text-mist/60 tracking-wide">
            Schemaläggning för hemtjänst
          </p>
        </div>

        {/* Login card */}
        <div className="card-glow rounded-2xl bg-ocean/60 backdrop-blur-sm p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Error banner */}
            {loginError && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-coral/10 border border-coral/20">
                <AlertCircle className="w-4 h-4 text-coral mt-0.5 shrink-0" />
                <p className="text-sm text-coral">{loginError.detail}</p>
              </div>
            )}

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-600 text-mist/80 uppercase tracking-wider mb-2"
              >
                E-post
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-11 px-4 rounded-lg bg-deep border border-reef text-moon placeholder:text-sediment text-sm font-display focus:border-glow/50 focus:outline-none transition-colors"
                placeholder="anna@hemtjanst.se"
              />
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-xs font-600 text-mist/80 uppercase tracking-wider mb-2"
              >
                Lösenord
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-11 px-4 pr-11 rounded-lg bg-deep border border-reef text-moon placeholder:text-sediment text-sm font-display focus:border-glow/50 focus:outline-none transition-colors"
                  placeholder="Ange lösenord"
                />
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-sediment hover:text-mist transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoggingIn}
              className="w-full h-11 rounded-lg bg-glow/90 hover:bg-glow text-abyss font-700 text-sm tracking-wide uppercase transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
            >
              {isLoggingIn ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loggar in...
                </>
              ) : (
                "Logga in"
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center mt-8 text-xs text-sediment">
          Timepiece v1.0
        </p>
      </div>
    </div>
  );
}
