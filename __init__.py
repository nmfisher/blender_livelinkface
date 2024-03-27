bl_info = { 
"author":"Nick Fisher <nick.fisher@avinium.com>",
"name":"LiveLinkFace Add-On",
"blender":(3,1,0),
"category":"3D View",
"location": "View3D > Sidebar > LiveLinkFace"
}

import bpy
from bpy_utils import register_custom_list_operator
from livelinkface.operators import LiveLinkFacePanel, ConnectOperator, LoadCSVOperator

def register():
    register_custom_list_operators("ll", "ll_targets", "ll_index")
    bpy.utils.register_class(LiveLinkFacePanel)
    bpy.utils.register_class(ConnectOperator)
    bpy.utils.register_class(LoadCSVOperator)

    bpy.types.Scene.ll_is_listening = bpy.props.BoolProperty(name="Server listening", description="Whether the server is currently listening", default=False)
    bpy.types.Scene.ll_host_ip = bpy.props.StringProperty(name="Host IP", description="IP address of the interface on this machine to listen", default="0.0.0.0")
    bpy.types.Scene.ll_host_port = bpy.props.IntProperty(name="Port", description="Port", default=11111)

    bpy.types.Scene.ll_record_stream = bpy.props.BoolProperty(
        name="Record",
        description="When true, blendshapes will be saved as successive frames in the action",
        default = False
    )

    bpy.types.Scene.invert_lr_mouth = bpy.props.BoolProperty(
        name="Invert Mouth L/R",
        description="Invert MouthLeft-MouthRight blendshapes",
        default = False)

def unregister():
    bpy.utils.unregister_class(LiveLinkFacePanel)
    bpy.utils.unregister_class(ConnectOperator)
    bpy.utils.unregister_class(LoadCSVOperator)
    unregister_custom_list_operators("ll","ll_targets", "ll_index")
    del bpy.types.Scene.ll_is_listening
    del bpy.types.Scene.ll_host_ip
    del bpy.types.Scene.ll_host_port
    del bpy.types.Scene.lL_record_stream
    del bpy.types.Scene.invert_lr_mouth
 
if __name__ == "main":
    register()        
