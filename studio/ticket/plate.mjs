// Photographs the ticket's own typesetting from the running site, for studio/ticket/ticket.py to press
// into the card: everything the contact page prints on the ticket, and the engraving cut by engrave.py in
// its place, as black ink on white. Then the conductor's stamp, on its own.
//
//   pnpm dev                                  (in another terminal)
//   node studio/ticket/plate.mjs
//
// Writes studio/ticket/art/plate.png and studio/ticket/art/stamp.png, each the ticket's 15 x 31 em at
// DENSITY pixels to the em. Uses the headless Chromium helper from the oeusume studio; set OEUSUME if that
// checkout is not in ~/Documents/oeusume. Run it again after changing anything printed on the ticket.
import { readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { setTimeout as sleep } from "node:timers/promises";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const OEUSUME = process.env.OEUSUME ?? join(homedir(), "Documents", "oeusume");
const { open } = await import(join(OEUSUME, "studio", "browser.mjs"));
const URL = process.env.URL ?? "http://localhost:3000/contact";
// Texture pixels per em: ticket.py's sheet is laid out at this density.
const DENSITY = 96;

const art = `data:image/png;base64,${readFileSync(join(HERE, "art", "street-ink.png")).toString("base64")}`;
const page = await open();
const { send, run } = page;

await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await send("Emulation.setEmulatedMedia", { media: "screen", features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
await send("Page.navigate", { url: URL });
await sleep(4000);
await run("document.fonts.ready.then(() => true)");

// Only the plate shows, in black on white. The engraving is white on black, so it is turned over.
await run(`(() => {
  const style = document.createElement("style");
  style.textContent = \`
    html, body { background: #fff !important; }
    body * { visibility: hidden !important; transition: none !important; animation: none !important; filter: none !important; }
    body *::before, body *::after { display: none !important; }
    [data-plate].shown, [data-plate].shown * { visibility: visible !important; color: #000 !important; text-decoration: none !important; }
    [data-art] { background-image: url(${art}); filter: invert(1) !important; }
  \`;
  document.head.append(style);
})()`);

for (const name of ["ticket", "stamp"]) {
  const selector = JSON.stringify(`[data-plate="${name}"]`);
  const em = Number(
    await run(`(() => {
      document.querySelectorAll("[data-plate]").forEach((el) => el.classList.remove("shown"));
      const el = document.querySelector(${selector});
      el.classList.add("shown");
      return parseFloat(getComputedStyle(el).fontSize);
    })()`),
  );
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: DENSITY / em, mobile: false });
  await sleep(600);
  const box = JSON.parse(
    await run(`(() => {
      const rect = document.querySelector(${selector}).getBoundingClientRect();
      return JSON.stringify({ x: rect.x + scrollX, y: rect.y + scrollY, width: rect.width, height: rect.height });
    })()`),
  );
  const shot = await send("Page.captureScreenshot", { format: "png", clip: { ...box, scale: 1 }, captureBeyondViewport: true });
  writeFileSync(join(HERE, "art", `${name === "ticket" ? "plate" : "stamp"}.png`), Buffer.from(shot.result.data, "base64"));
  console.log(name, `${(box.width / em).toFixed(3)} x ${(box.height / em).toFixed(3)} em at ${em.toFixed(2)} px`);
}
page.close();
