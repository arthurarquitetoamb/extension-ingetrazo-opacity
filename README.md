# Material Opacity for IngeTrazo

A Python extension for [IngeTrazo](https://ingetrazo.com/) that lets you assign **opacity** and **transparency** to an **existing named material** in the current document.

<img width="519" height="400" alt="opacity" src="https://github.com/user-attachments/assets/a1234949-a8f8-4686-9af8-d18c8591b98f" />

The plugin adds a **Material Opacity** panel/action so you can select a material already used in the model and apply an opacity value. The change is applied to the material and restamped onto every face and painted group that uses it, as a single undoable step.

## Important prerequisite (required workflow)

Before opening the plugin window, make sure the material you want to edit is a **named material** in the model:

1. In IngeTrazo, open the material/texture editing UI.
2. Go to **Edit Texture > (Name the material)**.
3. Click **Apply**.

Only after the material has been named and applied can the plugin reliably find and target it in the **Material Opacity** window.

> **Why this matters:** the plugin operates on materials identified by a name/tag in the document. If a paint/color has no material name yet, it will not appear as a selectable named material in the plugin.

## Features

- **Material selection:** choose from named materials found in the current IngeTrazo document
- **Opacity control:** set opacity from `0%` to `100%` using a slider or numeric input
- **Transparency display:** shows transparency automatically (`Transparency = 100% - Opacity`)
- **Document-wide update:** updates the selected material and restamps all faces/groups that use it
- **Undo/redo support:** applies changes as a single undoable operation
- **Per-document refresh:** refreshes the material list when the document changes (and includes a manual **Refresh** button)

## Requirements

- IngeTrazo with Python extension support (Extension API with `setup(app)`)
- A document containing at least one **named** material (see prerequisite above)

## Installation

1. Download or copy `material_opacity.py` from this repository/folder.
2. Place it in your IngeTrazo **user plugins** folder:
   - **Windows:** `%APPDATA%\ingetrazo\plugins\`
   - **Linux:** `$XDG_DATA_HOME/ingetrazo/plugins` (usually `~/.local/share/ingetrazo/plugins`)
   - **macOS:** use the user plugins directory for your IngeTrazo installation
3. Restart IngeTrazo (plugins are discovered at startup).

## Usage

1. Open your model in IngeTrazo.
2. Ensure the target material is named and applied:
   - **Edit Texture > (Name the material) > Apply**
3. Open **Extensions ▸ Material Opacity…** (or the **Material Opacity** panel).
4. Select the desired material from the **Material** dropdown.
5. Adjust **Opacity** (`100%` = opaque, `0%` = fully transparent).
6. Click **Apply**.

If the material does not appear immediately, click **Refresh** after naming/applying it in the model.

## How it works

- The plugin reads named materials from the active document (including named materials used in the model).
- When you click **Apply**, it creates an updated material definition with the chosen opacity while preserving the material’s existing properties (such as color, texture, and finish, when available).
- It applies the change using IngeTrazo’s material restamp/history mechanism so all instances of that named material are updated consistently in one undoable step.

## Notes and limitations

- **Named materials only:** this plugin targets materials by name/tag. Unnamed paints/colors are not selectable until they are named and applied.
- **Material must exist in the model/document context:** if a material was removed or renamed, use **Refresh** to reload the list.
- **No material creation flow:** this plugin edits opacity/transparency of existing named materials; it does not replace IngeTrazo’s material creation/naming UI.

## Troubleshooting

- **Material not listed:** confirm you completed **Edit Texture > (Name the material) > Apply**, then click **Refresh** in the plugin panel.
- **Panel/menu not visible:** verify `material_opacity.py` is in the correct user plugins folder and restart IngeTrazo.
- **No effect after Apply:** make sure the selected item is the correct named material used by the faces/groups you expect.

## License

 GPL-3.0.
