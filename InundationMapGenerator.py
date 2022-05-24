#!/usr/local/Python-3.6.6/bin/python3

from __future__ import division
import sys
sys.path.append('/home/snd2/qgis-3.6.2/build-gcc-7.2/output/python')
sys.path.append('/home/snd2/qgis-3.6.2/build-gcc-7.2/output/python/plugins')
from Functions import *
import qgis
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtXml import QDomDocument
from qgis.gui import *
import os
import processing
from processing.core.Processing import Processing
from math import pi
import glob

from qgis.analysis import QgsNativeAlgorithms
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

# ######## CHECK HOW TO USE GDAL
# processing.algorithmHelp("gdal:translate")
# ######## CHECK HOW TO USE GDAL

# Config-------------------------------------------------------------------------------------------
# Path of the programme ==================================
ProgrammeRoot = '../'

# Path of QGIS ===========================================
QgisRootPath  = '/home/snd2/qgis-3.6.2/build-gcc-7.2/output/'
os.environ["QGIS_PREFIX_PATH"] = QgisRootPath
os.environ["QT_QPA_FONTDIR"] = '/usr/share/fonts/adobe-source-han-sans-twhk/'

# Paths for raw data files ===============================
LiDARPAth     = ProgrammeRoot + 'data/DEM_mCD_mod/'         # directory of xyz files [DEM].
#LiDARPAth     = ProgrammeRoot + 'data/DSM_mCD_mod/'        # directory of xyz files [DSM].
WordPath      = ProgrammeRoot + 'data/iB10000_words_WGS84/' # directory of map labels files.
ShapPath      = ProgrammeRoot + 'data/iB10000_WGS84.gdb/'   # directory of map polygons and lines files.
#TemFile       =  ProgrammeRoot + 'data/qgis_composer_template/OverView_Template_Updated_version2.qpt'
TemFile       =  ProgrammeRoot + 'data/qgis_composer_template/OverView_Template_Updated_linux.qpt'
                                                            # directory of QGIS template files.              
															
OUTPUT_DPI=1000

Polygons = {'CovePoly' : 'MAP_COVEPOLY.shp',     # Order of polygons is important
            'HydrPoly' : 'iB10000_HYDRPOLY.shp',
            'BldgPoly' : 'iB10000_BLDGPOLY.shp',
            'TsptPoly' : 'iB10000_TSPTPOLY.shp',    
            'FaciPoly' : 'iB10000_FACIPOLY.shp',
            'TerrPoly' : 'iB10000_TERRPOLY.shp'}

Lines    = {'ElevLine' : 'iB10000_ELEVLINE.shp',
            'FaciLine' : 'iB10000_FACILINE.shp',
            'HydrLine' : 'iB10000_HYDRLINE.shp',
            'TerrLine' : 'iB10000_TERRLINE.shp',
            'TsptLine' : 'iB10000_TSPTLINE.shp'}

Words  =   {'BDRYANNO' : 'BDRYANNO.shp',
            'BLDGANNO' : 'BLDGANNO.shp',
            'ELEVANNO' : 'ELEVANNO.shp',
            'FACIANNO' : 'FACIANNO.shp',
            'HYDRANNO' : 'HYDRANNO.shp',
            'TSPTANNO' : 'TSPTANNO.shp',
            'PLACANNO' : 'PLACANNO.shp'}

# Paths for processing files =============================
ShpPath       = ProgrammeRoot + '/processing/xyz_to_shp/'  # xyz  ---> shp
TifPath       = ProgrammeRoot + '/processing/shp_to_tif/'  # shp  ---> tif
MergedPath    = ProgrammeRoot + '/processing/merge_tif/'   # tifs ---> tif
TranPath      = ProgrammeRoot + '/processing/translate/'   # tif  ---> tif with nodata value
FillPath      = ProgrammeRoot + '/processing/fill_nodata/' # tif  ---> tif with nodata value

# Path of output file ====================================
OutPath       = ProgrammeRoot + 'output/'

# Path of input file ====================================
InputPath     = ProgrammeRoot + 'input/'











# Main programme-------------------------------------------------------------------------------------------
# Auto Select input file

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
        time.sleep(0.5)qgis

InputFile     = InputPath + InputFile

# Classes


class RasterLayer():
    
    def __init__(self,Location, FileName, InunLevel, maptype):
        self.Directory = Location
        self.FileName  = FileName
        self.LayerName = FileName.split('.')[0]
        
        if maptype == 'inundation':
            self.Opacity     = 0.55
            InunLevel        = InunLevel.replace('(','').replace(')','').split('-')
            minLv,maxLv      = [int(item) for item in InunLevel]
            factor           = (maxLv - minLv) / 8
            self.InunList    = [minLv + i*factor for i in range(9)]
            # blue to Red
            ColList          = [QColor( 94,  0,255), QColor(  0,119,255), QColor(  0,179,255),
                                QColor(  0,255,217), QColor(  0,255, 68), QColor(251,255,  0),
                                QColor(225,191,  0), QColor(244,138, 67), QColor(255,  0,  0)]
            Words            = ['%.2f - %.2f' % (self.InunList[i-1], self.InunList[i]) if i > 0 else 'Below  %.2f' % self.InunList[i] for i in range(9)]
            self.ColList     = [QgsColorRampShader.ColorRampItem(self.InunList[i], ColList[i], Words[i]) for i in range(9)]
            self.LayerName   = 'Meters above chart datum'
        
        elif maptype == 'floodextent':
            self.Opacity     = 1
            Floodlevel       = float(InunLevel)
            Floodlevel      -= 0.2
            self.InunList    = [Floodlevel-i/5 for i in range(15)]
            self.InunList[0] = Floodlevel +0.2
            self.InunList.reverse()
            
            # Green to red
            self.ColList     = [QColor( 69,139,  0), QColor( 95,155,  0), QColor(122,172,  0),
                                QColor(148,188,  0), QColor(175,205,  0), QColor(201,221,  0),
                                QColor(228,238,  0), QColor(255,255,  0), QColor(255,218,  0),
                                QColor(255,182,  0), QColor(255,145,  0), QColor(255,109,  0),
                                QColor(255, 72,  0), QColor(255, 36,  0), QColor(255,  0,  0)]
            '''
            # Colour scale used in WWIII (blue > red > putple > black)
            self.ColList     = [QColor(  0, 51,225), QColor(  0,139,225), QColor(  0,223,223),
                                QColor(  0,207, 48), QColor(226,255, 76), QColor(255,182,  0),
                                QColor(217,  0,  3), QColor(255,  0,139), QColor(230, 84,255),
                                QColor(150, 58,255), QColor(197,159,255), QColor(255,213,255),
                                QColor(242,234,255), QColor(183,187,230), QColor(  0,  0,  0)]
            '''
            
            self.ColList.reverse()
            Words            = ["Above 3.0" if i == 0 else 'Below 0.4' if i == 14 else '%3.1f - %3.1f' % (3 - i/5, 3 - i/5 + 1/5) for i in range(15)]
            self.ColList     = [QgsColorRampShader.ColorRampItem(self.InunList[i], self.ColList[i], Words[i]) for i in range(15)]
            self.LayerName   = 'Flooding level [m]'
            
        
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
        self.InunLayer.renderer().setOpacity(self.Opacity) # set transparency
        self.InunLayer.triggerRepaint()

# Functions to plot Maps ======================================

def PrepareRasterLayer(scale, cooridinate):
    '''
    This function used to prepare the raster layers from raw data by given
    coordinate of the center of map and the scale of map.
    '''

    Boundary = WGS84_to_HK1980(cooridinate)
    #LiDARList = SelectFile2(Boundary) # DSM
    LiDARList = SelectFile(Boundary) # DEM

    print('Checking if file exist ...')
    MissFile = []
    for File in LiDARList:
            print(File)
            if not os.path.isfile(LiDARPAth+File):  # skip this part if file already exist
                    MissFile.append(File)
    LiDARList = [File for File in LiDARList if File not in MissFile]

    # Convert xyz file to shape file for merging ------------------------------


    print('Converting xyz to shp file ...')
    for XYZFile in LiDARList:
        ShpFile = ShpPath + XYZFile.replace('xyz','shp')
        TifFile = TifPath + XYZFile.replace('xyz','tif')
        if os.path.isfile(ShpFile) :  # skip this part if file already exist
            continue
        elif os.path.isfile(TifFile):  # skip this part if file already exist
            continue
        else:
            #XYZtoSHP(XYZFile, LiDARPAth, ShpPath, epsg = 2326) # if data corrdinate system is HK1980 grid system
            XYZtoSHP(XYZFile, LiDARPAth, ShpPath) # WGS84 

    QgsProject.instance().removeAllMapLayers()
    print('Conversion completed.')
    #--------------------------------------------------------------------------
    
    #---Convert shp file to tif file for merging ------------------------------
    print('Convert shp to tif ...')
    Processing.initialize()
    ShpList = []
    TifList = []
    for File in LiDARList:
            ShpFile = File.replace('xyz','shp')
            TifFile = TifPath + ShpFile.replace('.shp','.tif')
            
            if not os.path.isfile(TifFile):  # skip this part if file already exist
                    print('   Converting' + ShpFile + ' to tif ...')
                    Area = GetShpBoundary(ShpPath, ShpFile)
                    processing.run("gdal:rasterize",
                                   {"INPUT":ShpPath+ShpFile,
                                   "FIELD":"height",
                                   "UNITS":1,
                                   "WIDTH":5e-06,
                                   "HEIGHT":5e-06,
                                   "EXTENT":Area,
                                   "NO_DATA":0,
                                   "DATA_TYPE":6,    #  5: Int32, 6:Float32
                                   "INVERT":0,
                                   "OUTPUT":TifFile})
                    print('   done')
            TifList.append(TifFile)
            ShpList.append(ShpFile)
    #--------------------------------------------------------------------------
    print('Merge tif ....')
    MergedFile = MergedPath + ProjectName.replace(' ','_')+'_merged.tif'
    if not os.path.isfile(MergedFile): # skip this part if file already exist
            # processing.runalg("gdalogr:merge",
                              # ';'.join(TifList),
                              # False,False,-9999,5,MergedFile)
            processing.run("gdal:merge",
                                    {"INPUT":TifList,
                                     "PCT": False,
									 "NODATA_INPUT": 0,
									 "NODATA_OUTPUT" : -9999,
                                    "SEPARATE": False,
                                    "DATA_TYPE": 6,
                                    "OUTPUT":MergedFile})
    #--------------------------------------------------------------------------
    print('Translating raster layer ...')
    Area = ','.join([str(cooridinate[1]),str(cooridinate[3]),str(cooridinate[0]),str(cooridinate[2])])
    TranFile = TranPath + ProjectName.replace(' ','_')+'_translated.tif'
    if not os.path.isfile(TranFile):  # skip this part if file already exist
        processing.run("gdal:translate",{"INPUT":MergedFile,
                                     "NODATA": -9999,
                                    "DATA_TYPE": 6,    #  5: Int32, 6:Float32
                                    "OUTPUT": TranFile})
                                    
    #--------------------------------------------------------------------------
    print('Filling nodata values to translated tif ...')
    FillFile = FillPath + ProjectName.replace(' ','_')+'_fill.tif'
    if not os.path.isfile(FillFile):
        processing.run('gdal:fillnodata', {
            "INPUT":TranFile,
            "DISTANCE": 100,    #Maximum distance (in pixels) to search out for values to interpolate
            "ITERATIONS": 0,    #Number of smoothing iterations to run after the interpolation
            "BAND": 1,
            "NO_MASK": False,
            "MASK_LAYER": None,
            "OUTPUT": FillFile
            })
    
    

	#--------------------------------------------------------------------------
	#Added on 20200709: Assign the nodata value to fix the fillnodata problem
    print('Translating raster layer again...')
    Area = ','.join([str(cooridinate[1]),str(cooridinate[3]),str(cooridinate[0]),str(cooridinate[2])])
    TranFile = FillPath + ProjectName.replace(' ','_')+'_filled.tif'
    if not os.path.isfile(TranFile):  # skip this part if file already exist
        processing.run("gdal:translate",{"INPUT":FillFile,
                                     "NODATA": -9999,
                                    "DATA_TYPE": 6,    #  5: Int32, 6:Float32
                                    "OUTPUT": TranFile})
									
    head, tail = os.path.split(TranFile)
    return((head, tail))



def PlotMap(ProjectName, center_lat, center_lon, scale, InunRange, maptype):
    print('%s map : %s'%(maptype.title(), ProjectName))

    cooridinate = [Distance_to_LatLon(center_lat, center_lon,1300*scale,pi)[1],
               Distance_to_LatLon(center_lat, center_lon,1300*scale*18/13,3*pi/2)[0],
               Distance_to_LatLon(center_lat, center_lon,1300*scale,0)[1],
               Distance_to_LatLon(center_lat, center_lon,1300*scale*18/13,pi/2)[0]]

    if maptype == 'floodextent':
        Title                 = 'Flood extent map %s\nFlooding level : %.2f [mcd]' % (ProjectName, float(InunRange))
        OutPutFile            = OutPath + ProjectName.replace(' ','_') + '_floodextent'
    if maptype == 'inundation':
        Title                 = 'Inundation map\n%s %s [mcd]' % (ProjectName, InunRange)
        OutPutFile            = OutPath + ProjectName.replace(' ','_') + '_inundation'

    
    RasterPath,RasterName = PrepareRasterLayer(scale, cooridinate)    

    QgsProject.instance().removeAllMapLayers()
    global PolyLayers
    PolyLayers   = [PolygonVectorLayer(ShapPath, Polygons[i], i) for i in Polygons]
    PolyOrders   = [1,2,3,5,4,0]
    PolyLayers   = [PolyLayers[i] for i in PolyOrders]
    LineLayers   = [LineVectorLayer(ShapPath, Lines[i], i) for i in Lines]
    WordLayers   = [WordVectorLayer(WordPath, Words[i], i) for i in Words]
    LayerSet = []
    LayerSet2 = []
    LayerSetObj = []
    LayerSetObj2 = []

    # Import Line Layers ...    
    for i in range(len(LineLayers)):
        if PolyLayers[i].LayerName == 'HydrLine':
            LineLayers[i].AddLayer()
            LineLayers[i].SetStyle('#000000', 0.004)
            LayerSet.append(LineLayers[i].id)
            LayerSet2.append(LineLayers[i].id)
            LayerSetObj.append(LineLayers[i].LineLayer)
            LayerSetObj2.append(LineLayers[i].LineLayer)

    
    # Import Polygon Layers ...
    for i in range(len(PolyLayers)):
        PolyLayers[i].AddLayer()
        
        if PolyLayers[i].LayerName == 'HydrPoly':
                                    # LBlue     Black   PenWidth fill
            PolyLayers[i].SetStyle('#cdf4ff', '#000000', 0.003, 'yes')
        elif PolyLayers[i].LayerName == 'CovePoly': # this polygon layer used to cover the location where
                                                    # the interpolating result is weird due to data missing 
                                    # White     White   PenWidth fill
            PolyLayers[i].SetStyle('#ffffff', '#ffffff', 0.000, 'yes')
        else:
                                    # White     Black   PenWidth fill
            PolyLayers[i].SetStyle('#ffffff', '#000000', 0.003, 'no')
        LayerSet.append(PolyLayers[i].id)
        LayerSet2.append(PolyLayers[i].id)
        LayerSetObj.append(PolyLayers[i].PolyLayer)
        LayerSetObj2.append(PolyLayers[i].PolyLayer)
        
    # Import Line Layers ...    
    for i in range(len(LineLayers)):
        if PolyLayers[i].LayerName != 'HydrLine':
            LineLayers[i].AddLayer()
            #print('Importing line layer: %s' % LineLayers[i].id)
            LineLayers[i].SetStyle('#000000', 0.004)
            LayerSet.append(LineLayers[i].id)
            LayerSet2.append(LineLayers[i].id)
            LayerSetObj.append(LineLayers[i].LineLayer)
            LayerSetObj2.append(LineLayers[i].LineLayer)

    # Import Word Layers ...  
    for i in range(len(WordLayers)):
        WordLayers[i].AddLayer()
        #print('Importing Word layer: %s' % WordLayers[i].id)
        #WordLayers[i].SetStyle(2)
        WordLayers[i].SetStyle2(scale)
        LayerSet.append(WordLayers[i].id)
        LayerSetObj.append(WordLayers[i].WordLayer)

    # Import Raster Layers ...
    # Raster layer should import after shapefiles layer.
    Raster = RasterLayer(RasterPath, RasterName,InunRange, maptype)
    Raster.AddLayer()
    Raster.SetColorRange()
    LayerSet.append(Raster.id)
    LayerSetObj.append(Raster.InunLayer)
    # Finish Importing Raster layer ...

    # Generate output
    print('Generating output ...')
    # myMapRenderer = QgsMapRenderer()    #QGIS2
    
    mapRectangle = QgsRectangle(cooridinate[1],cooridinate[0],cooridinate[3],cooridinate[2])
    
    mapSetting=QgsMapSettings()
    mapSetting.setLayers(LayerSetObj)
    mapSetting.setExtent(mapRectangle)
    mapSetting.setOutputSize(QSize(297, 210))
    mapSetting.setOutputDpi(OUTPUT_DPI)
    myMapRenderer = QgsMapRendererParallelJob(mapSetting)
    
    comp=QgsLayout(QgsProject.instance())
    
    # myMapRenderer.setLayerSet(LayerSet)#QGIS2
    # myMapRenderer.setExtent(mapRectangle)#QGIS2
    # comp = QgsComposition(myMapRenderer)#QGIS2
    # comp.setPlotStyle(QgsComposition.Print)#QGIS2

    print('Loading template ...') # loading template file
    myTemplateFile = open(TemFile, 'rt')
    myTemplateContent = myTemplateFile.read()
    myTemplateFile.close()
    myDocument = QDomDocument()
    myDocument.setContent(myTemplateContent, False)
    rw_context = QgsReadWriteContext()
    #comp.loadFromTemplate(myDocument)#QGIS2
    qgisLayoutItems = comp.loadFromTemplate(myDocument, rw_context)
    print('Finished loading template.')

    #MainMap = comp.getComposerItemById('MainMap')#QGIS2
    #MainMap.setLayerSet(LayerSet)#QGIS2
    MainMap=comp.itemById('MainMap')
    MainMap.setLayers(LayerSetObj)
    #MainMap.setNewExtent(mapRectangle)#QGIS2
    MainMap.setExtent(mapRectangle)
    #MainMap.updateCachedImage()#QGIS2
    comp.refresh()
    MainMap.setScale(10000*scale)
    #MainMap.setNewScale(10000*scale)#QGIS2
    #MainMap.updateCachedImage()#QGIS2
    comp.refresh()


    MinMap=comp.itemById('MinMap')
    MinMap.setExtent(mapRectangle)
    MinMap.setScale(200000*scale)
    MinMap.setLayers(LayerSetObj2)
    comp.refresh()

    MapTitle =comp.itemById('Title')
    MapTitle.setText(Title)

    Legend = comp.itemById('Legend')
    # lyrGroup = QgsLayerTreeGroup()#QGIS2
    lyrGroup = QgsLayerTree()
    lyrGroup.addLayer(Raster.InunLayer)
    Legend.model().setRootGroup(lyrGroup)

    exportSetting = QgsLayoutExporter.PdfExportSettings()
    exportSetting.dpi = OUTPUT_DPI
    
    exporter = QgsLayoutExporter(comp)
    exporter.exportToPdf('%s.pdf' % (OutPutFile), exportSetting)

    #set paper to A4 size 297 x 210
    #QGIS2 comp.setPaperSize(297, 210)
    #QGIS2 comp.setPrintResolution(500)
    
    # DEBUG QgsProject.instance().write('/home/snd2/test/my_new_qgis_project.qgs')

    #QGIS2 printer = QPrinter()
    #QGIS2 printer.setOutputFormat(QPrinter.PdfFormat)
    #QGIS2 printer.setOutputFileName('%s.pdf' % (OutPutFile))
    #QGIS2 printer.setPaperSize(QSizeF(comp.paperWidth(), comp.paperHeight()), QPrinter.Millimeter)
    #QGIS2 printer.setFullPage(True)
    #QGIS2 printer.setColorMode(QPrinter.Color)
    #QGIS2 printer.setResolution(comp.printResolution())
    #QGIS2 pdfPainter = QPainter(printer)
    #QGIS2 paperRectMM = printer.pageRect(QPrinter.Millimeter)
    #QGIS2 paperRectPixel = printer.pageRect(QPrinter.DevicePixel)
    #QGIS2 comp.render(pdfPainter, paperRectPixel, paperRectMM)
    #QGIS2 pdfPainter.end()

    QgsProject.instance().removeAllMapLayers()
    return None

# Main Programme? ==========================================================================

#Initialize QGIS library -------------------------------------------------
qgs = QgsApplication([], True)
#QgsApplication.setPrefixPath(QgisRootPath, False)
QgsApplication.initQgis()
QgsCoordinateReferenceSystem("EPSG:4326")


with open(InputFile, 'r') as File:
    next(File)
    for line in File:
        line        = line.split(',')
        line        = [item.strip() for item in line]
        ProjectName = line[0]
        center_lat  = float(line[1])
        center_lon  = float(line[2])
        scale       = float(line[3])
        InunRange   = line[4]
        maptype     = line[5]
        
        if ProjectName[0] == '#': # Won't Plot if line start with "#"
            print('Skip plotting map for %s' % ProjectName.strip('#'))
            continue
            
        if maptype != 'inundation' and maptype != 'floodextent':
            print('Map type should be either inundation or floodextent.')
            break

        Data = PlotMap(ProjectName, center_lat, center_lon, scale, InunRange, maptype)
        #QgsProject.instance().clear()
        #QgsProject.instance()




# Exit Qgis ===============================================================================
QgsProject.instance().clear()
qgs.exitQgis()
qgs.exit()
