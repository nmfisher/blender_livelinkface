bl_info = { 
"author":"Nick Fisher <nick.fisher@avinium.com>",
"name":"LiveLinkFace Add-On",
"blender":(3,1,0),
"category":"3D View",
"location": "View3D > Sidebar > LiveLinkFace"
}

import bpy

from livelinkface.operators import LiveLinkFacePanel, ConnectOperator, LoadCSVOperator

classes = [ LiveLinkFacePanel, ConnectOperator, LoadCSVOperator ]
        
def register():
    bpy.types.Scene.ll_is_listening = bpy.props.BoolProperty(name="Server listening", description="Whether the server is currently listening", default=False)
    bpy.types.Scene.ll_host_ip = bpy.props.StringProperty(name="Host IP", description="IP address of the interface on this machine to listen", default="0.0.0.0")
    bpy.types.Scene.ll_host_port = bpy.props.IntProperty(name="Port", description="Port", default=11111)
    bpy.types.Scene.ll_target = bpy.props.PointerProperty(
        type = bpy.types.Object,
        name = "Target object to attach the LiveLink stream to",
    )

    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
        
if __name__ == "main":
    register()        