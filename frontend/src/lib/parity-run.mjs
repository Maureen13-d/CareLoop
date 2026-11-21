import { checksum, triageMaternal } from "./maternalTriage.mjs";

let raw = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  raw += chunk;
});
process.stdin.on("end", () => {
  const input = JSON.parse(raw);
  if (input.checksum_of) {
    process.stdout.write(JSON.stringify({ checksum: checksum(input.checksum_of) }));
    return;
  }
  const result = triageMaternal(input.reading || {}, input.signs || [], input.context || {});
  process.stdout.write(JSON.stringify({ level: result.level, rule_ids: result.rule_ids }));
});
