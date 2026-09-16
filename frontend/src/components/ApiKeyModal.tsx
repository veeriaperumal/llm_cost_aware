"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Key,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Trash2,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  Zap,
} from "lucide-react";

export interface SavedKeyInfo {
  id: string;
  user_id: string;
  provider_name: string;
  key_hint: string;
  is_valid: boolean;
  last_validated_at?: string;
  created_at?: string;
  updated_at?: string;
}

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  onKeysUpdated?: () => void;
}

interface ProviderMeta {
  id: string;
  name: string;
  tier1: string;
  tier2: string;
  freeTier: boolean;
  docUrl: string;
  placeholder: string;
}

const PROVIDERS: ProviderMeta[] = [
  {
    id: "gemini",
    name: "Google Gemini",
    tier1: "Gemini 2.5 Flash Lite",
    tier2: "Gemini 2.5 Flash",
    freeTier: true,
    docUrl: "https://aistudio.google.com/app/apikey",
    placeholder: "AIzaSy...",
  },
  {
    id: "groq",
    name: "Groq Cloud",
    tier1: "Llama 3.1 8B Instant",
    tier2: "Llama 3.3 70B Versatile",
    freeTier: true,
    docUrl: "https://console.groq.com/keys",
    placeholder: "gsk_...",
  },
  {
    id: "anthropic",
    name: "Anthropic Claude",
    tier1: "Claude 3.5 Haiku",
    tier2: "Claude 3.5 Sonnet",
    freeTier: false,
    docUrl: "https://console.anthropic.com/settings/keys",
    placeholder: "sk-ant-...",
  },
  {
    id: "openai",
    name: "OpenAI",
    tier1: "GPT-4o-mini",
    tier2: "GPT-4o",
    freeTier: false,
    docUrl: "https://platform.openai.com/api-keys",
    placeholder: "sk-proj-...",
  },
  {
    id: "mistral",
    name: "Mistral AI",
    tier1: "Mistral Small",
    tier2: "Mistral Large",
    freeTier: false,
    docUrl: "https://console.mistral.ai/api-keys",
    placeholder: "...",
  },
];

export const ApiKeyModal: React.FC<ApiKeyModalProps> = ({
  isOpen,
  onClose,
  userId,
  onKeysUpdated,
}) => {
  const [savedKeys, setSavedKeys] = useState<Record<string, SavedKeyInfo>>({});
  const [inputKeys, setInputKeys] = useState<Record<string, string>>({});
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [loadingMap, setLoadingMap] = useState<Record<string, boolean>>({});
  const [validationStatus, setValidationStatus] = useState<
    Record<string, { isValid: boolean; message: string } | null>
  >({});
  const [fetching, setFetching] = useState<boolean>(false);

  const fetchKeys = async () => {
    if (!userId) return;
    setFetching(true);
    try {
      const res = await fetch(`/api/keys?user_id=${encodeURIComponent(userId)}`, {
        headers: { "X-User-ID": userId },
      });
      if (res.ok) {
        const data: SavedKeyInfo[] = await res.json();
        const map: Record<string, SavedKeyInfo> = {};
        data.forEach((k) => {
          map[k.provider_name.toLowerCase()] = k;
        });
        setSavedKeys(map);
      }
    } catch (e) {
      console.error("Failed to load user API keys:", e);
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchKeys();
      setValidationStatus({});
    }
  }, [isOpen, userId]);

  if (!isOpen) return null;

  const handleTestKey = async (providerId: string) => {
    const rawKey = inputKeys[providerId];
    const saved = savedKeys[providerId];

    if (!rawKey && !saved) {
      setValidationStatus((prev) => ({
        ...prev,
        [providerId]: { isValid: false, message: "Please enter an API key to test" },
      }));
      return;
    }

    setLoadingMap((prev) => ({ ...prev, [providerId]: true }));
    try {
      const res = await fetch(`/api/keys/validate?user_id=${encodeURIComponent(userId)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-ID": userId,
        },
        body: JSON.stringify({
          provider_name: providerId,
          api_key: rawKey || undefined,
        }),
      });
      const data = await res.json();
      setValidationStatus((prev) => ({
        ...prev,
        [providerId]: { isValid: data.is_valid, message: data.message },
      }));
    } catch (e: any) {
      setValidationStatus((prev) => ({
        ...prev,
        [providerId]: { isValid: false, message: e.message || "Validation failed" },
      }));
    } finally {
      setLoadingMap((prev) => ({ ...prev, [providerId]: false }));
    }
  };

  const handleSaveKey = async (providerId: string) => {
    const rawKey = inputKeys[providerId];
    if (!rawKey || !rawKey.trim()) return;

    setLoadingMap((prev) => ({ ...prev, [providerId]: true }));
    try {
      const res = await fetch(`/api/keys?user_id=${encodeURIComponent(userId)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-ID": userId,
        },
        body: JSON.stringify({
          provider_name: providerId,
          api_key: rawKey.trim(),
        }),
      });

      if (res.ok) {
        const saved: SavedKeyInfo = await res.json();
        setSavedKeys((prev) => ({ ...prev, [providerId]: saved }));
        setInputKeys((prev) => ({ ...prev, [providerId]: "" }));
        setValidationStatus((prev) => ({
          ...prev,
          [providerId]: { isValid: true, message: "Key encrypted & saved successfully in DB" },
        }));
        if (onKeysUpdated) onKeysUpdated();
      } else {
        let errMsg = `Server error (${res.status})`;
        try {
          const err = await res.json();
          errMsg = err.detail || errMsg;
        } catch {
          // Response was HTML (e.g. 500/502), not JSON
        }
        setValidationStatus((prev) => ({
          ...prev,
          [providerId]: { isValid: false, message: errMsg },
        }));
      }
    } catch (e: any) {
      setValidationStatus((prev) => ({
        ...prev,
        [providerId]: { isValid: false, message: e.message || "Failed to save key" },
      }));
    } finally {
      setLoadingMap((prev) => ({ ...prev, [providerId]: false }));
    }
  };

  const handleDeleteKey = async (providerId: string) => {
    setLoadingMap((prev) => ({ ...prev, [providerId]: true }));
    try {
      const res = await fetch(`/api/keys/${providerId}?user_id=${encodeURIComponent(userId)}`, {
        method: "DELETE",
        headers: { "X-User-ID": userId },
      });
      if (res.ok) {
        setSavedKeys((prev) => {
          const next = { ...prev };
          delete next[providerId];
          return next;
        });
        setInputKeys((prev) => ({ ...prev, [providerId]: "" }));
        setValidationStatus((prev) => ({
          ...prev,
          [providerId]: null,
        }));
        if (onKeysUpdated) onKeysUpdated();
      }
    } catch (e) {
      console.error("Failed to delete key:", e);
    } finally {
      setLoadingMap((prev) => ({ ...prev, [providerId]: false }));
    }
  };

  const configuredCount = Object.keys(savedKeys).length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl max-h-[92vh] flex flex-col rounded-2xl bg-[#1e1e1e] border border-neutral-700 text-neutral-100 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-neutral-800 bg-[#252525]">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white">Manage LLM API Keys</h2>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  {configuredCount} Active in DB
                </span>
              </div>
              <p className="text-xs text-neutral-400 mt-0.5">
                Encrypted with AES-Fernet. Router dynamically resolves user keys for Tier 1 & Tier 2.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-700 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Security Notice */}
        <div className="px-5 py-2.5 bg-blue-950/30 border-b border-blue-900/30 flex items-center gap-2 text-xs text-blue-300">
          <ShieldCheck className="w-4 h-4 text-blue-400 shrink-0" />
          <span>
            Keys are encrypted in PostgreSQL. Raw values are never returned to the frontend.
          </span>
        </div>

        {/* Key List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {PROVIDERS.map((p) => {
            const saved = savedKeys[p.id];
            const valStatus = validationStatus[p.id];
            const isLoading = loadingMap[p.id];
            const inputValue = inputKeys[p.id] || "";
            const isRevealed = showKey[p.id] || false;

            return (
              <div
                key={p.id}
                className="p-4 rounded-xl bg-[#282828] border border-neutral-800 hover:border-neutral-700 transition space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="font-semibold text-sm text-neutral-100">{p.name}</span>
                    {p.freeTier ? (
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                        Free Tier Available
                      </span>
                    ) : (
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-neutral-700 text-neutral-300">
                        Paid / Pay-As-You-Go
                      </span>
                    )}
                    {saved && (
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-blue-500/15 text-blue-400 border border-blue-500/20 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Configured ({saved.key_hint})
                      </span>
                    )}
                  </div>
                  <a
                    href={p.docUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 transition"
                  >
                    Get Key <ExternalLink className="w-3 h-3" />
                  </a>
                </div>

                <div className="text-xs text-neutral-400 flex items-center gap-3">
                  <span>
                    <strong className="text-neutral-300">Tier 1:</strong> {p.tier1}
                  </span>
                  <span>•</span>
                  <span>
                    <strong className="text-neutral-300">Tier 2:</strong> {p.tier2}
                  </span>
                </div>

                {/* Input & Action buttons */}
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <input
                      type={isRevealed ? "text" : "password"}
                      value={inputValue}
                      onChange={(e) =>
                        setInputKeys((prev) => ({ ...prev, [p.id]: e.target.value }))
                      }
                      placeholder={saved ? `Update saved key (${saved.key_hint})` : `Paste your ${p.name} API Key`}
                      className="w-full bg-[#1c1c1c] border border-neutral-700 focus:border-blue-500 text-neutral-100 text-xs rounded-lg px-3 py-2 pr-9 outline-none transition font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKey((prev) => ({ ...prev, [p.id]: !isRevealed }))}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-white"
                    >
                      {isRevealed ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>

                  {inputValue.trim() ? (
                    <button
                      onClick={() => handleSaveKey(p.id)}
                      disabled={isLoading}
                      className="px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition flex items-center gap-1.5 shrink-0 disabled:opacity-50"
                    >
                      {isLoading ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      )}
                      Save Key
                    </button>
                  ) : null}

                  {(inputValue.trim() || saved) && (
                    <button
                      onClick={() => handleTestKey(p.id)}
                      disabled={isLoading}
                      className="px-3 py-2 rounded-lg bg-neutral-700 hover:bg-neutral-600 text-neutral-200 text-xs font-medium transition flex items-center gap-1.5 shrink-0 disabled:opacity-50"
                      title="Test API Key"
                    >
                      {isLoading ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Zap className="w-3.5 h-3.5 text-amber-400" />
                      )}
                      Test
                    </button>
                  )}

                  {saved && (
                    <button
                      onClick={() => handleDeleteKey(p.id)}
                      disabled={isLoading}
                      className="p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 transition shrink-0"
                      title="Delete saved key"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Validation Feedback */}
                {valStatus && (
                  <div
                    className={`p-2 rounded-lg text-xs flex items-center gap-2 ${
                      valStatus.isValid
                        ? "bg-emerald-950/40 border border-emerald-800/40 text-emerald-300"
                        : "bg-red-950/40 border border-red-800/40 text-red-300"
                    }`}
                  >
                    {valStatus.isValid ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    ) : (
                      <AlertCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                    )}
                    <span>{valStatus.message}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-neutral-800 bg-[#252525]">
          <span className="text-xs text-neutral-400">
            Session ID: <code className="text-neutral-300">{userId.slice(0, 16)}...</code>
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-neutral-700 hover:bg-neutral-600 text-white text-xs font-medium transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
