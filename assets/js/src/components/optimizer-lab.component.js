export const OptimizerLabComponent = {
  id: "optimizer-lab",
  version: "v4.3",
  label: "最佳化",
  runtimeStatus: "registered_not_independently_bundled",
  sourceOfTruth: "assets/js/src/app.bundle.source.js",
  owns: [
    "optimizer decision center",
    "rebalance candidates",
    "risk reduction simulator",
    "human approval and audit trail",
    "regime / Black-Litterman / governance panels"
  ],
  migrationBoundary: "Do not split runtime until schema validation and bundle source check pass."
};
