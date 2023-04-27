import bpy
import bpycv
import cv2
import numpy as np
import mathutils
import math
import json
import os
import sys

class DataGenerator:
    '''
    Constructor, set the objects or multiple objects if there are any
    '''

    # file_loc = '' load objects
    # imported_object = bpy.ops.import_scene.obj(filepath=file_loc)
    # obj_object = bpy.context.selected_objects[0] ####<--Fix

    def __init__(self, filePath = None, objectFile = None, lockedView = False):

        bpy.ops.wm.read_factory_settings(use_empty=True)
    
        #Create anchor points for the objects and camera axis
        bpy.ops.world.new()
        bpy.ops.object.empty_add()
        bpy.data.objects['Empty'].name = 'ObjectAxis'
        bpy.ops.import_scene.obj(filepath=objectFile)

        bpy.ops.object.empty_add()
        bpy.data.objects['Empty'].name = 'CameraAxis'

        bpy.ops.object.camera_add()
        
        # bpy.context.screen.scene = scene
        bpy.context.scene.camera = bpy.data.objects['Camera']


        #define file path if given
        #can use bpy.path.abspath("//") however explicit defintion is better
        self.filePath = filePath if filePath else './'
        #Set the variables
        self.scene = bpy.context.scene
        self.objectAxis = bpy.data.objects['ObjectAxis']

        self.cameraAxis =  bpy.data.objects['CameraAxis']
        self.cameraAxis.parent = self.objectAxis
        self.cameraAxis.rotation_mode = 'QUATERNION'
        self.cameraAxis.rotation_quaternion = (1,0,0,0)

        self.camera = bpy.data.objects['Camera']
        self.camera.parent = bpy.data.objects['CameraAxis']

        self.objects = []
        
        #Find all the meshes and add them to a list
        if bpy.data.objects:
            for object in bpy.data.objects:
                if object.type == 'MESH':
                    object.parent = self.objectAxis
                    self.objects.append(object)

        self.camera.location = (0, 0, self.findDistanceObject())

        
    def findDistanceObject(self):
        bbox_min = mathutils.Vector((float("inf"), float("inf"), float("inf")))
        bbox_max = mathutils.Vector((float("-inf"), float("-inf"), float("-inf")))

        #determine the max and min of the bounding boxs, use matrix_world to convert to global space
        for obj in self.objects:
            bbox = obj.bound_box
            for i in range(8):
                v = obj.matrix_world @ mathutils.Vector((bbox[i][0], bbox[i][1], bbox[i][2]))
                bbox_min.x = min(bbox_min.x, v.x)
                bbox_min.y = min(bbox_min.y, v.y)
                bbox_min.z = min(bbox_min.z, v.z)
                bbox_max.x = max(bbox_max.x, v.x)
                bbox_max.y = max(bbox_max.y, v.y)
                bbox_max.z = max(bbox_max.z, v.z)
                
        bbox = (bbox_min, bbox_max)

        #ignore these as they were done for testing and learning purposes
        #center = (bbox[1] + bbox[0]) / 2.0
        #test_dimension = bbox[1] - bbox[0] + center

        dimension = bbox[1] - bbox[0]

        # Get the maximum dimension of the bounding box using the diagonal length
        max_dimension = math.sqrt(dimension[0]**2 + dimension[1]**2)

        #Get vertical camera angle
        fov = min(self.camera.data.angle_y, self.camera.data.angle_x)

        #can also be used if you know the equation
        #flength = camera.data.lens

        #Use camera equation 
        #https://www.omnicalculator.com/other/camera-field-of-view
        #https://blender.stackexchange.com/questions/92201/what-does-focal-length-mean-in-blender
        #http://www.artdecocameras.com/resources/angle-of-view/
        distance = max_dimension / (2*math.tan(fov/ 2))
        
        return distance

    def generateBatch(self):
        
        try:
            os.makedirs(self.filePath + '/data/')
        except FileExistsError:
            print('Data directories exist, preceding with batch generation')
        except Exception as e:
            raise e
        
        try:
            os.makedirs(self.filePath + '/annotation/')
        except FileExistsError:
            print('Annonation directory exist, preceding with batch generation')
        except Exception as e:
            raise e

        #### TODO Set position and different angels for camera randomize them
        #### Freeform and locked
        #### DONE: Locked

        axis = self.cameraAxis

        #### TEST CODE
        for i in range(1):
            
            # Generate a random quaternion with uniformly distributed orientations
            # w = np.random.uniform(-1, 1)
            # x, y, z = np.random.uniform(-1, 1, size=3)
            # mag = np.sqrt(w**2 + x**2 + y**2 + z**2)
            # quat = np.array([w, x/mag, y/mag, z/mag])

            # quaternion = mathutils.Quaternion(quat)
            # axis.rotation_quaternion = axis.rotation_quaternion @ quaternion

            print("On render:", 1)
            print("--> Location of the camera:")
            self.scene.render.filepath =  self.filePath + 'data/' + 'testfilename'

            #render the view and save
            bpy.ops.render.render(write_still=True)

            annotationfile = self.filePath + 'annotation/' + 'testfileannotation.json'
            bbox = self.getCoordinates()
            annotation = {"bbox": bbox}

            result = bpycv.render_data()
            cv2.imwrite("demo-inst.png", np.uint16(result["inst"]))
            cv2.imwrite("demo-vis(inst_rgb_depth).jpg", result.vis()[..., ::-1])


            with open(annotationfile, 'w+') as outfile:
                json.dump(annotation, outfile)


    def boundingBox2D(self, object):
        '''
        Returns camera bounding box of mesh object.

        Negative 'z' value means the point is behind the camera.

        https://federicoarenasl.github.io/Data-Generation-with-Blender/#Main-function-to-extract-labels-from-all-objects-in-image
        https://blender.stackexchange.com/questions/7198/save-the-2d-bounding-box-of-an-object-in-rendered-image-to-a-text-file

        '''

        '''Transformation matrix'''
        matrix = self.camera.matrix_world.normalized().inverted()

        '''Using inverse of matrix to undo any transformation'''
        mesh = object.to_mesh(preserve_all_data_layers=True)
        # mesh = object
        mesh.transform(object.matrix_world)
        mesh.transform(matrix)


        ''' world coordinates for the camera view frame bounding box'''
        frame = [-v for v in self.camera.data.view_frame(scene=self.scene)[:3]]

        # print(frame)

        # Check if camera is in perspective or orthographic mode, 
        # camera_persp = self.camera.type != 'ORTHO'

        lx = []
        ly = []

        for v in mesh.vertices:
            co_local = v.co
            z = -co_local.z

            if z <= 0.0:
                ''' Vertex is behind the camera; ignore it. '''
                continue
            else:
                ''' Perspective division '''
                frame = [(v / (v.z / z)) for v in frame]

            min_x, max_x = frame[1].x, frame[2].x
            min_y, max_y = frame[0].y, frame[1].y

            x = (co_local.x - min_x) / (max_x - min_x)
            y = (co_local.y - min_y) / (max_y - min_y)

            lx.append(x)
            ly.append(y)

        ''' Image is not in view if all the mesh verts were ignored '''
        if not lx or not ly:
            return None
            

        '''Limit the values between 0.0 and 1.0'''
        # min_x = np.clip(min(lx), 0.0, 1.0)
        # max_x = np.clip(max(lx), 0.0, 1.0)

        # min_y = np.clip(min(ly), 0.0, 1.0)
        # max_y = np.clip(max(ly), 0.0, 1.0)

        min_x = np.clip(min(lx), 0.0, 1.0)
        min_y = np.clip(min(ly), 0.0, 1.0)
        max_x = np.clip(max(lx), 0.0, 1.0)
        max_y = np.clip(max(ly), 0.0, 1.0)

        ''' Image is not in view if both bounding points exist on the same side '''
        if min_x == max_x or min_y == max_y:
            return None

        #Get resolution for the render to create the coco annotation
        render = self.scene.render
        # fac = render.resolution_percentage * 0.01
        dim_x = render.resolution_x
        dim_y = render.resolution_y 


        '''Return coordinates in coco style annotation'''
        return (min_x*dim_x, (1-min_y)*dim_y), (max_x*dim_x, (1-max_y)*dim_y)


    def segmentationInstances(self, index, object):

    #### TODO: Get Segmentation image/array
    #### Segmentation using library or camera rays.

        categories_id = index
        obj = object
        # set each instance a unique inst_id, which is used to generate instance annotation.
        obj["inst_id"] = categories_id * 20


    def formatCoordinates(self, id, coordinates):
        if coordinates: 
        ## Change coordinates reference frame
            x1 = (coordinates[0][0])
            x2 = (coordinates[1][0])
            y1 = (coordinates[1][1])
            y2 = (coordinates[0][1])

            width = (x2-x1)  # Calculate the absolute width of the bounding box
            height = (y2-y1) # Calculate the absolute height of the bounding box

            #center
            # cx = x1 + (width/2) 
            # cy = y1 + (height/2)

            ## Formulate line corresponding to the bounding box of one class
            bboxCoordinates = [x1, y1, width, height]
            return bboxCoordinates
        else:
            pass
    
    def getCoordinates(self):
        allBbox = []

        for i,object in enumerate(self.objects):
            print("     On object:", object)


            bbox = self.boundingBox2D(object) # Get current object's coordinates

            #### TODO
            # get segmentation
            self.segmentationInstances(i+1, object)


            if bbox: # boundingbox2d are found then do format
                print("         Initial coordinates:", bbox)
                coordinates = self.formatCoordinates(id, bbox)
                print("         coordinates:", coordinates)

                allBbox.append(coordinates) # Update main_text_coordinates variables whith each
                # line corresponding to each class in the frame of the current image
            
            else:
                print("         Object not visible")
                pass

        return allBbox 

if __name__ == '__main__':

    #blender --background file --python pythonfile

    # blender = DataGenerator(objectFile='./models/Juno/JunoOBJ/Juno.obj')
    blender = DataGenerator(objectFile='/Users/Mjhon/Desktop/Research/3DPoseEstimation/BlenderDataGenerator/models/Juno/JunoOBJ/Juno.obj')

    print(blender.filePath)
    # print('Hello')
    # print(blender)
    blender.generateBatch()
    
