// A headless Chromium for the studio's scripts to photograph pages with, driven over the DevTools protocol. It is
// Playwright's headless shell (npx playwright install chromium-headless-shell); set HEADLESS_SHELL to use another.
//
//   const { send, run, close } = await open();
//
// send(method, params) answers with the protocol's whole reply ({ id, result }); run(expression) answers with the
// expression's value, waiting on it if it is a promise.
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, readdirSync, rmSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";

const CACHE = join(homedir(), "Library", "Caches", "ms-playwright");
const BUILDS = [
  ["chrome-headless-shell-mac-arm64", "chrome-headless-shell"],
  ["chrome-headless-shell-mac-x64", "chrome-headless-shell"],
  ["chrome-mac", "headless_shell"],
];

function shell() {
  if (process.env.HEADLESS_SHELL) return process.env.HEADLESS_SHELL;
  const installs = existsSync(CACHE) ? readdirSync(CACHE).filter((name) => name.startsWith("chromium_headless_shell-")) : [];
  for (const install of installs.sort().reverse()) {
    for (const [folder, binary] of BUILDS) {
      const path = join(CACHE, install, folder, binary);
      if (existsSync(path)) return path;
    }
  }
  throw new Error("No headless shell: run npx playwright install chromium-headless-shell, or set HEADLESS_SHELL.");
}

export async function open() {
  const profile = mkdtempSync(join(tmpdir(), "studio-chromium-"));
  const child = spawn(
    shell(),
    [
      "--remote-debugging-port=0",
      `--user-data-dir=${profile}`,
      "--allow-file-access-from-files",
      "--hide-scrollbars",
      "--no-first-run",
      "about:blank",
    ],
    { stdio: ["ignore", "ignore", "pipe"] },
  );

  // The browser says where it listens on its error stream; its page is found from there.
  const browser = await new Promise((done, fail) => {
    let said = "";
    child.stderr.on("data", (chunk) => {
      said += chunk;
      const found = said.match(/DevTools listening on (ws:\/\/\S+)/);
      if (found) done(new URL(found[1]));
    });
    child.on("exit", (code) => fail(new Error(`The headless shell quit (${code}) before it listened:\n${said}`)));
  });
  const targets = await (await fetch(`http://${browser.host}/json/list`)).json();
  const target = targets.find((each) => each.type === "page");

  const socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((done, fail) => {
    socket.onopen = done;
    socket.onerror = fail;
  });
  const waiting = new Map();
  let last = 0;
  socket.onmessage = ({ data }) => {
    const reply = JSON.parse(data);
    const pending = waiting.get(reply.id);
    if (!pending) return;
    waiting.delete(reply.id);
    if (reply.error) pending.fail(new Error(`${pending.method}: ${reply.error.message}`));
    else pending.done(reply);
  };

  function send(method, params = {}) {
    const id = ++last;
    socket.send(JSON.stringify({ id, method, params }));
    return new Promise((done, fail) => waiting.set(id, { method, done, fail }));
  }

  async function run(expression) {
    const { result } = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text);
    return result.result.value;
  }

  // The profile goes once the browser has quit, as it writes to it until then.
  function close() {
    socket.close();
    child.once("exit", () => rmSync(profile, { recursive: true, force: true }));
    child.kill();
  }

  return { send, run, close };
}
