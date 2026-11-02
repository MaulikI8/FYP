import { describe, expect, it, vi } from "vitest";
import { api } from "./api";

describe("typed API client", () => {
  it("keeps session credentials on read requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "ready", api_version: "v1" }) });
    vi.stubGlobal("fetch", fetchMock);

    const response = await api<{ status: string }>("/health/");

    expect(response.status).toBe("ready");
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/health/", expect.objectContaining({ credentials: "include" }));
  });
});
