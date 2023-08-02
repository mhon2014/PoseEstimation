import bpy
import numpy as np
import mathutils
import math
import json

import os, shutil

class Generator():
    def __init__(self, filePath = None, objectFile = None):
        '''
        Constructor, set the objects or multiple objects if there are any
        '''

        #Use this setting to setup blank workspace'''
        bpy.ops.wm.read_factory_settings(use_empty=True)
    
        bpy.ops.world.new()

        # self.data = bpy.data
        # self.context = bpy.context

        #Current scene
        self.scene = bpy.context.scene
        
        #Create anchor points for the objects
        self.ObjectAxis = bpy.data.objects.new(name='ObjectAxis', object_data=None)
        self.scene.collection.objects.link(self.ObjectAxis)

        #Create anchor points for the camera axis
        self.CameraAxis = bpy.data.objects.new(name='CameraAxis', object_data=None)
        self.scene.collection.objects.link(self.CameraAxis)
        self.CameraAxis.parent = self.ObjectAxis
        self.CameraAxis.rotation_mode = 'QUATERNION'
        self.CameraAxis.rotation_quaternion = (1,0,0,0)

        #https://blender.stackexchange.com/questions/151319/adding-camera-to-scene
        cameraData = bpy.data.cameras.new(name='Camera')
        self.Camera = bpy.data.objects.new('Camera', cameraData)
        self.scene.collection.objects.link(self.Camera)
        self.Camera.parent = self.CameraAxis
        self.cameraDistance = 0
        
        #Set the scene camera to the newly added camera
        self.scene.camera = bpy.data.objects['Camera']

        #Adding Sun lighting
        lightingData= bpy.data.lights.new(name='Sun', type='SUN')
        self.lighting = bpy.data.objects.new('Sun', lightingData)
        self.scene.collection.objects.link(self.lighting)
        self.lighting.parent = self.ObjectAxis
        self.lighting.rotation_mode = 'QUATERNION'
        self.lighting.rotation_quaternion = (1,0,0,0)

        #Random number generator
        self.rng = np.random.default_rng()

        #define file path if given
        #can use bpy.path.abspath("//") but this seems a bit cleaner and reliable
        if not filePath:
            filePath = './'

        print('Working directory: ' + filePath)

        try:
            os.makedirs(filePath + '/data/')
        except FileExistsError:
            print('Data directories exist, proceding with initialization')
        except Exception as e:
            raise e
        
        try:
            os.makedirs(filePath + '/annotation/')
        except FileExistsError:
            print('Annonation directory exist, proceding with initialization')
        except Exception as e:
            raise e
        
        try:
            os.makedirs(filePath + '/tmp_exr/')
        except FileExistsError:
            print('Temporary directory exist, proceding with initialization')
        except Exception as e:
            raise e
        
        

        self.dataFilePath = os.path.join(filePath, 'data/')
        self.annotationFilePath = os.path.join(filePath,'annotation/')
        self.tempFilePath = os.path.join(filePath, 'tmp_exr/')

        print('File Paths for data and annotation: ')
        print(self.dataFilePath)
        print(self.annotationFilePath)
        print(self.tempFilePath)

        #self._cleanFolder(self.tempFilePath)

        #Import Object
        self.objects = None

        if objectFile:
            bpy.ops.import_scene.obj(filepath=objectFile)

            #All imported objects are listed under selected after importing
            self.objects = bpy.context.selected_objects

            for object in self.objects:
                object.parent = self.ObjectAxis     

            #Find all the meshes and add them to a list
            # if bpy.data.objects:
            #     for object in bpy.data.objects:
            #         if object.type == 'MESH':
            #             object.parent = self.objectAxis
            #             self.objects.append(object)

            #finds the camera distance where the entire object fits into view
            self.cameraDistance = self.findCameraDistance(self.Camera, self.objects)
            
            self.Camera.location = (0, 0, self.cameraDistance)

        print(bpy.context.selected_objects)

        # print(self.scene.render.filepath)

        #https://blender.stackexchange.com/questions/27396/whats-the-difference-among-object-active-object-and-selected-objects
        # I wouldn't worry about active objects, selected objects ect...
        # As long as your using bpy.data to select or modify objects directly
        # instead of relying on bpy.context and active objects
        #self.ops.object.select_all(action='DESELECT')

    def setFilePaths(self):
        pass
    
    def importObject(self, objectFile):
        '''
        Setter function for importing the object from an object file and setting the objects list
        '''
        if self.objects:
            # bpy.ops.object.select_all(action='DESELECT')
            for obj in self.objects:
                bpy.data.objects.remove(obj, do_unlink = True)
        

        bpy.ops.import_scene.obj(filepath=objectFile)
        #All imported objects are listed under selected after importing
        self.objects = bpy.context.selected_objects

        for object in self.objects:
            object.parent = self.ObjectAxis
        

    def randomQuaternion(self):
        '''Generate a random quaternion with uniformly distributed orientations'''
        w = self.rng.uniform(-1, 1)
        x, y, z = self.rng.uniform(-1, 1, size=3)
        mag = np.sqrt(w**2 + x**2 + y**2 + z**2)
        quat = np.array([w, x/mag, y/mag, z/mag])

        return quat
    
    def getResolution(self):
        '''Utility function used for camera resolution'''
        resolution_scale = (self.scene.render.resolution_percentage / 100.0)
        resolution_x = self.scene.render.resolution_x * resolution_scale # [pixels]
        resolution_y = self.scene.render.resolution_y * resolution_scale # [pixels]
        return int(resolution_x), int(resolution_y)
    
    def cleanFolder(self, folderPath):
        '''
        Utility function to clear temporary folder and files if it exist,
        else create the folder, intended for internal use only
        '''
        if os.path.isdir(folderPath):
            for filename in os.listdir(folderPath):
                filePath = os.path.join(folderPath, filename)
                try:
                    if os.path.isfile(filePath) or os.path.islink(filePath):
                        #delete file if it exist
                        os.unlink(filePath)
                    elif os.path.isdir(filePath):
                        #remove tree path
                        #https://docs.python.org/3/library/shutil.html
                        shutil.rmtree(filePath)
                except Exception as e:
                    print('Failed to delete {filePath}. Reason: {error}'.format(filePath, e))
        else:
            pass

    def loadData(self, filePath, type=None):
        '''
        Utility function used to load array data from temporary exr file
        '''
        # Possible workaround for future
        # https://blender.stackexchange.com/questions/2170/how-to-access-render-result-pixels-from-python-script/248543#248543
        if not os.path.isfile(filePath):
            return None
        
        data = bpy.data.images.load(filePath)

        #Pixels coordinates are usually 0,0 starting top left, 
        #instead of the usual 0,0 bottom left known in math and graphs
        #https://blender.stackexchange.com/questions/471/is-it-possible-to-make-blender-a-y-up-world
        pixels = np.array(data.pixels)
        res_x, res_y = self.getResolution()
        pixels.resize((res_y, res_x, 4)) #(y, x, channels)
        pixels = np.flip(pixels, 0) # Flip the y axis

        return pixels

    def saveData(self):
        pass

    def findCameraDistance(self, cameraArg, objectArg):
        '''
        Function to return the distance for the camera to fit everything in view
        '''
        bbox_min = mathutils.Vector((float("inf"), float("inf"), float("inf")))
        bbox_max = mathutils.Vector((float("-inf"), float("-inf"), float("-inf")))

        #determine the max and min of the bounding boxs, use matrix_world to convert to global space
        for obj in objectArg:
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
        fov = min(cameraArg.data.angle_y, cameraArg.data.angle_x)

        #lens can also be used if you know the equation
        #flength = camera.data.lens

        #Use camera equation 
        #https://www.omnicalculator.com/other/camera-field-of-view
        #https://blender.stackexchange.com/questions/92201/what-does-focal-length-mean-in-blender
        #http://www.artdecocameras.com/resources/angle-of-view/
        distance = max_dimension / (2*math.tan(fov/ 2))
        
        return distance

    def generateData(self, amount = 0, format = 'PNG'):
        #### TODO Set position and different angels for camera randomize them
        #### Freeform and locked
        #### DONE: Locked

        self.cleanFolder(self.dataFilePath)
        self.cleanFolder(self.annotationFilePath)

        self.scene.render.image_settings.file_format= format

        if amount == 0:
            print("No data generated, data size specified is 0\n")
            return

        axis = self.CameraAxis
        lighting = self.lighting
        camera = self.Camera
        
        fileList = []

        annotationfile = os.path.join(self.annotationFilePath, 'annotation.json')
        
        

        for i in range(amount):

            #Get random quaternion for position
            quaternion = mathutils.Quaternion(self.randomQuaternion())
            axis.rotation_quaternion = axis.rotation_quaternion @ quaternion
            lighting.rotation_quaternion = lighting.rotation_quaternion @ quaternion
            
            # distance = self.rng.uniform(0, 15*self.cameraDistance)
            # camera.location = (0,0,distance)

            #Set the render save path for the image
            imageFile = 'image{index}'.format(index = i)
            imagePath = os.path.join(self.dataFilePath, imageFile)
            self.scene.render.filepath = imagePath

            #render the view and save
            bpy.ops.render.render(write_still=True)

            #Set segmentation image file path and name
            segmentationFile = 'segmentation{index}.npy'.format(index=i)
            segmentationPath = os.path.join(self.annotationFilePath, segmentationFile)

            # Bounding box coordinates
            # bbox = self.getBoundingBoxCoordinates()

            # retrieve segmentation
            segmentation = self.getSegmentation()

            #Save segmentation array to npy file
            np.save(segmentationPath, segmentation[:,:,0])

            #Dictionary for the annotation
            data = {'id': i,
                    'image_file' : imageFile,
                    'segmentation_file' : segmentationFile,
                    # 'bbox' : bbox,
                    'quaternion' : list(axis.rotation_quaternion)
                }
            

            # Append a dictionary to list
            fileList.append(data)

        #Dump the list into a json file
        annotation = { 'images' : fileList}
        with open(annotationfile, 'w+') as outfile:
            json.dump(annotation, outfile, indent=4)

    def getBoundingBox(self, object):
        '''
        Returns camera bounding box of mesh object.

        Negative 'z' value means the point is behind the camera.

        https://federicoarenasl.github.io/Data-Generation-with-Blender/#Main-function-to-extract-labels-from-all-objects-in-image
        https://blender.stackexchange.com/questions/7198/save-the-2d-bounding-box-of-an-object-in-rendered-image-to-a-text-file

        '''

        '''Transformation matrix'''
        matrix = self.Camera.matrix_world.normalized().inverted()

        '''Using inverse of matrix to undo any transformation'''
        mesh = object.to_mesh(preserve_all_data_layers=True)
        # mesh = object
        mesh.transform(object.matrix_world)
        mesh.transform(matrix)

        ''' world coordinates for the camera view frame bounding box'''
        frame = [-v for v in self.Camera.data.view_frame(scene=self.scene)[:3]]

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
    
    def setSegmentationNodes(self):
        '''This section uses the compositor functions in blender and sets it up
            Some terminologies:
            Nodes -> Collection of nodes in the compositor and contains inputs and outputs,
                    this handles creation of nodes
                    
            Links -> Links handles the links between the nodes, this is used for 
                    linking inputs and outputs of nodes together

            Using Temporary file, for now in Open EXR format
            https://blender.stackexchange.com/questions/148231/what-image-format-encodes-the-fastest-or-at-least-faster-png-is-too-slow
        '''

        #Set engine to cycles for object indexing
        self.scene.render.engine = 'CYCLES'
        # bpy.context.scene.render.engine = 'CYCLES'
        self.scene.view_layers['ViewLayer'].use_pass_object_index = True

        self.scene.use_nodes = True

        for i,obj in enumerate(self.objects):
            obj.pass_index = i+1

        nodes = self.scene.node_tree.nodes
        links = self.scene.node_tree.links

        #Remove initial composite node
        nodes.remove(nodes['Composite'])

        #layer node
        renderLayers = nodes['Render Layers']

        # segmentationViewer = nodes.new(type='CompositorNodeViewer')
        # segmentationViewer.name = 'Segmentation'
        # segmentationViewer.label = 'Segmentation'

        #Create output file node
        outputFile = nodes.new(type='CompositorNodeOutputFile')
        #Clear the slots
        outputFile.layer_slots.clear()
        outputFile.name = 'OutputFile'
        ## Set up the output format
        outputFile.format.file_format = 'OPEN_EXR'
        outputFile.format.color_mode = 'RGBA'
        outputFile.format.color_depth = '32'
        outputFile.format.exr_codec = 'PIZ'

        # #Create segmentation node, segmentation uses object pass index
        # segmentation = nodes.new(type='CompositorNodeComposite')
        # segmentation.name = 'Segmentation'
        # segmentation.label = 'Segmentation'

        self.cleanFolder(self.tempFilePath)

        #Set the path for the output
        outputFile.base_path = self.tempFilePath
        segmentationOutput = outputFile.layer_slots.new('SegmentationMask')

        #Link the index segmentation to the slot of the output node
        links.new(renderLayers.outputs['IndexOB'], segmentationOutput)
        
        # links.new(renderLayers.outputs['IndexOB'], segmentationViewer.inputs[0])

        # #Link the layer output to the input of the segmentation node
        # links.new(layers.outputs['IndexOB'], segmentation.inputs[0])

    def getSegmentation(self):
        '''
            Loads image exr and returns the data
        '''
        #https://blender.stackexchange.com/questions/170381/how-can-i-get-pixels-from-multiple-render-passes-through-python-and-store-them-t
        #https://blender.stackexchange.com/questions/149444/is-there-some-way-i-can-update-the-viewer-node-during-background-rendering-to-ou
        #https://blender.stackexchange.com/questions/69230/python-render-script-different-outcome-when-run-in-background

        # bpy.data.images['Render Result'].save_render('temporary.png')
        filePath = os.path.join(self.tempFilePath, 'SegmentationMask0001.exr')
        # print(filePath)

        segmentation = self.loadData(filePath)

        # print(segmentation.shape)
        # print(np.unique(segmentation))
        # im = Image.fromarray(npImage)
        # im.save("anotation/testfile.png")
        return segmentation

        # categories_id = index
        # obj = object
        # # set each instance a unique inst_id, which is used to generate instance annotation.
        # obj["inst_id"] = categories_id * 20

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
    
    def getBoundingBoxCoordinates(self):
        allBbox = []

        for i,object in enumerate(self.objects):
            # print("     On object:", object)

            bbox = self.getBoundingBox(object) # Get current object's coordinates

            if bbox: # boundingbox2d are found then do format
                # print("         Initial coordinates:", bbox)
                coordinates = self.formatCoordinates(id, bbox)
                # print("         coordinates:", coordinates)

                allBbox.append(coordinates) # Update main_text_coordinates variables whith each
                # line corresponding to each class in the frame of the current image
            
            else:
                print("         Object not visible")
                pass

        return allBbox 