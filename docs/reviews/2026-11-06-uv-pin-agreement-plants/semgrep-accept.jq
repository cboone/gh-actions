(.results | type == "array") and
(.errors | type == "array") and
(.results | length == 0) and
all(.errors[];
  .rule_id == "javascript.crypto-js.cryptojs-weak-algorithm.cryptojs-weak-algorithm" and
  .path == "docs/reviews/2026-11-06-uv-pin-agreement-plants/verdict.mjs" and
  (.message | contains("only supported in the Pro engine")))
