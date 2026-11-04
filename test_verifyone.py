import os
import sys
import unittest
import importlib.util

# 直接按文件路径加载两枚算子核心，规避 sys.path 多入口同名模块歧义。
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load(mod_name, relpath):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(_BASE, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_verifyone = _load("verifyone_core", os.path.join("verifyone", "verifyone.py"))
_guinie = _load("guinie_core", os.path.join("guinie", "guinie.py"))
VerifyFacade = _verifyone.VerifyFacade
Gate = _guinie.Gate

class _StubCheck:
    def check(self):
        return {"ok": True, "detail": "恒证探针全绿"}

class _StubGate:
    def __init__(self):
        self.g = Gate()
        self.g.register("r", lambda t: (True, "过"))
    def run_all(self, target):
        return self.g.run_all(target)

class T(unittest.TestCase):
    def test_all_green_overall_ok(self):
        v = VerifyFacade()
        v.register("心跳", lambda: {"ok": True, "detail": "alive"})
        v.register("门禁", _StubGate())
        r = v.verify_all()
        self.assertTrue(r["overall_ok"])

    def test_single_failure_blocks_overall(self):
        v = VerifyFacade()
        v.register("绿", lambda: {"ok": True, "detail": "好"})
        v.register("红", lambda: {"ok": False, "detail": "探针掉线"})
        r = v.verify_all()
        self.assertFalse(r["overall_ok"])

    def test_aggregation_contains_each_result(self):
        v = VerifyFacade()
        v.register("甲", lambda: {"ok": True, "detail": "甲过"})
        v.register("乙", lambda: {"ok": False, "detail": "乙败"})
        names = [r["name"] for r in v.verify_all()["results"]]
        self.assertEqual(names, ["甲", "乙"])

    def test_registration_order_irrelevant(self):
        def build(order):
            v = VerifyFacade()
            for name, fn in order:
                v.register(name, fn)
            return v.verify_all()["overall_ok"]
        self.assertTrue(build([("a", lambda: {"ok": True}), ("b", lambda: {"ok": True})]))
        self.assertFalse(build([("a", lambda: {"ok": False}), ("b", lambda: {"ok": True})]))
        self.assertFalse(build([("b", lambda: {"ok": True}), ("a", lambda: {"ok": False})]))

    def test_verifier_exception_counts_as_failed(self):
        v = VerifyFacade()
        v.register("炸裂", lambda: 1 / 0)
        r = v.verify_all()
        self.assertFalse(r["overall_ok"])
        self.assertIn("ZeroDivisionError", r["results"][0]["detail"])

    def test_check_style_verifier_adapted(self):
        v = VerifyFacade()
        v.register("恒证", _StubCheck())
        r = v.verify_all()
        self.assertTrue(r["overall_ok"])
        self.assertEqual(r["results"][0]["detail"], "恒证探针全绿")

if __name__ == "__main__":
    unittest.main()
