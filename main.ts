// news-image-20261120 — THE WORLD TODAY, Friday 20 November 2026.
// Entry program (@bosbuilds): the front-page image sits beside this file as
// entry.png. This program checks it is a well-formed 1024x1024 PNG inside
// the 1 MiB cap, then copies it to $MAKEFUN_OUTPUT_DIR/entry.png
// (default /output/entry.png). Node 22 standard library only, no network.
// The copy is byte-for-byte the input, so repeated runs agree exactly.

import { copyFileSync, mkdirSync, readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const MAX_BYTES = 1024 * 1024;
const EDGE = 1024;

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, "entry.png");
const outDir = process.env.MAKEFUN_OUTPUT_DIR || "/output";
const target = join(outDir, "entry.png");

const data = readFileSync(source);

if (data.length > MAX_BYTES) {
  throw new Error(
    `entry.png is ${data.length} bytes, over the ${MAX_BYTES} byte cap`,
  );
}
if (data.length < 33 || !data.subarray(0, 8).equals(PNG_MAGIC)) {
  throw new Error("entry.png is not a PNG file");
}
if (data.toString("latin1", 12, 16) !== "IHDR") {
  throw new Error("entry.png has no IHDR chunk first");
}
const width = data.readUInt32BE(16);
const height = data.readUInt32BE(20);
if (width !== EDGE || height !== EDGE) {
  throw new Error(`entry.png is ${width}x${height}, expected ${EDGE}x${EDGE}`);
}

mkdirSync(outDir, { recursive: true });
copyFileSync(source, target);

// Verify the copy is byte-identical to the validated input.
const written = readFileSync(target);
const digest = (buf) => createHash("sha256").update(buf).digest("hex");
if (digest(written) !== digest(data)) {
  throw new Error("copy differs from entry.png after write");
}
console.log(`wrote ${target} (${data.length} bytes, ${width}x${height})`);
