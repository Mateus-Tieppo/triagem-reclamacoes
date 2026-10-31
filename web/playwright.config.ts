import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  reporter: "list",
  use: { baseURL: "http://localhost:4321", ...devices["Desktop Chrome"], reducedMotion: "reduce" },
  projects: [
    { name: "desktop", use: { viewport: { width: 1440, height: 900 } } },
    { name: "celular", use: { viewport: { width: 375, height: 812 }, hasTouch: true, isMobile: true } },
  ],
  webServer: {
    command: "npx serve out -l 4321 --no-clipboard",
    url: "http://localhost:4321",
    reuseExistingServer: !process.env.CI,
  },
});
