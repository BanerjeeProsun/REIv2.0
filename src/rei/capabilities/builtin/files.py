from pydantic import BaseModel, ConfigDict, HttpUrl, Field
from rei.capabilities.spec import CapabilitySpec, RiskTier, DataClass, RateLimit
from rei.policy.schemas import PrivacyMode


class DownloadFileArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    url: HttpUrl = Field(..., max_length=2048)
    name: str = Field(..., max_length=255, pattern=r"^[\w\-. ]+$")


files_download_spec = CapabilitySpec(
    id="files.download",
    version=1,
    summary="Download a file",
    tier=RiskTier.R3,
    args_model=DownloadFileArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=True,
    reversible=False,
    allow_when_tainted=True,
    confirm_template="Download {url} as {name}",
    timeout_s=300.0,
    rate_limit=RateLimit(limit=10, period_s=3600),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)


def files_download_handler(args: DownloadFileArgs) -> dict[str, str]:
    print(f"Mock downloading file from {args.url} as {args.name}")
    return {"status": "success", "file": args.name}
