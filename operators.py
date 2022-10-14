import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator, StringProperty

import livelinkface.bpylivelinkface as llf

class LoadCSVOperator(Operator, ImportHelper):
    bl_idname = "scene.load_csv_operator"
    bl_label = "Load from CSV"
        
    filter_glob: bpy.props.StringProperty(options={'HIDDEN'}, default='*.csv',maxlen=255)

    def execute(self, context):
        bpy.ops.buttons.file_browse()
        return {'FINISHED'}
        
class ConnectOperator(bpy.types.Operator):
    bl_idname = "scene.connect_operator"
    bl_label = "connectbutton"

    def execute(self, context):
        if context.scene.ll_is_listening:
            llf.instance.close()
            llf.instance = None
            context.scene.ll_is_listening = False
            self.report({"INFO"}, "Disconnected")
            return {'FINISHED'}
        else:
            if context.scene.ll_target is None:
                self.report({"ERROR"}, "No target object selected")
            elif context.scene.ll_host_ip is None or len(context.scene.ll_host_ip) == 0:
                self.report({"ERROR"}, "No IP address set")
            elif context.scene.ll_host_port is None:
                self.report({"ERROR"}, "No port set")
            else:
                try:
                    llf.create_instance(context.scene.ll_target, context.scene.ll_host_ip, context.scene.ll_host_port)
                    context.scene.ll_is_listening = True
                    self.report({"INFO"}, "Started")
                except Exception as e:
                    context.scene.ll_is_listening = False
                    self.report({"ERROR"}, f"Error connecting : {e}")
                return {'FINISHED'}
            return {"CANCELLED"}

class LiveLinkFacePanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_live_link_face"
    bl_label = "LiveLinkFace"
    bl_category = "LiveLinkFace"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HEADER_LAYOUT_EXPAND"}

    def draw(self, context):
        box = self.layout.box()
        box.label(text="Stream")
        row = box.row()
        row.prop(context.scene, "ll_host_ip") 
        row.prop(context.scene, "ll_host_port")
        box.prop(context.scene, "ll_target", text = "Target")
        box.operator("scene.connect_operator", text="Disconnect" if context.scene.ll_is_listening else "Connect")
        box = self.layout.box()
        load_csv = box.operator("scene.load_csv_operator")
        

