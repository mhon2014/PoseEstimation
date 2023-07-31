# 3DPoseEstimation
[Description](#description)

[Getting Started](#gettingStarted)

[Data Preview](#dataDreview)

[References](#references)

<h2 id='description'> Description </h2>

---
This repository contains Python code to interface with blender to generate synthetic data. These data are images that include annotation of segmentation and object quaternion. Random rotation and camera distances are currently used for data generation, other variations may be included later for future addition.

<h2 id='gettingStarted'> Getting Started </h2>

---
To get started clone this repo into you desired folder. Import the class as shown below.

```python
from BlenderDataGenerator import SatteliteData

generator = SatteliteData.Generator()

```
<h2 id='dataDreview'> Data Preview </h2>

---
```json

```

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
