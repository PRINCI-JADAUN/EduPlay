import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "./api.js";

describe("API error responses", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("identifies non-JSON server errors and the failing endpoint", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      text: () => Promise.resolve("<html>Internal Server Error</html>"),
    }));

    await expect(api("/players/")).rejects.toThrow(
      "The server returned a non-JSON response for /players/ (HTTP 500). Check the backend logs for the error.",
    );
  });
});
