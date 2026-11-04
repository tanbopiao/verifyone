"""统一验证门面 —— 道统算子谱（verifyone）
道统出处：验证合一
工程映射：聚合恒证/圭臬/玄圭的统一验证入口
生长纪律：本地生长自由，推送远端需治理决议发令。
"""

class VerifyFacade:
    """统一验证门面：登记各路验证器，verify_all 聚合为总判定。

    验证器可为：
    - callable() -> {"ok": bool, "detail": str}
    - 算子实例：duck-typing 适配 .check() 或 .run_all()
    """

    def __init__(self):
        self._verifiers = {}                 # {name: verifier}，次序即登记序

    def describe(self) -> dict:
        return {"name": "verifyone", "role": "聚合恒证/圭臬/玄圭的统一验证入口",
                "stage": "m1", "verifiers": len(self._verifiers)}

    def register(self, name, verifier):
        """登记验证器；重名即拒绝（只增不覆盖）。"""
        if name in self._verifiers:
            raise ValueError(f"验证器 {name} 已登记，重名拒绝")
        self._verifiers[name] = self._adapt(verifier)

    @staticmethod
    def _adapt(verifier):
        """鸭子类型适配：统一包装为 callable() -> {"ok": bool, "detail": str}。"""
        if callable(verifier) and not hasattr(verifier, "check") and not hasattr(verifier, "run_all"):
            def plain():
                r = verifier()
                if not isinstance(r, dict) or "ok" not in r:
                    raise TypeError("验证器须返回 {'ok': bool, 'detail': str}")
                return {"ok": bool(r["ok"]), "detail": str(r.get("detail", ""))}
            return plain
        if hasattr(verifier, "check") and callable(getattr(verifier, "check")):
            def via_check():
                r = verifier.check()
                if isinstance(r, dict) and "ok" in r:
                    return {"ok": bool(r["ok"]), "detail": str(r.get("detail", ""))}
                return {"ok": bool(r), "detail": "check() 返回非字典，按布尔判定"}
            return via_check
        if hasattr(verifier, "run_all") and callable(getattr(verifier, "run_all")):
            def via_run_all():
                r = verifier.run_all(verifier)
                if not isinstance(r, dict) or "ok" not in r:
                    raise TypeError("run_all() 须返回 {'ok': bool, ...}")
                detail = "; ".join(f["rule"] for f in r.get("failed", [])) or "全绿"
                return {"ok": bool(r["ok"]), "detail": detail}
            return via_run_all
        raise TypeError(f"验证器不可适配：{type(verifier).__name__}")

    def verify_all(self):
        """聚合所有验证器结果：任一失败则整体不通过；无验证器视为未验证。"""
        results = []
        for name, fn in self._verifiers.items():
            try:
                r = fn()
            except Exception as exc:                     # 验证器自身崩坏视同失败
                r = {"ok": False, "detail": f"验证器执行异常：{type(exc).__name__}: {exc}"}
            results.append({"name": name, **r})
        return {"overall_ok": bool(results) and all(r["ok"] for r in results),
                "results": results}
