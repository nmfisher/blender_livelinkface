import time
import socket 
import bpy 
import csv

from livelinkface.pylivelinkface import PyLiveLinkFace, FaceBlendShape

instance = None

''' Create an instance of an BlenderLiveLinkFaceAnimator that will listen on the given IP/port. Prefer using this method than constructing an instance directly as this will ensure that any pre-existing connections are closed'''
def create_instance(target, host= "0.0.0.0", port = 11111):
    global instance
    if instance is not None:
        instance.close()
    instance = LiveLinkFaceServer(target, host, port)
    
class LiveLinkTarget:

    def __init__(self, target, num_frames, action_name=None):
        
        self.target = target
                
        # this is where the values for the shape keys/bones at every frame
        # if you are streaming, you only need to pass num_frames=0 and the first frame will be used each time
        self.sk_frames = [[0] * len(self.target.data.shape_keys.key_blocks)]*num_frames
        
        self.bone_props = [] 
        
        # iterate over LIVE_LINK_HEADER and extract any ARKit blendshape names that are driven by bones in the target object
        for i in range(LIVE_LINK_HEADER - 2):
            bone_prop = self.livelink_to_bone_prop(i)
            if bone_prop is not None:
                bone_props += [bone_prop]
                
        self.bone_frames = [[0] * len(self.bone_props)]*num_frames
                
        if action_name is not None:
            self.create_action(action_name)
            
    '''Sets the value for the LiveLink blendshape at index [i_ll] to [val] for frame [frame] (note the underlying target may be a blendshape or a bone).'''
    def set_frame_value(self, i_ll, val, frame=0):
        i_sk = self.livelink_to_shapekey_idx(i_ll)
        bone_idx = 0
        if i_sk != -1:
            self.sk_frames[frame][i_sk] = value
        else:
            bone_prop = self.livelink_to_bone_prop(i_ll)
            if bone_prop is not None:
                self.bone_frames[frame][bone_idx] = val
                bone_idx += 1
            else:
            #    print(f"Failed to set bone prop for {i_ll}")
                pass

    '''Loads a CSV in LiveLinkFace format. First line is the header (Timecode,BlendshapeCount,etc,etc), every line thereafter is a single frame with comma-separated weights'''
    @staticmethod
    def fromcsv(self,target,path,use_first_frame_as_zero=False, action_name):        
        csvdata = [x for x in csv.reader(open(path,"r"))]
        num_frames = len(csvdata) - 1
        
        target = LiveLinkTarget(target, num_frames, action_name=action_name)

        for blendshape,idx in enumerate(LIVE_LINK_FACE_HEADER):
            if idx == 0:
                continue
            
            rest_weight = float(csvdata[1][idx])
            
            for i in range(1, num_frames):
                val = float(csvdata[i][idx])
                if self.use_first_frame_as_zero:
                    val -= rest_weight
                self.set_frame_value(idx, i-1, val)
        
        target.update_animation()
    
    def update_animation(self):
        # a bit slow to use bpy.context.object.data.shape_keys.keyframe_insert(datapath,frame=frame)
        # (where datapath is 'key_blocks["MouthOpen"].value') 
        # better to add a new fcurve for each shape key then set the points in one go        
        for i_sk,fc in enumerate(self.sk_fcurves):
            frame_data = [i,self.sk_frames[i][i_sk] for i in len(self.sk_frames)]
            fc.keyframe_points.foreach_set('co',frame_data)
       
    def create_action(self, action_name):
    
        # create a new Action so we can directly create fcurves and set the keyframe points
        self.sk_action = bpy.data.actions.new(f"action_name) 
    
        # create the bone AnimData if it doesn't exist 
        if target.animation_data is None:
            target.animation_data_create()
            
        target.data.shape_keys.animation_data.action = self.action
            
        # create the shape key AnimData if it doesn't exist 
        if target.data.shape_keys.animation_data is None:
            target.data.shape_keys.animation_data_create()
            
        target.data.shape_keys.animation_data.action = self.action
        
        self.sk_fcurves = []
        
        for sk in target.data.shape_keys.key_blocks:
            datapath = f"{sk.path_from_id()}.value"
            fc = action.fcurves.new(datapath)
            fc.keyframe_points.add(count=len(self.sk_frames))
            self.sk_fcurves += [fc]
            
        for bone_prop in self.bone_props:
            fc = action.fcurves.new(datapath)
        
        for bone_prop in 
    
    def livelink_to_shapekey_idx(self, target, ll_idx):
        name = LIVE_LINK_FACE_HEADER[ll_idx+2]
        for n in [name, name[0].lower() + name[1:]]:
            idx = target.data.shape_keys.key_blocks.find(n)
            if idx != -1:
                return idx
        return idx

    def livelink_to_bone_prop(self, ll_idx):
        name = LIVE_LINK_FACE_HEADER[ll_idx+2]
        for n in [name, name[0].lower() + name[1:]]:
            try:
                target[n]
                return n
            except:
                pass
        return None        
       
    def update_to_frame(self, frame=0):
        self.target.data.shape_keys.key_blocks.foreach_set("value", self.sk_frames[frame])        
        for i,bone_prop in enumerate(self.bone_props):
            self.target[bone_prop] = self.bone_frames[frame][i]
        self.target.data.shape_keys.user.update()

class LiveLinkFaceServer:

    def __init__(self, target, host, udp_port):
        self.host = host
        self.port = udp_port
        self.millis = int(round(time.time() * 1000))
        self.target = LiveLinkTarget(target)
        
        bpy.app.timers.register(self.handle_data)
        self.create_socket()
        print(f"Animator listening on {self.host}:{self.port}")

    def create_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((self.host, self.port)) 
                                                
    def handle_data(self):
        interval = 1/60
        data = None
        try:
            current = int(round(time.time() * 1000))
            self.millis = current
            
            while True:
                try:
                    data, addr = self.sock.recvfrom(309) 
                except socket.error as e:
                    break
            if data is None:
                return interval
            success, live_link_face = PyLiveLinkFace.decode(data)
            if success:
                for i in range(len(FaceBlendShape)):
                    val = live_link_face.get_blendshape(FaceBlendShape(i))
                    self.target.set_frame_value(i, val, frame=0)
                self.target.update_to_frame(0)

        except Exception as e:
            print(e)
            
        return interval
    
    def close(self):
        try:
            bpy.app.timers.unregister(self.handle_data)
        except:
            pass
        self.sock.close()
       
