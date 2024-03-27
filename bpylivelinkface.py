import traceback
import time
import socket 
import bpy 
import csv
import random 

from livelinkface.pylivelinkface import PyLiveLinkFace, FaceBlendShape

LIVE_LINK_FACE_HEADER = "Timecode,BlendShapeCount,EyeBlinkLeft,EyeLookDownLeft,EyeLookInLeft,EyeLookOutLeft,EyeLookUpLeft,EyeSquintLeft,EyeWideLeft,EyeBlinkRight,EyeLookDownRight,EyeLookInRight,EyeLookOutRight,EyeLookUpRight,EyeSquintRight,EyeWideRight,JawForward,JawRight,JawLeft,JawOpen,MouthClose,MouthFunnel,MouthPucker,MouthRight,MouthLeft,MouthSmileLeft,MouthSmileRight,MouthFrownLeft,MouthFrownRight,MouthDimpleLeft,MouthDimpleRight,MouthStretchLeft,MouthStretchRight,MouthRollLower,MouthRollUpper,MouthShrugLower,MouthShrugUpper,MouthPressLeft,MouthPressRight,MouthLowerDownLeft,MouthLowerDownRight,MouthUpperUpLeft,MouthUpperUpRight,BrowDownLeft,BrowDownRight,BrowInnerUp,BrowOuterUpLeft,BrowOuterUpRight,CheekPuff,CheekSquintLeft,CheekSquintRight,NoseSneerLeft,NoseSneerRight,TongueOut,HeadYaw,HeadPitch,HeadRoll,LeftEyeYaw,LeftEyePitch,LeftEyeRoll,RightEyeYaw,RightEyePitch,RightEyeRoll".split(",")

instance = None

'''
Create a listener (an instance of LiveLinkFaceServer) on the given IP/port. 
Prefer using this method than constructing an instance directly as this will ensure that any pre-existing connections are closed
'''
def create_instance(targets, record=False, host= "0.0.0.0", port = 11111):
    global instance
    if instance is not None:
        instance.close()
    instance = LiveLinkFaceServer(targets, record, host, port)

'''
Interface for looking up shape key/custom properties by name and setting their respective weights on frames.
'''
class LiveLinkTarget:

    '''
    Construct an instance to manipulate frames on a single target object (which is an object within the Blender context).
    If the number of frames is known ahead of time (i.e. you are not working with streaming), this can be passed here.
    If you are streaming, pass num_frames=0 (or simply don't pass anything for the parameter and leave empty).
    The target should have at least one shape key or custom property with a name that corresponds to one of the entries in LIVE_LINK_FACE_HEADER.
    An exception will be raised if neither of these are present.
    '''
    def __init__(self, target, num_frames=360, action_name=None):
        
        self.target = target
        self.frame_nums = list(range(num_frames)) 

        # create an array-of-arrays to hold the (flattened) tuples of (frame_number,weight) for each shape key
        # i.e. each inner array will look like:
        # [ 0, v1, 1, v2, ..., N, vN ]
        # where v1 and v2 refer to the shape key weights at frames 0 and 1 respectively, and there are N frames in total
        # (note this will also create keyframes for non-LiveLinkFace shape keys on the mesh)
        # I can't find a better way to check if an object has shapekeys, so just use try-except
        try:
            self.sk_frame_data =  [ [ i for co in zip(self.frame_nums, [0.0] * num_frames) for i in co ] for _ in range(len(self.target.data.shape_keys.key_blocks)) ]
        except:
            self.sk_frames = None
        # some ARKit blendshapes may drive bone rotations, rather than mesh-deforming shape keys
        # if a custom property exists on the target object whose name matches the incoming ARkit shape, the property will be animated
        # it is then your responsibility to create a driver in Blender to rotate the bone between its extremities (blendshape values -1 to 1 )

        self.custom_props = [] 
        for i in range(len(LIVE_LINK_FACE_HEADER) - 2):
            custom_prop = self.livelink_to_custom_prop(i)
            if custom_prop is not None:
                self.custom_props += [custom_prop]
                print(f"Found custom property {custom_prop} for ARkit blendshape : {LIVE_LINK_FACE_HEADER[i+2]}")
                
        # if the user hasn't already explicitly created a custom property on the target for head rotation
        # we automatically create it here
        for k in ["HeadPitch","HeadRoll","HeadYaw"]:
            if k not in self.custom_props:
                self.target[k] = 0.0
                print(f"Created custom property {k} on target object")
                self.custom_props += [ k ] 
                
        print(f"Set custom_props to {self.custom_props}")
        self.custom_prop_framedata = [ [ i for co in zip(self.frame_nums, [0.0] * num_frames) for i in co ] for _ in range(len(self.custom_props)) ]
                
        if action_name is not None:
            self.create_action(action_name, num_frames)
        
        self.update_keyframes()

    '''
    Try and resolve an ARKit blendshape-id to a named shape key in the target object.
    ARKit blendshape IDs are the integer index within LIVE_LINK_FACE_HEADER (offset to exclude the first two columns.
    '''
    def livelink_to_shapekey_idx(self, ll_idx):
        name = LIVE_LINK_FACE_HEADER[ll_idx+2]

        # Invert Mouth Left and Rigth shapes to compensate for LiveLinkFace bug
        if bpy.context.scene.invert_lr_mouth:
            if name == 'MouthLeft':
                name = 'MouthRight'
            elif name == 'MouthRight':
                name = 'MouthLeft'

        for n in [name, name[0].lower() + name[1:]]:
            idx = self.target.data.shape_keys.key_blocks.find(n)
            if idx != -1:
                return idx
        return idx

    '''
    Try and resolve an ARKit blendshape-id to a custom property in the target object.
    ARKit blendshape IDs are the integer index within LIVE_LINK_FACE_HEADER (offset to exclude the first two columns.
    '''
    def livelink_to_custom_prop(self, ll_idx):
        name = LIVE_LINK_FACE_HEADER[ll_idx+2]

        # Invert Mouth Left and Rigth shapes to compensate for LiveLinkFace bug
        if bpy.context.scene.invert_lr_mouth:
            if name == 'MouthLeft':
                name = 'MouthRight'
            elif name == 'MouthRight':
                name = 'MouthLeft'
                
        for n in [name, name[0].lower() + name[1:]]:
            try:
                self.target[n]
                return n
            except:
                pass
        return None    
            
    '''Sets the value for the LiveLink blendshape at index [i_ll] to [val] for frame [frame] (note the underlying target may be a blendshape or a bone).'''
    def set_frame_value(self, i_ll, frame, val):
        i_sk = self.livelink_to_shapekey_idx(i_ll)
        frame_data_offset = (2*frame)+1 
        if i_sk != -1:
            self.sk_frame_data[i_sk][frame_data_offset] = val
        else:
            custom_prop = self.livelink_to_custom_prop(i_ll)
            if custom_prop is not None:
                custom_prop_idx = self.custom_props.index(custom_prop)
                self.custom_prop_framedata[custom_prop_idx][frame_data_offset] = val
            else:
#                print(f"Failed to find custom property for ARkit blendshape id {i_ll}")
                pass

    '''Loads a CSV in LiveLinkFace format. First line is the header (Timecode,BlendshapeCount,etc,etc), every line thereafter is a single frame with comma-separated weights'''
    @staticmethod
    def from_csv(targets,path,action_name="LiveLinkAction",use_first_frame_as_zero=False):        
        with open(path,"r") as csv_file:
            csvdata = list(csv.reader(csv_file))

        num_frames = len(csvdata) - 1

        targets = [LiveLinkTarget(target, num_frames, action_name=action_name) for target in targets]
        for idx,blendshape in enumerate(LIVE_LINK_FACE_HEADER):
            if idx < 2:
                continue
            
            rest_weight = float(csvdata[1][idx])
                        
            for i in range(1, num_frames):
                val = float(csvdata[i][idx])
                if use_first_frame_as_zero:
                    val -= rest_weight
                for target in targets:
                    ll_idx = idx - 2
                    frame=i-1
                    target.set_frame_value(ll_idx, i, val)

        for target in targets:
            target.update_keyframes()
        
        return targets
    
      
    def create_action(self, action_name, num_frames):
    
        # create a new Action so we can directly create fcurves and set the keyframe points
        try:
            self.sk_action = bpy.data.actions[f"{action_name}_shapekey"]
        except: 
            self.sk_action = bpy.data.actions.new(f"{action_name}_shapekey") 
                
        # create the bone AnimData if it doesn't exist 
        # important - we create this on the target (e.g. bpy.context.object), not its data (bpy.context.object.data)
        if self.target.animation_data is None:
            self.target.animation_data_create()
                                   
        # create the shape key AnimData if it doesn't exist 
        if self.target.data.shape_keys.animation_data is None:
            self.target.data.shape_keys.animation_data_create()
            
        self.target.data.shape_keys.animation_data.action = self.sk_action
        
        self.sk_fcurves = []
        self.custom_prop_fcurves = []
        
        for sk in self.target.data.shape_keys.key_blocks:
            datapath = f"{sk.path_from_id()}.value"
            
            fc = self.sk_action.fcurves.find(datapath)
            if fc is None:
                print(f"Creating fcurve for shape key {sk.path_from_id()}")
                fc = self.sk_action.fcurves.new(datapath)
                fc.extrapolation="CONSTANT"                
                fc.keyframe_points.add(count=num_frames)
            else:
                print(f"Found fcurve for shape key {sk.path_from_id()}")
            self.sk_fcurves += [fc]

        for custom_prop in self.custom_props:
            datapath = f"[\"{custom_prop}\"]"
            for i in range(num_frames):
                self.target.keyframe_insert(datapath,frame=i)
            self.custom_prop_fcurves += [fc for fc in self.target.animation_data.action.fcurves if fc.data_path == datapath]
    
    # this method actually sets the keyframe values via bpy
    def update_keyframes(self):
        # a bit slow to use bpy.context.object.data.shape_keys.keyframe_insert(datapath,frame=frame)
        # (where datapath is something like 'key_blocks["MouthOpen"].value') 
        # better to add a new fcurve for each shape key then set the points in one go        

        for i_sk,fc in enumerate(self.sk_fcurves):
            fc.keyframe_points.foreach_set('co',self.sk_frame_data[i_sk])
            fc.update()
            
        for i_b,fc, in enumerate(self.custom_prop_fcurves):
            fc.keyframe_points.foreach_set('co',self.custom_prop_framedata[i_b])
            fc.update()
       
    def update_to_frame(self, frame=0):
        self.target.data.shape_keys.key_blocks.foreach_set("value", self.sk_frames[frame])        
        for i,custom_prop in enumerate(self.custom_props):
            self.target[custom_prop] = self.custom_prop_framedata[i][(2*frame)+1]
        self.target.data.shape_keys.user.update()

class LiveLinkFaceServer:

    def __init__(self, targets, record, host, udp_port):
        self.record = record
        self.start_frame = -1
        self.listening = False
        self.host = host
        self.port = udp_port
        self.targets = [ LiveLinkTarget(x,num_frames=3600,action_name=f"LiveLinkFace") for x in targets ]
        
        bpy.app.timers.register(self.read_from_socket)
        self.create_socket()
        print(f"Ready to receive network stream on {self.host}:{self.port}")
    
    def isListening(self):
        return self.listening

    def listen(self):
        self.listening = True
        self.start_frame = -1

    def stopListening(self):
        self.listening = False;

    def create_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((self.host, self.port)) 
                                                
    def read_from_socket(self):
        if not self.listening:
            return
        interval = 1 / 60
        frame = None
        try:
            # continue reading from the socket until the buffer is drained
            while True:
                data, addr = self.sock.recvfrom(312) 
                success, live_link_face = PyLiveLinkFace.decode(data)
                if success:
                    if self.start_frame == -1:
                        self.start_frame = live_link_face._frames
                    if self.record:
                        frame = live_link_face._frames - self.start_frame
                    else:
                        frame = 0
                    for t in self.targets:
                        for i in range(len(FaceBlendShape)):
                            val = live_link_face.get_blendshape(FaceBlendShape(i))
                            t.set_frame_value(i, frame, val)
        except socket.error as e:
            pass
        except Exception as e:
            print(traceback.format_exc())
            print(e)
        if frame is not None:
            if self.record:
                bpy.context.scene.frame_current = frame 
            else:
                bpy.context.scene.frame_current = 0 
            for t in self.targets:
                t.update_keyframes()
           
        return interval
    
    def close(self):
        try:
            bpy.app.timers.unregister(self.handle_data)
        except:
            print("Failed to unregister timer")
            pass
        self.sock.close()
        self.start_frame = 0
       
