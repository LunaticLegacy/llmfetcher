"""Platform-aware subprocess lifecycle helpers."""

from __future__ import annotations

import ctypes
import os
import signal
import subprocess
from typing import Any


_WINDOWS = os.name == "nt"
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000


if _WINDOWS:
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class _IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64),
        ]

    class _BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class _ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _BasicLimitInformation),
            ("IoInfo", _IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    _kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    _kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    _kernel32.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    _kernel32.SetInformationJobObject.restype = ctypes.c_int
    _kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    _kernel32.AssignProcessToJobObject.restype = ctypes.c_int
    _kernel32.TerminateJobObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    _kernel32.TerminateJobObject.restype = ctypes.c_int
    _kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    _kernel32.CloseHandle.restype = ctypes.c_int


def popen_platform_kwargs() -> dict[str, Any]:
    """Return subprocess creation options for the current operating system."""
    if _WINDOWS:
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def attach_process_tree(process: subprocess.Popen[Any]) -> None:
    """Attach a process to a kill-on-close Windows Job Object when possible."""
    if not _WINDOWS:
        return
    try:
        job = _kernel32.CreateJobObjectW(None, None)
        if not job:
            raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
        limits = _ExtendedLimitInformation()
        limits.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not _kernel32.SetInformationJobObject(
            job, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            raise OSError(ctypes.get_last_error(), "SetInformationJobObject failed")
        process_handle = ctypes.c_void_p(int(process._handle))
        if not _kernel32.AssignProcessToJobObject(job, process_handle):
            raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject failed")
        setattr(process, "_llmfetcher_job", job)
    except (OSError, AttributeError, TypeError, ValueError):
        try:
            if "job" in locals() and job:
                _kernel32.CloseHandle(job)
        except Exception:
            pass


def terminate_process_tree(process: subprocess.Popen[Any]) -> None:
    """Terminate a process and all descendants, using native platform APIs."""
    if _WINDOWS:
        job = getattr(process, "_llmfetcher_job", None)
        if job:
            try:
                _kernel32.TerminateJobObject(job, 1)
                return
            finally:
                _kernel32.CloseHandle(job)
                setattr(process, "_llmfetcher_job", None)
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            return
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            return
        except (AttributeError, OSError, ProcessLookupError):
            pass
    try:
        process.kill()
    except (OSError, ProcessLookupError):
        pass


def close_process_tree(process: subprocess.Popen[Any]) -> None:
    """Release a Windows Job Object after normal process completion."""
    if not _WINDOWS:
        return
    job = getattr(process, "_llmfetcher_job", None)
    if job:
        _kernel32.CloseHandle(job)
        setattr(process, "_llmfetcher_job", None)
