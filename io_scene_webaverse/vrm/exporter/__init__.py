from typing import Set, cast

import bpy
from bpy_extras.io_utils import ExportHelper

from ..editor import validation
from ..preferences import get_preferences, use_legacy_importer_exporter
from .glb_obj import GlbObj


def export_vrm_update_addon_preferences(
    export_op: bpy.types.Operator, context: bpy.types.Context
) -> None:
    preferences = get_preferences(context)
    if not preferences:
        return
    if bool(preferences.export_invisibles) != bool(export_op.export_invisibles):
        preferences.export_invisibles = export_op.export_invisibles
    if bool(preferences.export_only_selections) != bool(
        export_op.export_only_selections
    ):
        preferences.export_only_selections = export_op.export_only_selections


class ExportVRM(bpy.types.Operator, ExportHelper):  # type: ignore[misc]
    bl_idname = "export_scene.vrm"
    bl_label = "Export VRM"
    bl_description = "Export VRM"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrm", options={"HIDDEN"}  # noqa: F722,F821
    )

    # vrm_version : bpy.props.EnumProperty(name="VRM version" ,items=(("0.0","0.0",""),("1.0","1.0","")))
    export_invisibles: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export invisible objects",  # noqa: F722
        update=export_vrm_update_addon_preferences,
    )
    export_only_selections: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export only selections",  # noqa: F722
        update=export_vrm_update_addon_preferences,
    )

    errors: bpy.props.CollectionProperty(type=validation.VrmValidationError)  # type: ignore[valid-type]

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.filepath:
            return {"CANCELLED"}
        filepath: str = self.filepath

        try:
            glb_obj = GlbObj(
                bool(self.export_invisibles), bool(self.export_only_selections)
            )
        except GlbObj.ValidationError:
            return {"CANCELLED"}
        # vrm_bin =  glb_obj().convert_bpy2glb(self.vrm_version)
        vrm_bin = glb_obj.convert_bpy2glb("0.0")
        if vrm_bin is None:
            return {"CANCELLED"}
        with open(filepath, "wb") as f:
            f.write(vrm_bin)
            
        print("got req 1 " + str(len(vrm_bin)))
        # import requests
        # r = requests.post("https://ipfs.exokit.org/", data = vrm_bin)
        # print(r.json())
        
        # print_console('ERROR', str(file.name));
        with open(filepath, 'rb') as f:
            data = f.read()
            print("got req 2 " + str(len(data)))
            # print_console('ERROR', str(data));
            r = requests.post('https://ipfs.exokit.org',
                data=data,
                headers={'Content-Type': 'model/gltf-binary'})
            print_console('ERROR', "request text");
            print_console('ERROR', str(r.text));
            resJson = r.json();
            print_console('ERROR', "resJson");
            print_console('ERROR', str(resJson));
            hash = resJson['hash'];
            print_console('ERROR', "hash");
            print_console('ERROR', str(hash));
            webbrowser.open('https://app.webaverse.com/preview.html?hash=' + hash + '&ext=vrm', new=2)

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        preferences = get_preferences(context)
        if preferences:
            self.export_invisibles = bool(preferences.export_invisibles)
            self.export_only_selections = bool(preferences.export_only_selections)
        if not use_legacy_importer_exporter() and "gltf" not in dir(
            bpy.ops.export_scene
        ):
            return cast(
                Set[str],
                bpy.ops.wm.gltf2_addon_disabled_warning(
                    "INVOKE_DEFAULT",
                ),
            )
        return cast(Set[str], ExportHelper.invoke(self, context, event))

    def draw(self, context: bpy.types.Context) -> None:
        pass  # Is needed to get panels available


class VRM_IMPORTER_PT_export_error_messages(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            str(context.space_data.active_operator.bl_idname) == "EXPORT_SCENE_OT_vrm"
        )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        operator = context.space_data.active_operator

        layout.prop(operator, "export_invisibles")
        layout.prop(operator, "export_only_selections")

        validation.WM_OT_vrmValidator.detect_errors_and_warnings(
            context, operator.errors, False, layout
        )


def menu_export(export_op: bpy.types.Operator, context: bpy.types.Context) -> None:
    export_op.layout.operator(ExportVRM.bl_idname, text="Webaverse VRM (.vrm)")
