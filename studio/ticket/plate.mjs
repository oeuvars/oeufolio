// Photographs the ticket's own typesetting from the running site, for studio/ticket/ticket.py to print on the
// card: everything the contact page prints on the ticket but its picture, as one black-on-white plate per ink the
// type is printed in (black, red, teal). ticket.py prints the picture from ink.py's plates into the same place.
//
//   pnpm dev                                  (in another terminal)
//   node studio/ticket/plate.mjs
//
// Writes studio/ticket/art/plate-<ink>.png, the ticket's 15 x 29.6 em at DENSITY pixels to the em. Uses the headless
// Chromium helper from the oeusume studio; set OEUSUME if that checkout is not in ~/Documents/oeusume, and URL if
// the site is not on localhost:3000. Run it again after changing anything printed on the ticket.
import { writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { setTimeout as sleep } from "node:timers/promises";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const OEUSUME = process.env.OEUSUME ?? join(homedir(), "Documents", "oeusume");
const { open } = await import(join(OEUSUME, "studio", "browser.mjs"));
const URL = process.env.URL ?? "http://localhost:3000/contact";
// Texture pixels per em: ticket.py lays its sheet out at this density.
const DENSITY = 96;

const INKS = ["k", "red", "teal"];
const page = await open();
const { send, run } = page;

await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 2600, deviceScaleFactor: 1, mobile: false });
await send("Emulation.setEmulatedMedia", { media: "screen", features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
await send("Page.navigate", { url: URL });
await sleep(4000);
await run("document.fonts.ready.then(() => true)");

// Only the plate shows, in black on white. Everything printed is set to the paper's colour unless it is in the ink
// being shot; svg follows the text's colour. The picture is left out.
await run(`(() => {
  const style = document.createElement("style");
  style.id = "plate";
  style.textContent = \`
    html, body { background: #fff !important; }
    body * { visibility: hidden !important; transition: none !important; animation: none !important; filter: none !important; }
    body *::before, body *::after { display: none !important; }
    [data-plate], [data-plate] * { visibility: visible !important; color: #fff !important; text-decoration: none !important; }
    [data-plate] svg, [data-plate] svg * { fill: currentColor !important; }
    [data-art] { visibility: hidden !important; }
  \`;
  document.head.append(style);
  const ink = document.createElement("style");
  ink.id = "ink";
  document.head.append(ink);
})()`);
if (!(await run(`!!document.getElementById("plate") && getComputedStyle(document.querySelector("img")).visibility === "hidden"`))) {
  throw new Error("The page reloaded while the plate was being set up. Run it again once the dev server is idle.");
}

const selector = JSON.stringify('[data-plate="ticket"]');
const em = Number(await run(`parseFloat(getComputedStyle(document.querySelector(${selector})).fontSize)`));
await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 2600, deviceScaleFactor: DENSITY / em, mobile: false });
await sleep(800);
const box = JSON.parse(
  await run(`(() => {
    const rect = document.querySelector(${selector}).getBoundingClientRect();
    return JSON.stringify({ x: rect.x + scrollX, y: rect.y + scrollY, width: rect.width, height: rect.height });
  })()`),
);

// The first shot after the page is scaled up comes back before it has repainted, blank. It is taken and thrown away.
await send("Page.captureScreenshot", { format: "png", clip: { ...box, scale: 1 }, captureBeyondViewport: true });

// One plate per ink that type is printed in. The picture is printed by ticket.py from ink.py's plates.
for (const ink of INKS) {
  const own = ink === "k" ? "[data-plate] *:not([data-ink]):not([data-ink] *)" : `[data-plate] [data-ink="${ink}"], [data-plate] [data-ink="${ink}"] *`;
  await run(`(() => {
    document.getElementById("ink").textContent = ${JSON.stringify(`${own} { color: #000 !important; }`)};
    return new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(() => done(true))));
  })()`);
  await sleep(500);
  const shot = await send("Page.captureScreenshot", { format: "png", clip: { ...box, scale: 1 }, captureBeyondViewport: true });
  writeFileSync(join(HERE, "art", `plate-${ink}.png`), Buffer.from(shot.result.data, "base64"));
}
console.log("plates", `${(box.width / em).toFixed(3)} x ${(box.height / em).toFixed(3)} em at ${em.toFixed(2)} px`);
page.close();
