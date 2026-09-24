import os
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from rei.capabilities.spec import CapabilitySpec, RiskTier, DataClass, RateLimit
from rei.policy.schemas import PrivacyMode


class OpenUrlArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    url: HttpUrl = Field(..., max_length=2048)


web_open_url_spec = CapabilitySpec(
    id="web.open_url",
    version=1,
    summary="Open a URL in the browser",
    tier=RiskTier.R2,
    args_model=OpenUrlArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=True,
    reversible=False,
    allow_when_tainted=True,
    confirm_template="Open URL: {url}",
    timeout_s=5.0,
    rate_limit=RateLimit(limit=10, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)


def web_open_url_handler(args: OpenUrlArgs) -> dict[str, str]:
    # In a real implementation we would check the blocklist here
    url_str = str(args.url)
    os.startfile(url_str)  # noqa: S606
    return {"status": "success", "url": url_str}
