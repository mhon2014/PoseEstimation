import bpy
import bpycv
import numpy as np
import json
import os
import sys

class Render:
    '''
    Constructor, set the objects or multiple objects if there are any
    '''
    def __init__(self, filePath = None):
        
        self.scene = bpy.data.scenes['Scene']
        self.camera = None
        self.filePath = bpy.path.abspath("//")
        

        # if bpy.data.meshes:
        #     for key, object in bpy.data.meshes.items():
        #         self.objects[key] = object

        self.objects = []

        if bpy.data.objects:

            for object in bpy.data.objects:
                if object.type == 'MESH':
                    self.objects.append(object)
                    
            self.camera = bpy.data.objects['Camera']


        #### TODO: Set camera in view of objects
        
    def setCamera(self):
        pass

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

        for i in range(1):
            print("On render:", 1)
            print("--> Location of the camera:")
            self.scene.render.filepath =  self.filePath + '/data/' + 'testfilename'
            bpy.ops.render.render(write_still=True)

            annotationfile = self.filePath + 'annotation/' + 'testfileannotation.json'
            bbox = self.getCoordinates()
            annotation = {"bbox": bbox}

            with open(annotationfile, 'w+') as outfile:
                json.dump(annotation, outfile)


    def boundingBox2D(self, object):
        '''
        Returns camera space bounding box of mesh object.`

        Negative 'z' value means the point is behind the camera.

        Takes shift-x/y, lens angle and sensor size into account
        as well as perspective/ortho projections.


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

        # #Double check if camera is in perspective or orthographic mode, 
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


        render = self.scene.render
        # fac = render.resolution_percentage * 0.01
        dim_x = render.resolution_x
        dim_y = render.resolution_y 



        return (min_x*dim_x, (1-min_y)*dim_y), (max_x*dim_x, (1-max_y)*dim_y)

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
            if bbox: # If find_bounding_box() doesn't return None
                print("         Initial coordinates:", bbox)
                coordinates = self.formatCoordinates(id, bbox) # Reformat coordinates to YOLOv3 format
                print("         coordinates:", coordinates)

                allBbox.append(coordinates) # Update main_text_coordinates variables whith each
                # line corresponding to each class in the frame of the current image
            
            else:
                print("         Object not visible")
                pass

        return allBbox 
    

if __name__ == '__main__':

    #blender --background file --python pythonfile

    blender = Render()
    print(blender.filePath)
    # print(blender.getCoordinates())
    blender.generateBatch()
    
