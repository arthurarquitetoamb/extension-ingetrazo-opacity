# SPDX-License-Identifier: GPL-3.0-or-later
"""Material Opacity — assign opacity and transparency to an existing material.

Adds a panel (Extensions ▸ Material Opacity…) that lets you pick any material
already registered in the open IngeTrazo document and set its opacity. The
change is applied to the material itself and restamped onto every face and
painted group that uses it, as a single undoable step.

Install: copy this file to %APPDATA%\\ingetrazo\\plugins\\ and restart IngeTrazo.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger("ingetrazo.plugins.material_opacity")


def _clamp_opacity(percent: int) -> int:
    return max(0, min(100, int(percent)))


class MaterialOpacityPanel(QWidget):
    """UI for choosing a material and applying an opacity value."""

    def __init__(self, app):
        super().__init__()
        self._app = app
        self._updating = False
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        intro = QLabel(
            "Set <b>opacity</b> and <b>transparency</b> for an existing material. "
            "The material and every face/group painted with it are updated together."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)

        self._material = QComboBox()
        self._material.setToolTip("Existing materials registered in the current document.")
        self._material.currentIndexChanged.connect(self._on_material_changed)
        form.addRow("Material:", self._material)

        slider_row = QWidget()
        slider_layout = QHBoxLayout(slider_row)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        slider_layout.setSpacing(6)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, 100)
        self._slider.setValue(100)
        self._slider.setToolTip("Opacity percentage (100 = opaque, 0 = fully transparent).")
        self._slider.valueChanged.connect(self._on_slider_changed)

        self._spin = QSpinBox()
        self._spin.setRange(0, 100)
        self._spin.setValue(100)
        self._spin.setSuffix(" %")
        self._spin.setToolTip("Opacity percentage.")
        self._spin.valueChanged.connect(self._on_spin_changed)

        slider_layout.addWidget(self._slider, 1)
        slider_layout.addWidget(self._spin)
        form.addRow("Opacity:", slider_row)

        self._transparency = QLabel("0 %")
        self._transparency.setToolTip("Transparency = 100% − opacity.")
        form.addRow("Transparency:", self._transparency)

        root.addLayout(form)

        actions = QHBoxLayout()
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setToolTip("Reload the list of materials from the document.")
        self._refresh_btn.clicked.connect(self.refresh)

        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setToolTip("Apply the selected opacity to the chosen material.")
        self._apply_btn.clicked.connect(self.apply_opacity)

        actions.addWidget(self._refresh_btn)
        actions.addStretch(1)
        actions.addWidget(self._apply_btn)
        root.addLayout(actions)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        root.addWidget(self._status)
        root.addStretch(1)

        self._update_transparency_label()

    # ---- UI state ---------------------------------------------------------

    def _set_controls_enabled(self, enabled: bool) -> None:
        self._material.setEnabled(enabled)
        self._slider.setEnabled(enabled)
        self._spin.setEnabled(enabled)
        self._apply_btn.setEnabled(enabled)

    def _update_transparency_label(self) -> None:
        opacity = _clamp_opacity(self._spin.value())
        self._transparency.setText(f"{100 - opacity} %")

    def _on_slider_changed(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            self._spin.setValue(_clamp_opacity(value))
            self._update_transparency_label()
        finally:
            self._updating = False

    def _on_spin_changed(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            value = _clamp_opacity(value)
            self._slider.setValue(value)
            self._update_transparency_label()
        finally:
            self._updating = False

    # ---- Document/materials -----------------------------------------------

    def _current_material_name(self) -> str | None:
        name = self._material.currentData()
        if isinstance(name, str) and name:
            return name
        text = self._material.currentText().strip()
        return text or None

    def _material_opacity_percent(self, mat) -> int:
        try:
            opacity = getattr(mat, "opacity", None)
            if opacity is None:
                return 100
            return _clamp_opacity(round(float(opacity) * 100))
        except Exception:
            return 100

    def _iter_used_named_materials(self):
        """Yield (name, attrs/material-dict) for materials used in the scene.

        Includes faces (loose and inside groups/components) and groups painted
        as a whole, so named materials remain discoverable even if they are not
        yet present in ``scene.materials``.
        """
        scene = self._app.scene
        try:
            from core.group import iter_placements
        except Exception:
            iter_placements = None

        def consider(attrs):
            if not isinstance(attrs, dict):
                return
            name = attrs.get("mat")
            if isinstance(name, str) and name:
                yield name, attrs

        # Loose faces
        try:
            for face in getattr(getattr(scene, "loose_mesh", None), "faces", []) or []:
                for item in consider(getattr(face, "attrs", None)):
                    yield item
        except Exception:
            pass

        # Faces inside groups/components (all placements, nested included)
        groups = getattr(scene, "groups", []) or []
        if callable(iter_placements):
            try:
                for top in groups:
                    for placement, _m in iter_placements(top):
                        mesh = getattr(placement, "mesh", None)
                        for face in getattr(mesh, "faces", []) or []:
                            for item in consider(getattr(face, "attrs", None)):
                                yield item
            except Exception:
                pass
        else:
            try:
                for group in groups:
                    for face in getattr(getattr(group, "mesh", None), "faces", []) or []:
                        for item in consider(getattr(face, "attrs", None)):
                            yield item
            except Exception:
                pass

        # Groups/components painted as a whole
        if callable(iter_placements):
            try:
                for top in groups:
                    for placement, _m in iter_placements(top):
                        for item in consider(getattr(placement, "material", None)):
                            yield item
            except Exception:
                pass
        else:
            try:
                for group in groups:
                    for item in consider(getattr(group, "material", None)):
                        yield item
            except Exception:
                pass

    def _collect_materials(self):
        """Return a dict name -> material-like object (Material or synthesized)."""
        from core.materials import Material

        try:
            registry = getattr(self._app.scene, "materials", {}) or {}
        except Exception:
            registry = {}

        out = {}
        # Registry entries first (authoritative)
        for name, mat in registry.items():
            if isinstance(name, str) and name:
                out[name] = mat

        # Add named materials found in actual usage (fallback synthesis)
        try:
            for name, attrs in self._iter_used_named_materials():
                if name in out:
                    continue
                color = attrs.get("color")
                texture = attrs.get("texture")
                opacity = attrs.get("opacity")
                try:
                    out[name] = Material(
                        name=name,
                        color=tuple(color) if color is not None else None,
                        texture=dict(texture) if isinstance(texture, dict) else None,
                        opacity=float(opacity) if opacity is not None else None,
                    )
                except Exception:
                    # Keep a minimal placeholder so it can still be selected/applied.
                    out[name] = Material(name=name)
        except Exception:
            log.exception("Failed to collect used materials")

        return out

    def _resolve_material(self, name: str):
        try:
            materials = self._collect_materials()
            return materials.get(name)
        except Exception:
            try:
                return (getattr(self._app.scene, "materials", {}) or {}).get(name)
            except Exception:
                return None

    def _on_material_changed(self, _index: int) -> None:
        name = self._current_material_name()
        if not name:
            return
        mat = self._resolve_material(name)
        if mat is None:
            return
        pct = self._material_opacity_percent(mat)
        self._updating = True
        try:
            self._slider.setValue(pct)
            self._spin.setValue(pct)
            self._update_transparency_label()
        finally:
            self._updating = False
        self._status.setText(f"Selected material: {name} (current opacity {pct}%).")

    def refresh(self) -> None:
        """Reload materials from the active document."""
        selected = self._current_material_name()
        try:
            materials = self._collect_materials()
            names = sorted(materials.keys(), key=lambda s: str(s).lower())
        except Exception:
            log.exception("Failed to read document materials")
            materials = {}
            names = []

        self._material.blockSignals(True)
        try:
            self._material.clear()
            if not names:
                self._material.addItem("No materials available", None)
            else:
                for name in names:
                    self._material.addItem(str(name), name)
                if selected and selected in names:
                    self._material.setCurrentIndex(names.index(selected))
        finally:
            self._material.blockSignals(False)

        has_materials = bool(names)
        self._set_controls_enabled(has_materials)
        if not has_materials:
            self._status.setText(
                "No named materials found. Use a material with a name/tag in the model "
                "(for example, a material applied with a name) and click Refresh."
            )
        else:
            self._on_material_changed(self._material.currentIndex())

    # ---- Apply ------------------------------------------------------------

    def apply_opacity(self) -> None:
        name = self._current_material_name()
        if not name:
            self._status.setText("Select a material to edit.")
            return

        percent = _clamp_opacity(self._spin.value())
        opacity = None if percent >= 100 else round(percent / 100.0, 4)

        try:
            scene = self._app.scene
            current = self._resolve_material(name)
            if current is None:
                self.refresh()
                self._status.setText(f"Material '{name}' is no longer available.")
                return

            from core.history import RestampMaterialCommand
            from core.materials import Material

            new_material = Material(
                name=name,
                color=getattr(current, "color", None),
                texture=getattr(current, "texture", None),
                opacity=opacity,
                finish=getattr(current, "finish", None),
            )

            vp = self._app.viewport
            vp.history.execute(RestampMaterialCommand(name, new_material))

            notify = getattr(vp, "notify_scene_changed", None)
            if callable(notify):
                notify()
            vp.update()

            self.refresh()
            self._status.setText(
                f"Applied {percent}% opacity ({100 - percent}% transparency) to '{name}'."
            )
        except Exception:
            log.exception("Failed to apply material opacity")
            self._status.setText("Could not apply opacity. Check the application log for details.")


def setup(app):
    panel_widget = MaterialOpacityPanel(app)
    dock = app.add_panel("Material Opacity", panel_widget, name="material_opacity")

    try:
        app.on_document_changed(panel_widget.refresh)
    except Exception:
        log.exception("Could not connect on_document_changed")

    def show():
        try:
            app.show_panel(dock)
        except Exception:
            try:
                dock.show()
                dock.raise_()
            except Exception:
                log.exception("Could not show Material Opacity panel")

    try:
        app.add_menu_action(
            "Material Opacity…",
            show,
            tip="Assign opacity and transparency to an existing material.",
        )
    except Exception:
        log.exception("Could not add menu action")

    log.info("Material Opacity extension loaded (key=%s)", getattr(app, "key", "?"))
