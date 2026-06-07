export { QuantRiskComponent } from "./quant-risk.component.js";
export { OptimizerLabComponent } from "./optimizer-lab.component.js";
export { MacroIntelligenceComponent } from "./macro-intelligence.component.js";
export { HoldingCardsComponent } from "./holding-cards.component.js";

export const uiComponentSplitPolicy = {
  version: "v4.3",
  mode: "registry_first_safe_split",
  runtimeBundle: "assets/js/app.bundle.js",
  sourceOfTruth: "assets/js/src/app.bundle.source.js",
  rule: "No component becomes authoritative until build, schema, and validation gates pass."
};
