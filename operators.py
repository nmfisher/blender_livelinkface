import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator, StringProperty

from livelinkface.bpylivelinkface import create_instance

class LoadCSVOperator(Operator, ImportHelper):
    bl_idname = "scene.load_csv_operator"
    bl_label = "Load from CSV"
        
    filter_glob: bpy.props.StringProperty(options={'HIDDEN'}, default='*.csv',maxlen=255)

    id : bpy.props.IntProperty()

    def execute(self, context):
        bpy.ops.buttons.file_browse()
        return {'FINISHED'}
        
class ConnectOperator(bpy.types.Operator):
    bl_idname = "scene.connect_operator"
    bl_label = "Connect"

    id : bpy.props.IntProperty()

    def execute(self, context):
        if context.scene.ll_target is None:
            self.report({"ERROR"}, "No target object selected")
        elif context.scene.ll_host_ip is None or len(context.scene.ll_host_ip) == 0:
            self.report({"ERROR"}, "No IP address set")
        elif context.scene.ll_host_port is None:
            self.report({"ERROR"}, "No port set")
        else:
            self.instance = create_instance(context.scene.ll_target, context.scene.ll_host_ip, context.scene.ll_host_port)
            self.report({"ERROR"}, "starting")
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
        #load_csv = self.layout.operator("scene.load_csv_operator")
        row = self.layout.row()
        row.prop(context.scene, "ll_host_ip") 
        row.prop(context.scene, "ll_host_port")
        self.layout.prop(context.scene, "ll_target", text = "Target")
        self.layout.operator("scene.connect_operator")
        

