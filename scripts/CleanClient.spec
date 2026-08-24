# -*- mode: python ; coding: utf-8 -*-
"""Lean PyInstaller spec for clean_client.

Avoids --collect-all PySide6 (pulls WebEngine/3D/etc.) and excludes the host
environment's ML stack (torch/transformers/sklearn/...) which previously
ballooned the bundle to ~1.6GB and made builds take forever.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_all, collect_data_files

SPECDIR = Path(SPEC).resolve().parent  # noqa: F821 — provided by PyInstaller
ROOT = SPECDIR.parent
ENTRY = ROOT / "clean_client" / "app.py"
CONFIG_JSON = ROOT / "clean_client" / "config" / "default.json"
PROFILE_JSON = ROOT / "clean_client" / "profiles" / "unholy_default.json"
ICON_ICO = ROOT / "clean_client" / "assets" / "cleanclient.ico"
ICON_PNG = ROOT / "clean_client" / "assets" / "cleanclient_icon.png"

# Host ML / web / notebook stack — never needed by CleanClient.
EXCLUDE_MODULES = [
    "torch",
    "torchvision",
    "torchaudio",
    "functorch",
    "transformers",
    "tensorflow",
    "keras",
    "sklearn",
    "scikit-learn",
    "scipy",
    "pandas",
    "matplotlib",
    "sympy",
    "networkx",
    "onnxruntime",
    "onnx",
    "fastapi",
    "starlette",
    "uvicorn",
    "aiohttp",
    "grpc",
    "grpcio",
    "nltk",
    "yt_dlp",
    "IPython",
    "notebook",
    "jupyter",
    "pytest",
    "_pytest",
    "langsmith",
    "openai",
    "tiktoken",
    "tokenizers",
    "huggingface_hub",
    "safetensors",
    "rich",
    "cv2.gapi",
    # Heavy Qt modules we do not use
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineProcess",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtGraphs",
    "PySide6.QtGraphsWidgets",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtQuick3D",
    "PySide6.QtDesigner",
    "PySide6.QtTest",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtSensors",
    "PySide6.QtSerialBus",
    "PySide6.QtSerialPort",
    "PySide6.QtPositioning",
    "PySide6.QtLocation",
    "PySide6.QtVirtualKeyboard",
    "PySide6.QtWebView",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtTextToSpeech",
    "PySide6.QtHttpServer",
    "PySide6.QtScxml",
]

# Drop matching binaries/datas copied by collect_all(PySide6).
# Use path-ish markers so we do NOT kill numpy.libs/libscipy_openblas*.dll
# (that filename contains the substring "scipy" but is required by numpy).
DROP_NAME_PARTS = (
    "Qt6WebEngine",
    "QtWebEngine",
    "Qt63D",
    "/Qt3D",
    "\\Qt3D",
    "Qt6Charts",
    "Qt6DataVisualization",
    "Qt6Graphs",
    "Qt6Pdf",
    "Qt6Quick3D",
    "Qt6Designer",
    "Qt6Test",
    "Qt6Bluetooth",
    "Qt6Nfc",
    "Qt6Sensors",
    "Qt6Serial",
    "Qt6Positioning",
    "Qt6Location",
    "Qt6VirtualKeyboard",
    "Qt6WebView",
    "Qt6WebChannel",
    "Qt6WebSockets",
    "Qt6RemoteObjects",
    "Qt6TextToSpeech",
    "Qt6HttpServer",
    "Qt6Scxml",
    "assistant.exe",
    "designer.exe",
    "linguist.exe",
    "balsam.exe",
    "balsamui.exe",
    "qmlcachegen.exe",
    "qmllint.exe",
    "qmlls.exe",
)

DROP_PATH_SEGMENTS = (
    "/torch/",
    "\\torch\\",
    "/scipy/",
    "\\scipy\\",
    "/sklearn/",
    "\\sklearn\\",
    "/transformers/",
    "\\transformers\\",
    "/onnxruntime/",
    "\\onnxruntime\\",
    "/pandas/",
    "\\pandas\\",
    "/fastapi",
    "\\fastapi",
    "torch-",
    "scipy-",
    "scikit_learn",
    "transformers-",
    "onnxruntime-",
    "pandas-",
)


def _keep_artifact(item) -> bool:
    """PyInstaller artifact tuples are (dest_name, src_path, typecode)."""
    name = str(item[0]) if item else ""
    src = str(item[1]) if item and len(item) > 1 else ""
    blob = f"{name}|{src}"
    blob_l = blob.lower()
    if any(part.lower() in blob_l for part in DROP_NAME_PARTS):
        return False
    # Keep numpy.libs/*openblas* even though the filename mentions scipy.
    if "numpy.libs" in blob_l and "openblas" in blob_l:
        return True
    if any(seg.lower() in blob_l for seg in DROP_PATH_SEGMENTS):
        return False
    return True


datas = [
    (str(CONFIG_JSON), "clean_client/config"),
    (str(PROFILE_JSON), "clean_client/profiles"),
]
if ICON_ICO.exists():
    datas.append((str(ICON_ICO), "clean_client/assets"))
if ICON_PNG.exists():
    datas.append((str(ICON_PNG), "clean_client/assets"))
binaries: list = []
hiddenimports = [
    "clean_client",
    "clean_client.app",
    "clean_client.paths",
    "clean_client.ui.main_window",
    "clean_client.ui.calibrator",
    "clean_client.ui.theme",
    "clean_client.ui.pages.control_page",
    "clean_client.ui.pages.rotation_page",
    "clean_client.ui.pages.vision_page",
    "clean_client.ui.pages.settings_page",
    "clean_client.capture.backends",
    "clean_client.capture.mss_backend",
    "clean_client.capture.dxcam_backend",
    "clean_client.capture.printwindow_backend",
    "clean_client.capture.window",
    "clean_client.vision.protocol",
    "clean_client.vision.mock",
    "clean_client.vision.factory",
    "clean_client.engine.loop",
    "clean_client.engine.bootstrap",
    "clean_client.config.loader",
    "clean_client.rotation.profile",
    "clean_client.rotation.selector",
    "clean_client.input.sendinput",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtNetwork",
    "PySide6.QtSvg",
    "shiboken6",
    "qfluentwidgets",
]

# Collect Qt / Fluent resources, then strip unused heavy bits.
for pkg in ("PySide6", "shiboken6", "qfluentwidgets"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += [x for x in pkg_datas if _keep_artifact(x)]
    binaries += [x for x in pkg_binaries if _keep_artifact(x)]
    hiddenimports += [
        h
        for h in pkg_hidden
        if not any(h == e or h.startswith(e + ".") for e in EXCLUDE_MODULES)
    ]

# Ensure Fluent icon / qss resources are present even if collect_all misses them.
datas += collect_data_files("qfluentwidgets")

a = Analysis(
    [str(ENTRY)],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDE_MODULES,
    noarchive=False,
    optimize=0,
)

# Second-pass filter in case Analysis still resolved something heavy.
a.binaries = [x for x in a.binaries if _keep_artifact(x)]
a.datas = [x for x in a.datas if _keep_artifact(x)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CleanClient",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX slows builds and often triggers AV false positives
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_ICO) if ICON_ICO.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="CleanClient",
)
