"""Loads the real QML UI offscreen and checks it is clean and wired.

QML mistakes (a bad id, a missing property, a binding to something renamed)
only show up at runtime as warnings, so this test fails on any QML warning,
then drives the privacy-mode dialog and the interrupt controls.
"""
import os
from typing import Any

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")
from PySide6.QtCore import QMetaObject, QObject, Qt, QtMsgType, qInstallMessageHandler  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


class FakeStore:
    def read(self, key: str) -> Any:
        return {"name": "Ada Lovelace", "purpose": "testing"} if key == "user_profile" else None

    def list_all(self) -> list[Any]:
        return []


@pytest.fixture(scope="module")
def ui() -> Any:
    app = QApplication.instance() or QApplication([])
    messages: list[str] = []

    def handler(mode: QtMsgType, context: Any, message: str) -> None:
        if mode in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            messages.append(message)

    previous = qInstallMessageHandler(handler)
    from rei.capabilities.builtin import register_builtin
    from rei.capabilities.registry import CapabilityRegistry
    from rei.ui.app import ReiUI

    registry = CapabilityRegistry()
    register_builtin(registry)
    rei_ui = ReiUI()
    rei_ui.set_context(  # type: ignore[no-untyped-call]
        FakeStore(), registry, {"defaults": {"privacy_mode": "local_only"}}, connectors=None
    )
    QTest.qWait(300)
    yield rei_ui, messages, app
    qInstallMessageHandler(previous)


def _root(rei_ui: Any) -> Any:
    # Keep the root wrapper alive: shiboken invalidates child wrappers found
    # through findChild() once their parent's Python wrapper is collected.
    root = getattr(rei_ui, "_test_root", None)
    if root is None:
        roots = rei_ui.engine.rootObjects()
        assert roots, "Main.qml failed to load"
        root = rei_ui._test_root = roots[0]
    return root


def _find(rei_ui: Any, name: str) -> Any:
    root = _root(rei_ui)
    obj: Any = root.findChild(QObject, name)
    if obj is None:
        # Page content is created by Loaders: walk the visual item tree instead,
        # keeping every wrapper visited alive (see _root)
        seen: list[Any] = getattr(rei_ui, "_test_items", [])
        rei_ui._test_items = seen
        stack = [root.contentItem()]
        while stack and obj is None:
            item = stack.pop()
            seen.append(item)
            if item.objectName() == name:
                obj = item
            stack.extend(item.childItems())
    assert obj is not None, f"{name} not found in the QML tree"
    return obj


def _qml_warnings(messages: list[str]) -> list[str]:
    # Only QML problems; ignore platform-plugin chatter from the offscreen backend
    return [m for m in messages if ".qml" in m or "qrc:" in m or "ReferenceError" in m or "TypeError" in m]


def test_main_qml_loads_without_warnings(ui: Any) -> None:
    rei_ui, messages, _ = ui
    _root(rei_ui)
    # Visit every page so lazily-evaluated bindings run too
    root = _root(rei_ui)
    for index in range(6):
        root.setProperty("currentPage", index)
        QTest.qWait(60)
    root.setProperty("currentPage", 0)
    # Now playing, onboarding and the minimum window width exercise the rest
    rei_ui.backend.set_now_playing("A fairly long song title for eliding", False, "youtube")
    rei_ui.backend.needsSetup = True
    root.setProperty("width", 880)
    for state in ("listening", "processing", "speaking", "idle"):
        rei_ui.set_state(state)
        QTest.qWait(60)
    rei_ui.backend.set_now_playing("", False, "")
    rei_ui.backend.needsSetup = False
    root.setProperty("width", 1180)
    QTest.qWait(60)
    assert _qml_warnings(messages) == []


def test_privacy_dialog_needs_confirmation(ui: Any) -> None:
    rei_ui, messages, _ = ui
    backend = rei_ui.backend
    applied: list[str] = []
    backend.privacyModeSelected.connect(applied.append)
    dialog = _find(rei_ui, "privacyModeDialog")

    # Requesting a mode opens the dialog with it preselected, but changes nothing
    backend.requestPrivacyMode("Cloud Assisted")
    QTest.qWait(250)
    assert dialog.property("visible") is True
    assert dialog.property("selectedIndex") == 2
    assert backend.privacyModeText == "Local Only"

    # Cancel closes it and still changes nothing
    QMetaObject.invokeMethod(dialog, "cancel")
    QTest.qWait(250)
    assert dialog.property("visible") is False
    assert applied == []
    assert backend.privacyModeText == "Local Only"

    # Only confirming applies the mode
    backend.requestPrivacyMode("Local + Connectors")
    QTest.qWait(250)
    QMetaObject.invokeMethod(dialog, "confirm")
    QTest.qWait(250)
    assert applied == ["Local + Connectors"]
    assert dialog.property("visible") is False

    # Opening on the current mode: confirming without a change applies nothing
    backend.requestPrivacyMode("")
    QTest.qWait(250)
    assert dialog.property("selectedIndex") == 0
    QMetaObject.invokeMethod(dialog, "confirm")
    QTest.qWait(250)
    assert applied == ["Local + Connectors"]
    assert _qml_warnings(messages) == []


def test_stop_button_follows_state(ui: Any) -> None:
    rei_ui, messages, _ = ui
    backend = rei_ui.backend
    stop = _find(rei_ui, "stopButton")

    rei_ui.set_state("idle")
    QTest.qWait(200)
    assert stop.property("enabled") is False

    for state in ("processing", "speaking"):
        rei_ui.set_state(state)
        QTest.qWait(200)
        assert stop.property("enabled") is True, state
        assert stop.property("opacity") == pytest.approx(1.0)

    interrupts: list[bool] = []
    backend.interruptRequested.connect(lambda: interrupts.append(True))
    QMetaObject.invokeMethod(stop, "clicked")
    QTest.qWait(50)
    assert interrupts == [True]

    rei_ui.set_state("listening")
    QTest.qWait(200)
    assert stop.property("enabled") is False
    assert _qml_warnings(messages) == []


def test_escape_interrupts_only_without_a_dialog(ui: Any) -> None:
    rei_ui, _, _ = ui
    backend = rei_ui.backend
    window = _root(rei_ui)
    window.requestActivate()
    QTest.qWait(100)
    if not window.isActive():
        pytest.skip("offscreen platform cannot activate windows for shortcuts")

    interrupts: list[bool] = []
    backend.interruptRequested.connect(lambda: interrupts.append(True))

    rei_ui.set_state("speaking")
    QTest.qWait(100)
    QTest.keyClick(window, Qt.Key.Key_Escape)
    QTest.qWait(50)
    assert interrupts == [True]

    # With the privacy dialog open, Esc closes the dialog instead
    dialog = _find(rei_ui, "privacyModeDialog")
    backend.requestPrivacyMode("Cloud Assisted")
    QTest.qWait(250)
    QTest.keyClick(window, Qt.Key.Key_Escape)
    QTest.qWait(250)
    assert interrupts == [True]
    assert dialog.property("visible") is False
    rei_ui.set_state("idle")
