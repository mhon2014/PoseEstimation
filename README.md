# 3DPoseEstimation
[Description](#description)

[Getting Started](#gettingstarted)

[Data Preview](#datapreview)

[References](#references)

<h2 id='description'> Description </h2>

---
This repository contains Python code to interface with blender to generate synthetic data. These data are images that include annotation of segmentation and object quaternion. Random rotation and camera distances are currently used for data generation, other variations may be included later for future addition.

<h2 id='gettingstarted'> Getting Started </h2>

---
To get started clone this repo into you desired folder. Import the class as shown below.

```python
from BlenderDataGenerator import SatteliteData

generator = SatteliteData.Generator()

```
<h2 id='datapreview'> Data Preview </h2>

---
JSON annotation example
```json
{
    "images": [
        {
            "id": 0,
            "image_file": "image0.png",
            "segmentation_file": "segmentation0.npy",
            "quaternion": [
                -0.1703329235315323,
                0.06445111334323883,
                -0.8884263038635254,
                0.42687997221946716
            ]
        },
        {
            "id": 1,
            "image_file": "image1.png",
            "segmentation_file": "segmentation1.npy",
            "quaternion": [
                0.33882102370262146,
                -0.3533002734184265,
                0.24369029700756073,
                -0.5794264078140259
            ]
        },
        {
            "id": 2,
            "image_file": "image2.png",
            "segmentation_file": "segmentation2.npy",
            "quaternion": [
                0.19276432693004608,
                0.09966883063316345,
                -0.7412636280059814,
                -0.19215363264083862
            ]
        }, 
    ...
    ]
}
```
Data image preview
![Image Preview](imagePreview.png)

Segmentation preview
![Segmentation Preview](segmentationPreview.png)


<h2 id='references'> References </h2>

----
```python
class Generator():
    def __init__(self, filePath = None, objectFile = None)
```
Generator constructor function, sets up the environment, camera and objects axis.

If <b>objectFile</b> is given then generator will import object file from the given path.

Data and annotation file path is used in the <b>filePath</b> variable, if no file path has been given then it will use the current directory in which the generator is created.

```python
def randomQuaternion(self):
```
```python
def getResolution(self):
```
```python
def cleanFolder(self, folderPath):
```
```python
def loadData(self, filePath, type=None):
```

```python
def findCameraDistance(self, cameraArg, objectArg):
```
```python
def generateData(self, amount = 0):
```
```python
def getBoundingBox(self, object):
```
```python
def setSegmentationNodes(self):
```
```python
def getSegmentation(self):
```
```python
def formatCoordinates(self, id, coordinates):
```
```python
def getBoundingBoxCoordinates(self):
```
