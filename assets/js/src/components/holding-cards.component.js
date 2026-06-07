export const HoldingCardsComponent = {
  id: "holding-cards",
  version: "v4.3",
  label: "持倉卡片",
  runtimeStatus: "registered_not_independently_bundled",
  sourceOfTruth: "assets/js/src/app.bundle.source.js",
  owns: [
    "holding cards",
    "portfolio table row presentation",
    "position-level metrics display"
  ],
  migrationBoundary: "Split after frontend component registry and DOM anchors are stable."
};
