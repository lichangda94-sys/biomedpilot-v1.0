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

    appkit_result = _activate_with_appkit()
    if appkit_result.success:
        return appkit_result

    services_result = _activate_with_application_services()
    if services_result.success:
        return services_result

    if appkit_result.available or services_result.available:
        reason = f"{appkit_result.reason}; {services_result.reason}"
        return MacOSActivationResult(True, True, False, reason)
    return appkit_result


def _activate_with_appkit() -> MacOSActivationResult:
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
                activate_all_windows = 1 << 0
                activate_ignoring_other_apps = 1 << 1
                running_ok = send_bool_ulong(
                    current_app,
                    sel(b"activateWithOptions:"),
                    activate_all_windows | activate_ignoring_other_apps,
                )

        success = bool(policy_ok or running_ok)
        if success:
            reason = "activated_appkit" if policy_ok else "activated_running_application"
        else:
            reason = "appkit_activation_rejected"
        return MacOSActivationResult(True, True, success, reason)
    except Exception as exc:
        return MacOSActivationResult(True, False, False, f"appkit_{exc.__class__.__name__}: {exc}")


def _activate_with_application_services() -> MacOSActivationResult:
    try:
        services = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        )
    except OSError as exc:
        return MacOSActivationResult(True, False, False, f"application_services_unavailable:{exc}")

    class ProcessSerialNumber(ctypes.Structure):
        _fields_ = [
            ("highLongOfPSN", ctypes.c_uint32),
            ("lowLongOfPSN", ctypes.c_uint32),
        ]

    k_current_process = 2
    k_process_transform_to_foreground_application = 1
    psn = ProcessSerialNumber(0, k_current_process)

    try:
        transform = services.TransformProcessType
        transform.argtypes = [ctypes.POINTER(ProcessSerialNumber), ctypes.c_uint32]
        transform.restype = ctypes.c_int32
        set_front = services.SetFrontProcess
        set_front.argtypes = [ctypes.POINTER(ProcessSerialNumber)]
        set_front.restype = ctypes.c_int32
    except AttributeError as exc:
        return MacOSActivationResult(True, False, False, f"application_services_symbol_missing:{exc}")

    transform_status = int(transform(ctypes.byref(psn), k_process_transform_to_foreground_application))
    front_status = int(set_front(ctypes.byref(psn)))
    if front_status == 0:
        return MacOSActivationResult(True, True, True, "activated_application_services")
    return MacOSActivationResult(
        True,
        True,
        False,
        f"application_services_rejected:transform={transform_status};front={front_status}",
    )
