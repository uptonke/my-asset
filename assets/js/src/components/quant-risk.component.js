export const QuantRiskComponent = {
  id: "quant-risk",
  version: "v4.3",
  label: "量化風控",
  runtimeStatus: "registered_not_independently_bundled",
  sourceOfTruth: "assets/js/src/app.bundle.source.js",
  owns: [
    "risk metrics",
    "VaR / ES display",
    "drawdown and risk contribution panels",
    "risk x-ray cards"
  ],
  migrationBoundary: "Extract only after v4.6 validation gate remains green."
};
