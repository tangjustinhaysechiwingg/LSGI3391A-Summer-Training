#!/usr/local/Python-3.6.6/bin/python3

from __future__ import division
import sys
sys.path.append('/home/snd2/qgis-3.6.2/build-gcc-7.2/output/python')
sys.path.append('/home/snd2/qgis-3.6.2/build-gcc-7.2/output/python/plugins')
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtCore import *
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.gui import *
from Functions import ImportRasterLayer,ImportShapeLayer, SetLayerStyle, SetLineLayerStyle, SetWordStyle, PolygonVectorLayer, LineVectorLayer, WordVectorLayer
import timeit
import glob
import os

start = timeit.default_timer()


ProgrammeRoot = '../'
QgisRootPath  = '/home/snd2/qgis-3.6.2/build-gcc-7.2/output/'
os.environ["QGIS_PREFIX_PATH"] = QgisRootPath
os.environ["QT_QPA_FONTDIR"] = '/usr/share/fonts/adobe-source-han-sans-twhk/'

WordPath      = ProgrammeRoot + 'data/iB10000_words_WGS84/'
ShapPath      = ProgrammeRoot + 'data/iB10000_WGS84.gdb/'
TiffPath      = ProgrammeRoot + 'data/OverviewMapRasters/'
TemFile       = ProgrammeRoot + 'data/qgis_composer_template/FloodOverView.qpt'
OutPath       = ProgrammeRoot + 'output/'
InputPath     = ProgrammeRoot + 'input/'  

Polygons = {'HydrPoly' : 'iB10000_HYDRPOLY.shp', # HydrPoly should be the first member of shapefiles
            'BldgPoly' : 'iB10000_BLDGPOLY.shp', # it is used to cover the raster layer.
            'TsptPoly' : 'iB10000_TSPTPOLY.shp',    
            'FaciPoly' : 'iB10000_FACIPOLY.shp',
            'TerrPoly' : 'iB10000_TERRPOLY.shp'}

Lines    = {'ElevLine' : 'iB10000_ELEVLINE.shp',
            'FaciLine' : 'iB10000_FACILINE.shp',
            'HydrLine' : 'iB10000_HYDRLINE.shp',
            'TerrLine' : 'iB10000_TERRLINE.shp',
            'TsptLine' : 'iB10000_TSPTLINE.shp'}

Words  =   {'BDRYANNO' : 'BDRYANNO.shp',
            'ELEVANNO' : 'ELEVANNO.shp',
            'HYDRANNO' : 'HYDRANNO.shp'}

Stations = {'CCH' : 'CCH.tif',
            'CLK' : 'CLK.tif',
            'CLK' : 'CLK.tif',
            'KCT' : 'KLT.tif',
            'KLW' : 'KLW.tif',
            'MWC' : 'MWC.tif',
            'QUB' : 'QUB.tif',
            'SPW' : 'SPW.tif',
            'TAO' : 'TAO.tif',
            'TBT' : 'TBT.tif',
            'TMW' : 'TMW.tif',
            'TPK' : 'TPK.tif',
            'WGL' : 'WGL.tif'}




# Main programme-------------------------------------------------------------------------------------------
# Select input file


InputList     = glob.glob(InputPath + '*')
InputList     = [os.path.basename(f) for f in InputList]
InputDict     = ['%-2s  : %s' % (i+1, InputList[i]) for i in range(len(InputList))]
InputDict     = '\n'.join(InputDict)


while True:
    try:
        InputFile = input('Please choose your intput file:\n' + InputDict + '\n')
        InputFile = InputList[int(InputFile)-1]
        break
    except:
        print('Please enter a number.\n\n')
        time.sleep(0.5)
print("InputFile")
FloodData     = InputFile
OutFile       = FloodData.replace('.txt','')

#Initialize QGIS library -------------------------------------------------
qgs = QgsApplication([], True)
#QgsApplication.setPrefixPath(QgisRootPath, False)
QgsApplication.initQgis()
QgsCoordinateReferenceSystem("EPSG:4326")
QgsProject.instance().removeAllMapLayers()

class RasterLayer():
    
    def __init__(self,Location, FileName, Floodlevel, LayerName = False):
        Floodlevel = float(Floodlevel)
        Floodlevel -= 0.2
        self.InunList = [Floodlevel-i/5 for i in range(15)] # Calculate different flooding level
        self.InunList[0] = Floodlevel + 0.2
        self.ColList = [QColor(69 ,139,0), QColor(95,155,0),
                        QColor(122,172,0), QColor(148,188,0),
                        QColor(175,205,0), QColor(201,221,0),
                        QColor(228,238,0), QColor(255,255,0),
                        QColor(255,218,0), QColor(255,182,0),
                        QColor(255,145,0), QColor(255,109,0),
                        QColor(255,72, 0), QColor(255,36,0),
                        QColor(255,0,0)]
        self.ColList = [QgsColorRampShader.ColorRampItem(self.InunList[14], self.ColList[14], "Above 3.0"),
                        QgsColorRampShader.ColorRampItem(self.InunList[13], self.ColList[13], "2.8 - 3.0"),
                        QgsColorRampShader.ColorRampItem(self.InunList[12], self.ColList[12], "2.6 - 2.8"),
                        QgsColorRampShader.ColorRampItem(self.InunList[11], self.ColList[11], "2.4 - 2.6"),
                        QgsColorRampShader.ColorRampItem(self.InunList[10], self.ColList[10], "2.2 - 2.4"),
                        QgsColorRampShader.ColorRampItem(self.InunList[9], self.ColList[9], "2.0 - 2.2"),
                        QgsColorRampShader.ColorRampItem(self.InunList[8], self.ColList[8], "1.8 - 2.0"),
                        QgsColorRampShader.ColorRampItem(self.InunList[7], self.ColList[7], "1.6 - 1.8"),
                        QgsColorRampShader.ColorRampItem(self.InunList[6], self.ColList[6], "1.4 - 1.6"),
                        QgsColorRampShader.ColorRampItem(self.InunList[5], self.ColList[5], "1.2 - 1.4"),
                        QgsColorRampShader.ColorRampItem(self.InunList[4], self.ColList[4], "1.0 - 1.2"),
                        QgsColorRampShader.ColorRampItem(self.InunList[3], self.ColList[3], "0.8 - 1.0"),
                        QgsColorRampShader.ColorRampItem(self.InunList[2], self.ColList[2], "0.6 - 0.8"),
                        QgsColorRampShader.ColorRampItem(self.InunList[1], self.ColList[1], "0.4 - 0.6"),
                        QgsColorRampShader.ColorRampItem(self.InunList[0], self.ColList[0], "Below 0.4")]
        # self.ColList = [QgsColorRampShader.ColorRampItem(Floodlevel-0.5, self.ColList[0], "Above 0.5")] # single color 
        self.Directory = Location
        self.FileName  = FileName
        if LayerName:
            self.LayerName = LayerName
        else:
            self.LayerName = FileName.split('.')[0]
        
    def AddLayer(self):
        self.InunLayer = ImportRasterLayer('%s/%s' % (self.Directory, self.FileName), self.LayerName)
        QgsProject.instance().addMapLayer(self.InunLayer)
        self.id = self.InunLayer.id()
        
    def SetColorRange(self):
        self.fcn = QgsColorRampShader()
        self.fcn.setColorRampType(QgsColorRampShader.Discrete)
        self.fcn.setColorRampItemList(self.ColList)
        self.shader = QgsRasterShader()
        self.shader.setRasterShaderFunction(self.fcn)
        self.renderer = QgsSingleBandPseudoColorRenderer(self.InunLayer.dataProvider(), 1, self.shader)
        self.InunLayer.setRenderer(self.renderer)
        self.InunLayer.renderer().setOpacity(1) # set transparency
        self.InunLayer.triggerRepaint()



FloodTable = open('%s/%s' % (InputPath, FloodData)).readlines()[1::]
FloodTable = [data.replace('\n','').split() for data in FloodTable]
FloodTable = [[data[0], float(data[1])] for data in FloodTable]

LayerSet = []
LayerSetObj = []

RasterLayers = [RasterLayer(TiffPath, Stations[Data[0]], Data[1]) for Data in FloodTable]
PolyLayers   = [PolygonVectorLayer(ShapPath, Polygons[i], i) for i in Polygons]
LineLayers   = [LineVectorLayer(ShapPath, Lines[i], i) for i in Lines]
WordLayers   = [WordVectorLayer(WordPath, Words[i], i) for i in Words]

RasterLayers[0].LayerName = "Flood depth [m]"qgiC

# LegendLayer  = RasterLayer(TiffPath, Stations["TAO"], 10, "Flood depth [m]") 
# LegendLayer.InunLayer = ImportRasterLayer('%s/%s' % (LegendLayer.Directory, LegendLayer.FileName), LegendLayer.LayerName)
# LegendLayer.SetColorRange()

# Import Raster Layers ...
# QGIS2: Raster layer should import after shapefiles layer.
# !!!ORFDERING IS IMPORTANT
for j in range(len(RasterLayers)):
    RasterLayers[j].AddLayer()
    print('Importing raster layer: %s' % RasterLayers[j].id)
    RasterLayers[j].SetColorRange()
    LayerSet.append(RasterLayers[j].id)
    LayerSetObj.append(RasterLayers[j].InunLayer)
	
# Import Polygon Layers ...   
for i in range(len(PolyLayers)):
    PolyLayers[i].AddLayer()
    print('Importing polygon layer: %s' % PolyLayers[i].id)
    if PolyLayers[i].LayerName == 'HydrPoly':
        PolyLayers[i].SetStyle('#cdf4ff', '#000000', 0.003, 'yes')
        
    else:
        PolyLayers[i].SetStyle('#ffffff', '#000000', 0.003, 'no')
    LayerSet.append(PolyLayers[i].id)
    LayerSetObj.append(PolyLayers[i].PolyLayer)
    
# Import Line Layers ...    
for i in range(len(LineLayers)):
    LineLayers[i].AddLayer()
    print('Importing line layer: %s' % LineLayers[i].id)
    LineLayers[i].SetStyle('#000000', 0.004)
    LayerSet.append(LineLayers[i].id)
    LayerSetObj.append(LineLayers[i].LineLayer)

# Import Word Layers ...  
for i in range(len(WordLayers)):
    WordLayers[i].AddLayer()
    print('Importing Word layer: %s' % WordLayers[i].id)
    WordLayers[i].SetStyle(1.2)
    LayerSet.append(WordLayers[i].id)
    LayerSetObj.append(WordLayers[i].WordLayer)

# Finish Importing Raster layer ...

#LegendLayer  = RasterLayer(TiffPath, Stations["TAO"], 5, "Flood depth [m]")
#LegendLayer.InunLayer = ImportRasterLayer('%s/%s' % (LegendLayer.Directory, LegendLayer.FileName), LegendLayer.LayerName)


print('Generating output ...')
mapSetting=QgsMapSettings()
mapSetting.setLayers(LayerSetObj)
mapSetting.setOutputSize(QSize(297, 210))


comp=QgsLayout(QgsProject.instance())

exportSetting = QgsLayoutExporter.ImageExportSettings()
exportSetting.dpi = 2300
    
# myMapRenderer = QgsMapRenderer()
# myMapRenderer.setLayerSet(LayerSet)
# comp = QgsComposition(myMapRenderer)
# comp.setPlotStyle(QgsComposition.Print)
# comp.setPaperSize(297, 210)
# comp.setPrintResolution(3000)

print('Loading template ...')
# myTemplateFile = file(TemFile, 'rt')
myTemplateFile = open(TemFile, 'rt')
myTemplateContent = myTemplateFile.read()
myTemplateFile.close()
myDocument = QDomDocument()
myDocument.setContent(myTemplateContent, False)
rw_context = QgsReadWriteContext()
#comp.loadFromTemplate(myDocument)
qgisLayoutItems = comp.loadFromTemplate(myDocument, rw_context)
print('Finish loading template ...')

# MainMap = comp.getComposerItemById('MainMap')
# MainMap.setLayerSet(LayerSet)
# MainMap.updateCachedImage()

MainMap=comp.itemById('MainMap')
MainMap.setLayers(LayerSetObj)
comp.refresh()
    

Legend = comp.itemById('Legend')
lyrGroup = QgsLayerTree()
#lyrGroup.addLayer(LegendLayer.InunLayer)
lyrGroup.addLayer(RasterLayers[0].InunLayer)
Legend.model().setRootGroup(lyrGroup)


    
# Legend = comp.getComposerItemById('Legend')
# lyrGroup = QgsLayerTreeGroup()
# lyrGroup.addLayer(LegendLayer.InunLayer)
# Legend.modelV2().setRootGroup(lyrGroup)

    
    
# image = comp.printPageAsRaster(0)
print('Saving image ...')
# image.save('%s/%s.png' % (OutPath, OutFile),'png')
exporter = QgsLayoutExporter(comp)
exportResult = exporter.exportToImage('%s/%s.png' % (OutPath, OutFile), exportSetting)
print('Done!')
print('%s/%s.png' % (OutPath, OutFile))
print(exportResult)

# DEBUG QgsProject.instance().write('/home/snd2/test/my_new_qgis_project2.qgs')

QgsProject.instance().clear()
qgs.exitQgis()
qgs.exit()

stop = timeit.default_timer()
print('Run time :%1s seconds.' % (stop - start))  
#sys.exit()
