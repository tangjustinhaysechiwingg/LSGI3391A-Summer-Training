from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt import QtGui

from qgis.utils import iface
from qgis.gui import *
from osgeo import osr
import math
import sys
sys.path.append('/home/snd2/qgis-3.6.2/build-gcc-7.2/output/python')
sys.path.append('/home/snd2/qgis-3.6.2/build-gcc-7.2/output/python/plugins')
import processing
import os
from math import sin, cos, sqrt, atan2, tan, atan, pi
from processing.core.Processing import Processing

'''
def CalInunList(InunRange):
    return([InunRange-i/4 for i in range(9)])

'''
def CalInunListDSD(InunRange):
    InunRange = InunRange - 0.2
    InunList = [InunRange-i/5 for i in range(15)]
    InunList[0] = InunRange +0.2
    return(InunList)


def roundup(x):
    return int(math.ceil(x / 1000)) * 1000

def rounddown(x):
    return int(round((x - 0.5) / 1000) * 1000)


def HK80_WGS84(lon, lat): # convert cooridinate system from HK1980 to WGS84

    old_crs = osr.SpatialReference()
    old_crs.ImportFromEPSG(2326) # EPSG 2326 :  HK1980
    new_crs = osr.SpatialReference()
    new_crs.ImportFromEPSG(4326) # EPSG 4326 :  WGS 84
    transform = osr.CoordinateTransformation(old_crs,new_crs)
    Point = transform.TransformPoint(lon,lat)[0:2]
    return(Point)
    
def WGS84_to_HK1980(cooridinate):

    O_point1 = [cooridinate[1], cooridinate[2]]
    O_point2 = [cooridinate[3], cooridinate[0]]
    old_crs = osr.SpatialReference()
    old_crs.ImportFromEPSG(4326)
    new_crs = osr.SpatialReference()
    new_crs.ImportFromEPSG(2326)
    transform = osr.CoordinateTransformation(old_crs,new_crs)
    Point1 = transform.TransformPoint(O_point1[0], O_point1[1])[0:2]
    Point2 = transform.TransformPoint(O_point2[0], O_point2[1])[0:2]
    Boundary_N = roundup(Point1[1])
    Boundary_E = roundup(Point2[0])
    Boundary_S = rounddown(Point2[1])
    Boundary_W = rounddown(Point1[0])
    return([Boundary_N,Boundary_E,Boundary_S,Boundary_W])

def SelectFile(Boundary): # select file used to plot Inundation map
    
    Boundary_N = int(str(Boundary[0])[0:3])
    Boundary_E = int(str(Boundary[1])[0:3])
    Boundary_S = int(str(Boundary[2])[0:3]) - 1
    Boundary_W = int(str(Boundary[3])[0:3]) - 1
    Hori = range(Boundary_W, Boundary_E)
    Vert = range(Boundary_S, Boundary_N)
    FileList = []
    for N in Vert:
        for E in Hori:
            FileList.append('e'+str(E)+'n'+str(N)+'_DEM_mod.xyz')
    return(FileList)
    
'''
def SelectFile2(Boundary): # use DSM Data
    
    Boundary_N = int(str(Boundary[0])[0:3])
    Boundary_E = int(str(Boundary[1])[0:3])
    Boundary_S = int(str(Boundary[2])[0:3])
    Boundary_W = int(str(Boundary[3])[0:3])
    Hori = range(Boundary_W, Boundary_E)
    Vert = range(Boundary_S, Boundary_N)
    FileList = []
    for N in Vert:
        for E in Hori:
            FileList.append('e'+str(E)+'n'+str(N)+'_DSM_mod.xyz')
    return(FileList)
'''

def GetShpBoundary(ShpPath, ShpFile): # Get the bounding box of the shapefile

    layer = QgsVectorLayer(ShpPath + ShpFile, 'ShapeLayer', 'ogr')
    ext = layer.extent()
    (xmin, xmax, ymin, ymax) = (ext.xMinimum(), ext.xMaximum(), ext.yMinimum(), ext.yMaximum())
    bbox = [xmin, xmax, ymin, ymax]
    bbox = ','.join([str(item) for item in bbox])

    return(bbox)

def XYZtoSHP(XYZFile, XYZPath, ShpPath, epsg = 4326): # epsg defalt setting WGS84

    ShpFile = ShpPath + XYZFile.replace('.xyz','.shp')
    
    # check if shp file exist
    if not os.path.isfile(ShpFile):
        FileFullPath = XYZPath + XYZFile
        # Import a xyz data to qgis
        uri = "file://" + FileFullPath + "?delimiter=%s&crs=EPSG:%s&xField=%s&yField=%s" % (" ",         # delimiter of the file:
                                                                                        epsg,        # cooridinate system
                                                                                        "longitude", # header of the x cooridinate of the delimited file
                                                                                        "latitude")  # header of the y cooridinate of the delimited file
        print('   Importing data from '+ XYZFile+' ...')
        layer = QgsVectorLayer(uri, XYZFile.replace('.xyz',''), "delimitedtext")
        #QgsMapLayerRegistry.instance().addMapLayer(layer)    #QGIS2
        QgsProject.instance().addMapLayer(layer)
        if not layer.isValid(): # check validation for the imported data.
            print('   Cannot import ' + XYZPath + XYZFile)
        else:
            print('   Converting '+XYZFile+' to shp ...')
            layer.setCrs(QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId))
            fields = layer.fields()
            field_names = [field.name() for field in fields]
            _writer = QgsVectorFileWriter.writeAsVectorFormat(layer, ShpFile,"utf-8",QgsCoordinateReferenceSystem(),"ESRI Shapefile")
            print('   done')
            QgsProject.instance().removeAllMapLayers()
            

def ImportRasterLayer(raster, LayerName = 'RasterLayer'):
    fileInfo = QFileInfo(raster)
    path = fileInfo.filePath()
    baseName = LayerName
    layer = QgsRasterLayer(path, baseName)
    QgsProject.instance().addMapLayer(layer)
    if layer.isValid() is False:
        print("   Unable to read basename and file path - Your string is probably invalid")
    return(layer)

def ImportShapeLayer(shp, LayerName):
    layer = QgsVectorLayer(shp, LayerName, "ogr")
    if layer.isValid() is False:
        print("   Unable to read basename and file path - Your string is probably invalid")
    return(layer)
'''
def SetLayerColourRGB(layer, R, G, B):
    symbols = layer.renderer().symbols()
    symbol = symbols[0]
    symbol.setColor(QColor.fromRgb(R, G, B))
'''

def SetLayerStyle(layer, fill_color, border_color, border, fill):
    mySymbol1=QgsFillSymbol.createSimple({'color':str(fill_color),
                                                'color_border':str(border_color),
                                                'width_border':str(border),
                                                'style':str(fill)})
    renderer = layer.renderer()
    renderer.setSymbol(mySymbol1)
    layer.triggerRepaint()
    
def SetLineLayerStyle(layer, color, border):
    symbols = layer.renderer().symbols(QgsRenderContext())
    symbol = symbols[0]
    symbol.setWidth(border)
    symbol.setColor(QColor.fromRgb(0 ,0 ,0))
    layer.triggerRepaint()


def SetWordStyle(layer, size):
    mySymbol1=QgsFillSymbol.createSimple({'color':'0,0,0,0',
                                            'color_border':'0,0,0,0',
                                            'style':'no'})
    layer.setProviderEncoding(u'Big5')										
							
    pc=QgsPropertyCollection('mycol')
    prop=QgsProperty()
    prop.setExpressionString(str(size))
    pc.setProperty(QgsPalLayerSettings.Size ,prop)
	
    palyr = QgsPalLayerSettings()
    palyr.setDataDefinedProperties(pc)
    palyr.enabled = True
    palyr.fieldName = 'TextString'
    palyr.placement = QgsPalLayerSettings.OverPoint
	
	
    layer.setLabelsEnabled(True)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(palyr))
    renderer = layer.renderer()
    renderer.setSymbol(mySymbol1)
    layer.triggerRepaint()

    
def SetWordStyle2(layer, scale):
    # https://gis.stackexchange.com/questions/70111/how-to-obtain-rotation-field-name-defined-in-the-labels-data-defined-section-i
    mySymbol1=QgsFillSymbol.createSimple({'color':'0,0,0,0',
                                            'color_border':'0,0,0,0',
                                            'style':'no'})
                                            
    layer.setProviderEncoding(u'Big5')
	
    prop=QgsProperty()
    prop.setField("")
    pc=QgsPropertyCollection('mycol')
    pc.setProperty(QgsPalLayerSettings.FontCase ,prop)
    pc.setProperty(QgsPalLayerSettings.Bold ,prop)
    pc.setProperty(QgsPalLayerSettings.Rotation ,prop)
                    
    prop=QgsProperty()
    prop.setExpressionString('"FontSize" * %s / 10' % scale)
    pc.setProperty(QgsPalLayerSettings.Size ,prop)
    
    prop=QgsProperty()
    prop.setField('Italic')
    pc.setProperty(QgsPalLayerSettings.Italic ,prop)
    
    prop=QgsProperty()
    prop.setField('Underline')
    pc.setProperty(QgsPalLayerSettings.Underline ,prop)
    
    
    # Set TextString
    palyr = QgsPalLayerSettings()
    palyr.setDataDefinedProperties(pc)
    palyr.enabled = True
    palyr.fieldName = 'TextString'
    palyr.placement = QgsPalLayerSettings.OverPoint
       
    layer.setLabelsEnabled(True)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(palyr))
    renderer = layer.renderer()
    renderer.setSymbol(mySymbol1)
    layer.triggerRepaint()

def Distance_to_LatLon( lat1, lon1, distance, Azimuth): # calculate position cooridinate by displacement
    Alpha1 = Azimuth #rad
    lat1 = lat1*pi/180 #rad
    lon1 = lon1*pi/180 #rad
    dis = distance
    a = 6378137      # semi major axes of earth 
    b = 6356752.3142 # semi minor axes of earth
    f = (a-b)/a
    sinAlpha1 = sin(Alpha1)
    cosAlpha1 = cos(Alpha1)
    tanU1 = (1-f)*tan(lat1)
    cosU1 = 1/sqrt(1+tanU1**2)
    sinU1 = cosU1*tanU1
    sigma1 = atan(tanU1/cosAlpha1)
    sinAlpha = cosU1*sinAlpha1
    cosSqAlpha = 1 - sinAlpha*sinAlpha
    uSq = cosSqAlpha*(a**2-b**2)/b**2
    A = 1 + (uSq/16384)*(4096+uSq*(-768+uSq*(320-175*uSq)))
    B = uSq/1024*(256+uSq*(-128+uSq*(74-47*uSq)))
    Sigma = dis/(b*A)
    sigmaP = 2*pi
    cos2SigmaM = cos(2*sigma1+Sigma)
    sinSigma = sin(Sigma)
    cosSigma = cos(Sigma)
    while abs(Sigma - sigmaP) > 1E-19:
            cos2SigmaM = cos(2*sigma1+Sigma)
            sinSigma = sin(Sigma)
            cosSigma = cos(Sigma)
            deltaSigma = B*sinSigma*(cos2SigmaM+B/4*(cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)-B/6*cos2SigmaM*(-3+4*sinSigma*sinSigma)*(-3+4*cos2SigmaM*cos2SigmaM)))
            sigmaP = Sigma
            sigma = dis/(b*A)+deltaSigma
    tmp = sinU1*sinSigma - cosU1*cosSigma*cosAlpha1
    lat2 = atan2(sinU1*cosSigma + cosU1*sinSigma*cosAlpha1, (1-f)*sqrt(sinAlpha*sinAlpha + tmp*tmp))
    lambd = atan2(sinSigma*sinAlpha1, cosU1*cosSigma - sinU1*sinSigma*cosAlpha1)
    C = f/16*cosSqAlpha*(4+f*(4-3*cosSqAlpha))
    L = lambd - (1-C) * f * sinAlpha * (sigma + C*sinSigma*(cos2SigmaM+C*cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)))
    dat = [(L+lon1)*180/pi,lat2*180/pi]
    return(dat)

class PolygonVectorLayer():
    
    def __init__(self,Location, FileName, LayerName):
        self.Directory = Location
        self.FileName  = FileName
        self.LayerName = LayerName
        
    def AddLayer(self):
        self.PolyLayer = ImportShapeLayer('%s%s' % (self.Directory, self.FileName), self.LayerName)
        QgsProject.instance().addMapLayer(self.PolyLayer)
        self.id = self.PolyLayer.id()
        
    def SetStyle(self, fillcolor, pencolor, penwidth, fill):
        SetLayerStyle(self.PolyLayer, fillcolor, pencolor, penwidth, fill)
        
class LineVectorLayer():
    
    def __init__(self,Location, FileName, LayerName):
        self.Directory = Location
        self.FileName  = FileName
        self.LayerName = LayerName
        
    def AddLayer(self):
        self.LineLayer = ImportShapeLayer('%s%s' % (self.Directory, self.FileName), self.LayerName)
        QgsProject.instance().addMapLayer(self.LineLayer)
        self.id = self.LineLayer.id()
        
    def SetStyle(self, pencolor, penwidth):
        SetLineLayerStyle(self.LineLayer, pencolor, penwidth)

class WordVectorLayer():
    
    def __init__(self,Location, FileName, LayerName):
        self.Directory = Location
        self.FileName  = FileName
        self.LayerName = LayerName
        
    def AddLayer(self):
        self.WordLayer = ImportShapeLayer('%s%s' % (self.Directory, self.FileName), self.LayerName)
        QgsProject.instance().addMapLayer(self.WordLayer)
        self.id = self.WordLayer.id()
        
    def SetStyle(self, size):
        SetWordStyle(self.WordLayer, size)

    def SetStyle2(self, scale):
        SetWordStyle2(self.WordLayer, scale)
