from __future__ import annotations

import ctypes
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class MacOSActivationResult:
    attempted: bool
    available: bool
    success: bool
    reason: str


def activate_macos_app() -> MacOSActivationResult:
    """Make a Python-hosted Qt GUI behave like a foreground macOS app."""
    if sys.platform != "darwin":
        return MacOSActivationResult(False, False, True, "not_macos")

    try:
        objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]

        ns_application = objc.objc_getClass(b"NSApplication")
        if not ns_application:
            return MacOSActivationResult(True, False, False, "nsapplication_unavailable")

        sel = objc.sel_registerName
        send_id = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", objc))
        send_void = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", objc))
        send_bool_long = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long)(("objc_msgSend", objc))
        send_bool_ulong = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong)(("objc_msgSend", objc))
        send_void_bool = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool)(("objc_msgSend", objc))
        send_void_id = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", objc))

        app = send_id(ns_application, sel(b"sharedApplication"))
        if not app:
            return MacOSActivationResult(True, False, False, "shared_application_unavailable")

        regular_policy = 0
        policy_ok = send_bool_long(app, sel(b"setActivationPolicy:"), regular_policy)
        send_void(app, sel(b"finishLaunching"))
        send_void_id(app, sel(b"unhide:"), None)
        send_void_bool(app, sel(b"activateIgnoringOtherApps:"), True)

        running_application = objc.objc_getClass(b"NSRunningApplication")
        running_ok = False
        if running_application:
            current_app = send_id(running_application, sel(b"currentApplication"))
            if current_app:
                activate_ignoring_other_apps = 1 << 1
                running_ok = send_bool_ulong(current_app, sel(b"activateWithOptions:"), activate_ignoring_other_apps)

        success = bool(policy_ok or running_ok)
        if success:
            reason = "activated" if policy_ok else "activated_running_application"
        else:
            reason = "activation_policy_rejected"
        return MacOSActivationResult(True, True, success, reason)
    except Exception as exc:
        return MacOSActivationResult(True, False, False, f"{exc.__class__.__name__}: {exc}")
