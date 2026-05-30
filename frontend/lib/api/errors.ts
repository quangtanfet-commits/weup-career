/**
 * Backend error envelope (the hardened `ErrorEnvelope` component in the
 * OpenAPI schema). The typed clients surface failures as `ApiError` so callers
 * never have to parse raw responses.
 */
export interface ErrorEnvelopeShape {
  readonly code?: string;
  readonly message?: string;
  readonly detail?: unknown;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | undefined;
  readonly body: unknown;

  constructor(status: number, message: string, code?: string, body?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.body = body;
  }
}

/** Best-effort extraction of a human message + code from a failed response. */
export async function toApiError(response: Response): Promise<ApiError> {
  let body: unknown = undefined;
  let message = `HTTP ${response.status}`;
  let code: string | undefined;
  try {
    body = await response.json();
    if (body && typeof body === "object") {
      const env = body as ErrorEnvelopeShape & { error?: ErrorEnvelopeShape };
      const envelope = env.error ?? env;
      if (typeof envelope.message === "string") message = envelope.message;
      if (typeof envelope.code === "string") code = envelope.code;
    }
  } catch {
    // Non-JSON error body — keep the default message.
  }
  return new ApiError(response.status, message, code, body);
}
