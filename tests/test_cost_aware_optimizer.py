import json
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from run_cost_aware_optimizer import bl_scenario,solve,build,save_snapshot,load_snapshot,CONFIG
from run_skfolio_sandbox import optimizer_snapshot_id

class Phase3(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads(CONFIG.read_text())
        self.ts=["BOXX","GLDM","BTC-USD","00981A","QQQ","VOO","IFRA","VEA"]
        self.buckets=dict(zip(self.ts,["cash","gold","crypto","taiwan_equity","global_equity","global_equity","global_equity","global_equity"]))
        self.r=pd.DataFrame(np.random.default_rng(42).normal(0,[.001,.008,.04,.02,.015,.012,.014,.013],(200,8)),columns=self.ts,index=pd.bdate_range("2025-01-01",periods=200))
        self.w=pd.Series([.15,.05,.10,.10,.15,.15,.10,.20],index=self.ts)
        self.priors=[{"ticker":t,"bucket":self.buckets[t],"relative_score":float(i)/4,"confidence":.6,"current_weight_pct":self.w[t]*100} for i,t in enumerate(self.ts)]
        self.cost=np.array([.001]*8)
    def test_zero_view_shift_returns_prior(self):
        mu,cov,pi,v=bl_scenario(self.r,self.w,self.priors,{**self.cfg,"view_pp_per_score":0})
        np.testing.assert_allclose(mu,pi,atol=1e-12)
    def test_cost_and_floor(self):
        mu,cov,_,_=bl_scenario(self.r,self.w,self.priors,self.cfg)
        for kind in ("cvar","cvar_cost","mean_variance"):
            w,info=solve(self.r,self.w,self.buckets,mu,cov,self.cost,self.cfg,kind,float(mu@self.w)-.02)
            self.assertEqual(info["status"],"OK")
            self.assertLessEqual(info["turnover_pct"],15.00001)
            self.assertAlmostEqual(info["estimated_oneoff_cost_pct"],float(self.cost@np.abs(w-self.w))*100)
            self.assertGreaterEqual(info["net_scenario_excess_return_pct"]+1e-5,info["return_floor_pct"])
    def test_infeasible_floor(self):
        mu,cov,_,_=bl_scenario(self.r,self.w,self.priors,self.cfg)
        w,info=solve(self.r,self.w,self.buckets,mu,cov,self.cost,self.cfg,"cvar_cost",10.)
        self.assertIsNone(w);self.assertEqual(info["status"],"INFEASIBLE")
    def test_snapshot_roundtrip_and_stale_sources(self):
        sources={t:"test" for t in self.ts}
        meta={"snapshot_id":optimizer_snapshot_id(self.r,self.w,"fx",sources),"fx_source":"fx","sources":sources,"asset_buckets":self.buckets}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"snap.npz";save_snapshot(p,self.r,self.w,meta)
            r,w,m=load_snapshot(p);self.assertEqual(m,meta)
            np.testing.assert_array_equal(r.to_numpy(),self.r.to_numpy())
        out=build(self.r,self.w,meta,{"snapshot_id":"stale"},{},self.cfg)
        self.assertEqual(out["status"],"BLOCKED")
        self.assertFalse(out["execution_permission"])
    def test_full_report(self):
        meta={"snapshot_id":"x","asset_buckets":self.buckets,"skipped":[]}
        prior={"snapshot_id":"x","status":"OK","asset_expected_return_priors":self.priors}
        out=build(self.r,self.w,meta,prior,{"snapshot_id":"x","status":"OK"},self.cfg)
        self.assertFalse(out["execution_permission"]);self.assertEqual(len(out["portfolios"]),3)
        self.assertEqual(len(out["sensitivity"]),7)
        json.dumps(out,allow_nan=False)

if __name__=="__main__":
    unittest.main()
