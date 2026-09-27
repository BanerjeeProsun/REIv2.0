from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from rei.capabilities.spec import CapabilitySpec, RiskTier, DataClass, RateLimit
from rei.policy.schemas import PrivacyMode


class SetVolumeArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    level: int = Field(..., ge=0, le=100)


media_set_volume_spec = CapabilitySpec(
    id="media.set_volume",
    version=1,
    summary="Set system volume",
    tier=RiskTier.R1,
    args_model=SetVolumeArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=False,
    reversible=True,
    allow_when_tainted=True,
    confirm_template="Set volume to {level}%",
    timeout_s=5.0,
    rate_limit=RateLimit(limit=20, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)


def media_set_volume_handler(args: SetVolumeArgs) -> dict[str, str | int]:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL # type: ignore
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume # type: ignore

    devices = AudioUtilities.GetSpeakers()
    interface = devices.EndpointVolume if hasattr(devices, "EndpointVolume") else devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    
    # pycaw uses a scalar from 0.0 to 1.0
    scalar = args.level / 100.0
    volume.SetMasterVolumeLevelScalar(scalar, None)
    
    return {"status": "success", "volume": args.level}


MediaAction = Literal["play", "pause", "next", "prev"]


class MediaControlArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: MediaAction


media_control_spec = CapabilitySpec(
    id="media.control",
    version=1,
    summary="Control media playback",
    tier=RiskTier.R1,
    args_model=MediaControlArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=False,
    reversible=True,
    allow_when_tainted=True,
    confirm_template="Media control: {action}",
    timeout_s=5.0,
    rate_limit=RateLimit(limit=30, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)


def media_control_handler(args: MediaControlArgs) -> dict[str, str]:
    import ctypes
    # Virtual-Key Codes for Media Control
    VK_MEDIA_NEXT_TRACK = 0xB0
    VK_MEDIA_PREV_TRACK = 0xB1
    VK_MEDIA_PLAY_PAUSE = 0xB3
    
    key_map = {
        "play": VK_MEDIA_PLAY_PAUSE,
        "pause": VK_MEDIA_PLAY_PAUSE,
        "next": VK_MEDIA_NEXT_TRACK,
        "prev": VK_MEDIA_PREV_TRACK
    }
    
    vk = key_map.get(args.action)
    if vk:
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0) # Key up
        
    return {"status": "success", "action": args.action}
