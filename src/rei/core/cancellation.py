import asyncio

class CancelToken:
    def __init__(self) -> None:
        self._cancelled = False
        self._event = asyncio.Event()
        
    def cancel(self) -> None:
        self._cancelled = True
        self._event.set()
        
    @property
    def is_cancelled(self) -> bool:
        return self._cancelled
        
    async def wait(self) -> None:
        await self._event.wait()
        
    def raise_if_cancelled(self) -> None:
        if self._cancelled:
            raise asyncio.CancelledError()
