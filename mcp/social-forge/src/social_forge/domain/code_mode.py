"""Validated Code Mode limits. No setting can disable authorization or grant issuance rules."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CodeModeSettings:
    deno: str = "deno"
    principal: str = "workspace-owner"
    allowed_platforms: tuple[str, ...] = ()
    timeout_ms: int = 10000
    cpu_ms: int = 5000
    memory_mb: int = 256
    max_output_bytes: int = 65536
    max_code_bytes: int = 32768
    max_calls: int = 32
    max_concurrency: int = 4

    @classmethod
    def from_dict(cls, data: dict) -> "CodeModeSettings":
        value = cls(**data)
        if not isinstance(value.deno, str) or not value.deno:
            raise ValueError("invalid Code Mode deno setting")
        if not isinstance(value.principal, str) or not value.principal or len(value.principal) > 128:
            raise ValueError("invalid Code Mode principal")
        from .platforms import get
        if not isinstance(value.allowed_platforms, (list, tuple)):
            raise TypeError("Code Mode allowed_platforms must be a list")
        for platform in value.allowed_platforms:
            get(platform)
        for name, low, high in (("timeout_ms", 100, 30000), ("cpu_ms", 100, 30000),
                                ("memory_mb", 64, 512), ("max_output_bytes", 1024, 1048576),
                                ("max_code_bytes", 128, 65536), ("max_calls", 1, 128),
                                ("max_concurrency", 1, 8)):
            number = getattr(value, name)
            if type(number) is not int or not low <= number <= high:
                raise ValueError(f"code_mode.{name} must be {low}..{high}")
        return value


class CodeModeError(ValueError):
    """Public errors contain fixed messages, never underlying service exceptions."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)
