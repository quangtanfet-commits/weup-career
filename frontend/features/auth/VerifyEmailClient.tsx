"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import { verifyEmail } from "@/lib/api/endpoints/auth";
import {
  VerifyEmailView,
  type VerifyState,
} from "@/features/auth/VerifyEmailView";

/**
 * Owns the verify-email state machine (email-verification-2026-06.md §3.2). Reads
 * `?token=` and POSTs it once on mount: 204 → success, any error (or a missing
 * token) → the generic invalid state. Runs entirely in the browser — it must not
 * be statically prerendered with a token and it performs a single side-effecting
 * POST, so the parent wraps it in a Suspense boundary for `useSearchParams`.
 */
export function VerifyEmailClient() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  // A missing token is invalid synchronously at render, so the effect never has
  // to call setState in its body — its only setState calls live in the async POST
  // callbacks (react-hooks/set-state-in-effect forbids synchronous in-effect
  // setState).
  const [state, setState] = useState<VerifyState>(
    token ? "verifying" : "invalid",
  );
  const started = useRef(false);

  useEffect(() => {
    if (!token) return;
    // Guard against React StrictMode double-invoke consuming the single-use
    // token twice (the second call would 401 and flip a real success to invalid).
    if (started.current) return;
    started.current = true;

    verifyEmail(token).then(
      () => setState("success"),
      () => setState("invalid"),
    );
  }, [token]);

  return <VerifyEmailView state={state} />;
}
