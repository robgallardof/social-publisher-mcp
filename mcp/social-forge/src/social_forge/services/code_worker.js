// Trusted bootstrap only. Security is enforced by Deno permissions and the host bridge, not this JS.
const encoder = new TextEncoder();
const decoder = new TextDecoder();
const reader = Deno.stdin.readable.getReader();
let buffer = "";
async function line() {
  while (!buffer.includes("\n")) {
    const { value, done } = await reader.read();
    if (done) throw new Error("bridge_closed");
    buffer += decoder.decode(value, { stream: true });
  }
  const index = buffer.indexOf("\n");
  const result = buffer.slice(0, index);
  buffer = buffer.slice(index + 1);
  return JSON.parse(result);
}
// Deno.stdout.write may perform partial writes. Serialize frames to avoid interleaving Promise.all calls.
let output = Promise.resolve();
function send(value) {
  const bytes = encoder.encode(JSON.stringify(value) + "\n");
  output = output.then(async () => {
    let offset = 0;
    while (offset < bytes.length) offset += await Deno.stdout.write(bytes.subarray(offset));
  });
  return output;
}
const init = await line();
const pending = new Map();
let sequence = 0;
const social = Object.create(null);
for (const name of init.capabilities) {
  const [namespace, method] = name.split(".");
  social[namespace] ??= Object.create(null);
  social[namespace][method] = (args = {}) => {
    if (pending.size >= init.max_concurrency) return Promise.reject(new Error("concurrency_limit"));
    const id = ++sequence;
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      send({ type: "call", id, name, arguments: args }).catch(reject);
    });
  };
}
async function receive() {
  while (true) {
    const response = await line();
    const call = pending.get(response.id);
    if (!call) continue;
    pending.delete(response.id);
    if (response.ok) call.resolve(response.result);
    else call.reject(new Error(response.error));
  }
}
receive().catch(() => {});
try {
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
  const result = await new AsyncFunction("social", '"use strict";\n' + init.code)(social);
  if (pending.size) throw new Error("unawaited_operations");
  await send({ type: "result", result: result ?? null });
} catch {
  // User exception messages can contain arbitrary content. Host returns a fixed, safe classification.
  await send({ type: "error", error: "javascript_error" });
}
Deno.exit(0);
