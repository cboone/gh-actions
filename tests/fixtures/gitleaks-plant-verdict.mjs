import { assertionLabel } from "./gitleaks-assertion-verdict.mjs";

try {
  await import("../check-gitleaks-base-config.mjs");
} catch (error) {
  const label = assertionLabel(error);
  if (label === null) throw error;
  console.log(`GITLEAKS_VERDICT assertion: ${label}`);
  process.exitCode = 1;
}
