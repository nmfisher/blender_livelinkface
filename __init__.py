import sys

sys.dont_write_bytecode = True

bl_info = { 
"author":"Nick Fisher <nick.fisher@avinium.com>",
"name":"LiveLinkFace Add-On",
"blender":(3,1,0),
"category":"3D View",
"location": "View3D > Sidebar > LiveLinkFace"
}

import bpy

from livelinkface.operators import LiveLinkFacePanel, ConnectOperator, LoadCSVOperator, CUSTOM_OT_actions, CUSTOM_OT_addViewportSelection, CUSTOM_OT_printItems, CUSTOM_OT_clearList, CUSTOM_OT_removeDuplicates, CUSTOM_OT_selectItems, CUSTOM_OT_deleteObject, CUSTOM_UL_items

class ObjectSlot(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(name="Object",type=bpy.types.Object)


classes = (
    LiveLinkFacePanel, 
    ConnectOperator, 
    LoadCSVOperator, 
    ObjectSlot,
    CUSTOM_OT_actions,
    CUSTOM_OT_addViewportSelection,
    CUSTOM_OT_printItems,
    CUSTOM_OT_clearList,
    CUSTOM_OT_removeDuplicates,
    CUSTOM_OT_selectItems,
    CUSTOM_OT_deleteObject,
    CUSTOM_UL_items,
    
)


        
def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.ll_is_listening = bpy.props.BoolProperty(name="Server listening", description="Whether the server is currently listening", default=False)
    bpy.types.Scene.ll_host_ip = bpy.props.StringProperty(name="Host IP", description="IP address of the interface on this machine to listen", default="0.0.0.0")
    bpy.types.Scene.ll_host_port = bpy.props.IntProperty(name="Port", description="Port", default=11111)
    bpy.types.Scene.ll_targets = bpy.props.CollectionProperty(
        type = ObjectSlot,
        name = "Target object(s) to attach the LiveLink stream to",
    )
    bpy.types.Scene.ll_targets_index = bpy.props.IntProperty()




def unregister():
    for c in classes:
        try:
            bpy.utils.unregister_class(c)
        except (RuntimeError, ValueError):
            pass  # Ignore unregistering errors for classes that weren't registered
    if hasattr(bpy.types.Scene, 'll_targets'):
        del bpy.types.Scene.ll_targets
    if hasattr(bpy.types.Scene, 'll_targets_index'):
        del bpy.types.Scene.ll_targets_index
        
if __name__ == "__main__":
    unregister()
    register()        