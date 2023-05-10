from abc import ABC, abstractmethod
class DataGenerator(ABC):
    @abstractmethod
    def generateData(self):
        pass

    @abstractmethod
    def getBoundingBox(self):
        pass
    
    @abstractmethod
    def getSegmentation(self):
        pass