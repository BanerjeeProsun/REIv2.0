import win32api  # type: ignore
import win32con  # type: ignore
import win32job  # type: ignore
import subprocess


class ProcessJobObject:
    def __init__(self) -> None:
        self.hJob = win32job.CreateJobObject(None, "")
        info = win32job.QueryInformationJobObject(self.hJob, win32job.JobObjectExtendedLimitInformation)
        info["BasicLimitInformation"]["LimitFlags"] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        win32job.SetInformationJobObject(self.hJob, win32job.JobObjectExtendedLimitInformation, info)

    def assign_process(self, process: subprocess.Popen[bytes] | subprocess.Popen[str]) -> None:
        handle = win32api.OpenProcess(win32con.PROCESS_SET_QUOTA | win32con.PROCESS_TERMINATE, False, process.pid)
        try:
            win32job.AssignProcessToJobObject(self.hJob, handle)
        finally:
            win32api.CloseHandle(handle)
