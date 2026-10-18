// Photographs the poster's type (type.html, laid out by type.json) for poster.py to print: one plate for the title
// and one for the passages, white on black, at SCALE times the reference's 736 x 981 pixels.
//
//   node studio/poster/type.mjs
//
// Writes studio/poster/art/title.png and studio/poster/art/body.png, with the headless Chromium in studio/browser.mjs,
// and src/components/poster.json, where the companies named in the passages fall, for poster.py to run a highlighter
// over and for the page to lay their links on.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { setTimeout as sleep } from "node:timers/promises";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const { open } = await import(join(HERE, "..", "browser.mjs"));
const SCALE = 3;
const WIDTH = 736;
const HEIGHT = 981;

const page = await open();
const { send, run, close } = page;
await send("Emulation.setDeviceMetricsOverride", { width: WIDTH, height: HEIGHT, deviceScaleFactor: SCALE, mobile: false });
await send("Page.navigate", { url: pathToFileURL(join(HERE, "type.html")).href });
await sleep(1500);
const layout = readFileSync(join(HERE, "type.json"), "utf8");
const over = await run(`window.lay(${layout})`);
if (over.length) console.warn(`Lines longer than their measure:\n  ${over.join("\n  ")}`);

const marks = await run("window.marks()");
writeFileSync(join(HERE, "..", "..", "src", "components", "poster.json"), `${JSON.stringify({ size: [WIDTH, HEIGHT], marks }, null, 2)}\n`);

mkdirSync(join(HERE, "art"), { recursive: true });
for (const plate of ["title", "body"]) {
  await run(`(() => { document.body.className = ${JSON.stringify(plate)}; return new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(() => done(true)))); })()`);
  await sleep(300);
  const shot = await send("Page.captureScreenshot", { format: "png", clip: { x: 0, y: 0, width: WIDTH, height: HEIGHT, scale: 1 } });
  writeFileSync(join(HERE, "art", `${plate}.png`), Buffer.from(shot.result.data, "base64"));
}
close();
