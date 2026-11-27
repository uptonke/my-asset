import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('assets/js/src/app.bundle.source.js', 'utf8');
assert.equal(source, fs.readFileSync('assets/js/app.bundle.js', 'utf8'));
const start = source.indexOf('function modifiedDietzPeriod(');
const end = source.indexOf('const enrichedHistory', start);
assert.ok(start >= 0 && end > start);
const transactions = {value: [
    {type: 'Deposit', date: '2026-01-03', totalCashFlow: 100},
    {type: 'Withdraw', date: '2026-01-05', totalCashFlow: -20},
    {type: 'Deposit', date: '2026-01-01', totalCashFlow: 500},
    {type: 'Buy', date: '2026-01-03', totalCashFlow: -50},
    {type: 'Deposit', date: '2026-01-06', totalCashFlow: 500},
]};
const ctx = vm.createContext({transactions});
vm.runInContext(source.slice(start, end), ctx);
const t0 = Date.parse('2026-01-01'), t1 = Date.parse('2026-01-05');
const result = ctx.modifiedDietzPeriod(1000, 1185, t0, t1);
assert.equal(result.totalFlow, 80);
assert.equal(result.weightedFlow, 50);
assert.equal(result.denominator, 1050);
assert.equal(result.flowCount, 2);
assert.ok(Math.abs(result.periodReturn - 0.1) < 1e-12);
assert.equal(ctx.modifiedDietzPeriod(0, 1185, t0, t1), null);
assert.equal(ctx.modifiedDietzPeriod(1000, 1185, t1, t0), null);
assert.match(source, /strict_twr_available:\s*false/);
assert.match(source, /modified_dietz_return_annualized/);
console.log('Frontend performance semantics regression checks passed');
