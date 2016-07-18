# -*- coding: utf-8 -*-

"""
- Tipo de script:
Define a drenagem com base nas nascentes e no MDT

- Data:
17/07/2010

- Autor:
Gustavo S. F. Molleri (gustavo.molleri@gmail.com)
"""

#------------------------------------------------------------

# Modulos utilizados
import os, sys

# from numpy import *
import numpy

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo import gdal_array
from osgeo import gdalconst

#----------------------------------------------------------------------------------	

class Stream(object):

	def __init__(self, dir, shp, infile, outfile):
	
		self.shp = shp	
		self.dir = dir
		self.infile = infile
		self.outfile = outfile
	
	
	#-------------------------------
	# OGR para extrair as coordenadas do .shp de nascentes
	def read_shp(self):

		ds = ogr.Open(self.shp,0)
		
		if ds is None:

			print "Open failed.\n"
			sys.exit(1)

		layer = self.shp.split('/')
		layer =  layer[-1][0:-4]

		lyr = ds.GetLayerByName(layer)
		
		# Identifica e salva a referencia espacial
		self.proj4 = lyr.GetSpatialRef().ExportToProj4()		
		
		lyr.ResetReading()

		ptLst = []

		print '  Extraindo Vertices...'
		
		for feat in lyr:
		##            print feat.GetField(0) # Codigo
		##            print feat.GetField(3) # Long
		##            print feat.GetField(4) # Lat
			# num_cod = feat.GetFieldAsDouble(0)

			geom = feat.GetGeometryRef()
			
			if geom == None:
				continue
				
			coord =[]

			for i in range(geom.GetPointCount()):
				# print geom.GetX(i)
				# # x = str(geom.GetX(i)).split('.')
				# print str(geom.GetX(i)).split('.')[1][:5]
				# # print float(geom.GetX(i))

				x = '.'.join([str(geom.GetX(i)).split('.')[0],str(geom.GetX(i)).split('.')[1][:6]])
				y = '.'.join([str(geom.GetY(i)).split('.')[0],str(geom.GetY(i)).split('.')[1][:6]])
				
				coord.append([float(x),float(y)])
			
			if len(coord) == 0:
				continue				

			ptLst.append(coord[0])
			
			self.coord_nasc = ptLst


			
	#-------------------------------	
	# Abre a imagem e extrai informacoes	
	def raster(self):
	
		fname = self.infile
		# outfname = self.dir+'/'+self.outfile

		# Abre o arquivo RASTER
		dataset = gdal.Open(fname, gdalconst.GA_ReadOnly)
		
		if dataset is None:
			print ' Nao pode abrir o arquivo especificado! '
			sys.exit(1)
			
		print
		print '- Informacoes da IMAGEM'
		print '  Arquivo de imagem: ',fname
		
		# Adquire informacoes da Imagem
		print
		print '  Tipo de arquivo: ', dataset.GetDriver().ShortName,'/', \
			  dataset.GetDriver().LongName
		print
		
		self.ncol =  dataset.RasterXSize
		self.nlin =  dataset.RasterYSize
				
		print '  Dimensoes: '
		print '      ', dataset.RasterCount,' Banda(s)'
		print '      ', self.ncol,' Colunas'
		print '      ', self.nlin,' Linhas '
		print
		print '  Projecao da imagem: ',dataset.GetProjection()
		print


		driver = dataset.GetDriver()
		self.proj = dataset.GetProjection()
		self.geotransform = dataset.GetGeoTransform()

		# adfGeoTransform[0] /* top left x */
		# adfGeoTransform[1] /* w-e pixel resolution */
		# adfGeoTransform[2] /* rotation, 0 if image is "north up" */
		# adfGeoTransform[3] /* top left y */
		# adfGeoTransform[4] /* rotation, 0 if image is "north up" */
		# adfGeoTransform[5] /* n-s pixel resolution */
		
		self.originX = self.geotransform[0]
		self.originY = self.geotransform[3]
		self.pixelWidth = self.geotransform[1]
		self.pixelHeight = self.geotransform[5]
		
		print '  Coordenadas da origem = (',self.originX, ',',self.originY,')'
		print '  Dimensoes do pixel = (',self.pixelWidth, ',',self.pixelHeight,')'
		print

		# Adquire informacoes das bandas
		print '   Informacoes por BANDA'
		print
		
		band = dataset.GetRasterBand(1)

		type = gdal.GetDataTypeName(band.DataType)	
		print '  Caract. do dado =',type

		min = band.GetMinimum()
		max = band.GetMaximum()
		
		if min is None or max is None:
			(min,max) = band.ComputeRasterMinMax(1)
			
		print '  Min=%.3f, Max=%.3f' % (min,max)
		print
		
		print "- Carregando imagem p/ memoria..."
		# print "PIL"
		# import Image
		# os.chdir('C:/bacias_ok/teste_agree/hand/teste1/')

		# im = Image.open('fdr_esri1.tif','r')		
		# self.pix = im.load()

		# print "Numpy"
		self.data = band.ReadAsArray(0, 0, self.ncol, self.nlin)
	
	
	
	#-------------------------------
	# Cria matriz com informacao do fluxo		
	def matriz(self):
		# print "\n- Criando matriz ...\n"
		self.matriz = numpy.zeros((self.nlin,self.ncol), dtype=numpy.int)		

	
		
	#-------------------------------
	# Extrai o valor do pixel na imagem	
	def get_value(self):

		# Abre o arquivo RASTER	
		# PIL
		try:
			valor = self.data[self.ind_dir[0], self.ind_dir[1]]
			self.mat_value = self.matriz[self.ind_dir[0], self.ind_dir[1]]
			
			
		except:
			valor = -1
		# Numpy
		# valor = self.data[y_off,x_off]
		self.value = valor

	
	
	#-------------------------------
	# Identifica o indice do pixel na imagem 
	#	com base nas coordenadas do ponto
	def pixval(self, x, y):		

		# print 's',x, y 
		x_off = int((x - self.originX) / self.pixelWidth)
		y_off = int((y - self.originY) / self.pixelHeight)
				

		self.indice = [y_off,x_off]
		
		
		self.value = self.data[y_off,x_off]	
		print "Pixel Nascente:  ",self.indice, self.value
		# exit()
		

		self.mat_value = self.matriz[y_off,x_off]
		
		print
	
	
	
	#-------------------------------
	# Identifica o pixel para onde o fluxo vai [col,lin]
	def direc(self):
	
		if self.value not in [1, 2, 4, 8, 16, 32, 64, 128]:
			print 'O valor ' + self.value + 'existe na matrix de direcao configurada!'
			raise Exception('O valor ' + self.value + 'existe na matrix de direcao configurada!')
	
		if self.value == 1:
			ind_dir = [self.indice[0],self.indice[1]+1]
			
		elif self.value == 2:
			ind_dir = [(self.indice[0]+1),(self.indice[1]+1)]
			
		elif self.value == 4:
			ind_dir = [(self.indice[0]+1),(self.indice[1])]
			
		elif self.value == 8:
			ind_dir = [(self.indice[0]+1),(self.indice[1]-1)]
			
		elif self.value == 16:
			ind_dir = [(self.indice[0]),(self.indice[1]-1)]
			
		elif self.value == 32:
			ind_dir = [(self.indice[0]-1),(self.indice[1]-1)]
				
		elif self.value == 64:
			ind_dir = [(self.indice[0]-1),(self.indice[1])]
				
		elif self.value == 128:
			ind_dir = [(self.indice[0]-1),(self.indice[1]+1)]
			
		# print [ind_dir[0],ind_dir[1]],self.value
		
		# Indice do pixel para onde o fluxo passa
		self.ind_dir = [ind_dir[0],ind_dir[1]]

		
		
	#-------------------------------
	# Calcula a direcao do fluxo 
	def fluxo(self):
	
		self.read_shp()
		self.raster()
		self.matriz()
		
		print '\n- Processando fluxo ...\n'
		
		# Apresenta as informacoes da imagem (RASTER)
		# self.raster()

		# Variaval onde serao armazenados os indices do fluxo
		# self.trace = []

		# Contador
		b = 0
		print '\n Nascentes:\n'
		for x, y in self.coord_nasc:

			# Apresenta informacoes do processamento
			b = b + 1	
			
			print '  '+str(b)+'/'+str(len(self.coord_nasc))	
			
			# Chama a funcao pixval
			try:
				self.pixval(x, y)
			
			except:
				# print x,y, self.value			
				continue
			
			if self.value <= 0 or self.value == 255 or self.mat_value == 1:			
				continue
			
			# Insere na var temporaria 'collin' o indice referente as nascentes	
			collin = []
			collin = [[self.indice[0],self.indice[1]]]	
			
			self.matriz[self.indice[0], self.indice[1]] = 1
			
			a = 1		
		
			while a != 0:
				
				# Roda a funcao para identificar o indice do pixel
				#	para o onde o fluxo vai		
				self.direc()		
					
				if len(collin) <= 2:
				
					# collin = [[self.indice[0],self.indice[1]]]
					
					collin.append(self.ind_dir)
					
					self.matriz[self.ind_dir[0], self.ind_dir[1]] = 1
					
					self.indice = self.ind_dir
					
					self.get_value()					
					
					continue					
					
				self.get_value()
				
				if self.value <= 0 or self.value == 255 or self.mat_value == 1:	
					a = 0 
					continue
					
				# elif self.value == 255:
					# a = 0 
					# continue
					
				# if self.ind_dir in collin:
					# a = 0 
					# continue
					
				collin.append(self.ind_dir)
				
				self.matriz[self.ind_dir[0], self.ind_dir[1]] = 1
				
				self.indice = self.ind_dir
			
			
		self.pix = None	
		
		self.salva_tif()
		
		
	
	#-------------------------------
	# Salva a imagem de saida em tif		
	def salva_tif(self):	
		print
		print " - Criando imagem de saida..."
		
		out_fname = self.dir+'/'+self.outfile
		
		print out_fname
		
		format = 'GTiff'

		out_driver = gdal.GetDriverByName(format)
		outDataset = out_driver.Create(out_fname, self.ncol, self.nlin, 1)
										
		
		outDataset.GetRasterBand(1).WriteArray(self.matriz, 0, 0)	


		outDataset.SetGeoTransform(self.geotransform)
		outDataset.SetProjection(self.proj)
		outDataset.GetRasterBand(1).GetStatistics(0,1)	
		
		outDataset = None
		out_driver = None


		
#-------------------------------		
# Executa a classe		

# img = Stream(dir, shp, infile, outfile)

# Chama as funcoes
# img.fluxo()



#----------------------------------------------------------------------------------
