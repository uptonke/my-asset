import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('assets/js/src/app.bundle.source.js', 'utf8');
assert.equal(source, fs.readFileSync('assets/js/app.bundle.js', 'utf8'));
const start = source.indexOf('function simulateGbmVsJumpPaths(');
const end = source.indexOf('function normCdf(', start);
assert.ok(start >= 0 && end > start, 'GBM helper not found');
const ctx = vm.createContext({});
vm.runInContext(source.slice(start, end), ctx);
const simulate = ctx.simulateGbmVsJumpPaths;
const config = {muAnnual: 0.08, sigmaAnnual: 0.2, jumpLambdaAnnual: 0,
    jumpMean: -0.15, jumpStd: 0, horizonWeeks: 52, nSims: 1000, seed: 20261124};
const baseline = simulate(config);
assert.deepEqual(baseline.baseline, baseline.jumpStress, 'zero jumps must give identical paths');
const stressedConfig = {...config, jumpLambdaAnnual: 4};
const stressed = simulate(stressedConfig);
assert.deepEqual(stressed, simulate(stressedConfig), 'fixed seed must be reproducible');
assert.equal(stressed.nSims, 1000);
assert.equal(stressed.horizonWeeks, 52);
for (const row of [stressed.baseline, stressed.jumpStress]) {
    for (const value of Object.values(row)) assert.ok(Number.isFinite(value));
    assert.ok(row.es95 <= row.p5 && row.p5 <= row.p50 && row.p50 <= row.p95);
    assert.ok(row.medianMdd >= -1 && row.medianMdd <= 0);
    for (const p of [row.lossProb, row.mdd10Prob, row.mdd20Prob]) assert.ok(p >= 0 && p <= 1);
    assert.ok(row.mdd20Prob <= row.mdd10Prob);
}
assert.ok(stressed.jumpStress.p50 < stressed.baseline.p50);
assert.ok(stressed.jumpStress.es95 < stressed.baseline.es95);
assert.equal(simulate({...config, sigmaAnnual: 0}), null);
assert.equal(simulate({...config, muAnnual: NaN}), null);
console.log('GBM path simulation regression checks passed');
