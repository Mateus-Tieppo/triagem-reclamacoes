import { defineConfig, devices } from "@playwright/test";

// BASE_URL=https://... roda o mesmo fluxo contra o site publicado.
const site = process.env.BASE_URL;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  reporter: "list",
  use: { baseURL: site ?? "http://localhost:4321", ...devices["Desktop Chrome"], reducedMotion: "reduce" },
  projects: [
    { name: "desktop", use: { viewport: { width: 1440, height: 900 } } },
    { name: "celular", use: { viewport: { width: 375, height: 812 }, hasTouch: true, isMobile: true } },
  ],
  webServer: site
    ? undefined
    : {
        command: "npx serve out -l 4321 --no-clipboard",
        url: "http://localhost:4321",
        reuseExistingServer: !process.env.CI,
      },
});
