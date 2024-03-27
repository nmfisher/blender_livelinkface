import bpy
from bpy_extras.io_utils import ImportHelper

from bpy.props import (IntProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       PointerProperty)

from bpy_utils.operators import (CUSTOM_OT_actions)
from bpy.types import (Operator,
                       Panel,
                       PropertyGroup,
                       UIList)

import livelinkface.bpylivelinkface as llf

def checkPrereqs(context):
    if len(context.scene.ll_targets) == 0:
        self.report({"ERROR"}, "No target object selected")
    elif context.scene.ll_host_ip is None or len(context.scene.ll_host_ip) == 0:
        self.report({"ERROR"}, "No IP address set")
    elif context.scene.ll_host_port is None:
        self.report({"ERROR"}, "No port set")
    else:
        return True
    return False

class LoadCSVOperator(Operator, ImportHelper):
    bl_idname = "scene.load_csv_operator"
    bl_label = "Load from CSV"
        
    filename_ext = ".csv"
    filter_glob: bpy.props.StringProperty(options={'HIDDEN'}, default='*.csv',maxlen=255)

    def execute(self, context):
        if checkPrereqs(context):
            #try:
            llf.LiveLinkTarget.from_csv([t.obj for t in context.scene.ll_targets], self.filepath)
            self.report({"INFO"}, "Loaded")
            return {'FINISHED'}
            #except Exception as e:
            #    print(e)
            #    self.report({"ERROR"}, f"Error loading from CSV : {self.filepath}")
        return {'CANCELLED'}
        
class ConnectOperator(bpy.types.Operator):
    bl_idname = "scene.connect_operator"
    bl_label = "connectbutton"

    def execute(self, context):
        if llf.instance is not None and llf.instance.isListening():
            try:
                llf.instance.close()
                llf.instance = None
            except:
                pass
            context.scene.ll_is_listening = False
            self.report({"INFO"}, "Disconnected")
            return {'FINISHED'}
        else:
            if checkPrereqs(context):
                try:
                    llf.create_instance([t.obj for t in context.scene.ll_targets], context.scene.ll_record_stream, context.scene.ll_host_ip, context.scene.ll_host_port)
                    llf.instance.listen()
                    self.report({"INFO"}, "Started")
                except Exception as e:
                    llf.instance.stopListening()
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

    invert_lr_mouth : BoolProperty(
        name="Invert Mouth L/R",
        description="Invert MouthLeft-MouthRight blendshapes",
        default = False
        )

    def draw(self, context):
        box = self.layout.box()
        box.label(text="Target")
                
        rows = 2
        row = box.row()
        row.template_list("CUSTOM_UL_items", "", bpy.context.scene, "ll_targets", bpy.context.scene, "ll_index", rows=rows)
        col = row.column(align=True)
        col.operator("ll_custom.list_action", icon='ADD', text="").action = 'ADD'
        col.operator("ll_custom.list_action", icon='REMOVE', text="").action = 'REMOVE'
        
        box = self.layout.box()
        box.label(text="Stream")
        row = box.row()
        row.prop(context.scene, "ll_host_ip") 
        row.prop(context.scene, "ll_host_port")      
        row = box.row()

        row.prop(context.scene, "ll_record_stream", text="Record?")
        row.operator("scene.connect_operator", text="Disconnect" if llf.instance is not None and llf.instance.isListening() else "Connect")

        box = self.layout.box()
        box.label(text="Import")
        load_csv = box.operator("scene.load_csv_operator")
        
        box = self.layout.box()
        box.label(text="Adjustments")
        row = box.row()
        box.prop(context.scene, "invert_lr_mouth", text="Invert Mouth L/R")

