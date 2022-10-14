instance = None

''' Create an instance of an BlenderLiveLinkFaceAnimator that will listen on the given IP/port. Prefer using this method than constructing an instance directly as this will ensure that any pre-existing connections are closed'''
def create_instance(target, host= "0.0.0.0", port = 11111):
    global instance
    if instance is not None:
        instance.close()
    instance = BlenderLiveLinkFaceAnimator(target, host, port)

class BlenderLiveLinkFaceAnimator:

    def __init__(self, target, host, udp_port):
        self.host = host
        self.port = udp_port
        self.millis = int(round(time.time() * 1000))
        self.target = target
        self.ll_to_sk = [-1] * len(FaceBlendShape)    
        self.ll_to_bone = [-1] * len(FaceBlendShape)    
        self.sk_vals = [0] * len(self.target.data.shape_keys.key_blocks)
        bpy.app.timers.register(self.handle_data)
        self.create_socket()
        print(f"Animator listening on {host}:{port}")

    def create_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((self.host, self.port)) 
                        
    def livelink_to_shapekey_idx(self, i):
        name = LIVE_LINK_FACE_HEADER[i+2]
        for n in [name, name[0].lower() + name[1:]]:
            idx = self.target.data.shape_keys.key_blocks.find(n)
            if idx != -1:
                return idx
        return idx
    
    def livelink_to_bone_prop(self, i):
        name = LIVE_LINK_FACE_HEADER[i+2]
        for n in [name, name[0].lower() + name[1:]]:
            try:
                self.target[n]
                return n
            except:
                pass
        return None        
        
    def set_value_for_index(self, i_ll, value):
        i_sk = self.livelink_to_shapekey_idx(i_ll)
        if i_sk != -1:
            self.sk_vals[i_sk] = value
        else:
            bone_prop = self.livelink_to_bone_prop(i_ll)
            if bone_prop is not None:
                self.target[bone_prop] = value
            #else:
            #    print(f"Failed to set bone prop for {i_ll}")
    
    def update(self):
        self.target.data.shape_keys.key_blocks.foreach_set("value", self.sk_vals)
        self.target.data.shape_keys.user.update()
            
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
                    self.set_value_for_index(i, live_link_face.get_blendshape(FaceBlendShape(i)))
                self.update()
            #else:
            #    print("Fail")

        except Exception as e:
            print(e)
            
        return interval
    
    def close(self):
        try:
            bpy.app.timers.unregister(self.handle_data)
        except:
            pass
        self.sock.close()
        
        
                    