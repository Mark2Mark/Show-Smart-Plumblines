#!/usr/bin/env python
# encoding: utf-8

# TODO:
# 	- skew the bounds first? Currently we got bounds and skew later,
# 		this might lead to inaccuracy? Check with anchor alignment between two points
# 	- Badge with distance from center points if only to objects


import objc
from GlyphsApp.plugins import *
import sys, os, re
import math

import GlyphsApp

GlyphsReporterProtocol = objc.protocolNamed( "GlyphsReporter" )

class SmartPlumblines ( NSObject, GlyphsReporterProtocol ):

	def init( self ):
		try:
			#Bundle = NSBundle.bundleForClass_( NSClassFromString( self.className() ));
			return self
		except Exception as e:
			self.logToConsole( "init: %s" % str(e) )

	def interfaceVersion( self ):
		try:
			return 1
		except Exception as e:
			self.logToConsole( "interfaceVersion: %s" % str(e) )

	def title( self ):
		try:
			return "Smart Plumblines"
		except Exception as e:
			self.logToConsole( "title: %s" % str(e) )

	def keyEquivalent( self ):
		try:
			return u"p"
			# return None
		except Exception as e:
			self.logToConsole( "keyEquivalent: %s" % str(e) )

	def modifierMask( self ):
		'''
		return NSShiftKeyMask | NSControlKeyMask | NSCommandKeyMask | NSAlternateKeyMask
		'''
		try:
			return NSCommandKeyMask | NSControlKeyMask | NSAlternateKeyMask
			# return 0
		except Exception as e:
			self.logToConsole( "modifierMask: %s" % str(e) )

	def drawForegroundForLayer_( self, Layer ):
		try:
			pass
		except Exception as e:
			self.logToConsole( "drawForegroundForLayer_: %s" % str(e) )


	def BoundsRect(self, NSRect):
		x = NSRect[0][0]
		y = NSRect[0][1]
		width = NSRect[1][0]
		height = NSRect[1][1]
		return x, y, width, height


	def drawLine(self, x1, y1, x2, y2):
		strokeWidth = 1/self.getScale()
		myPath = NSBezierPath.bezierPath()
		myPath.moveToPoint_((x1, y1))
		myPath.lineToPoint_((x2, y2))
		myPath.setLineWidth_(strokeWidth)
		if self.dashed:
			myPath.setLineDash_count_phase_((2, 2), 2, 0.0)
		myPath.stroke()


	def italo(self, yPos):
		'''
		ITALIC OFFSET
		'''
		offset = math.tan(math.radians(self.angle)) * self.xHeight/2
		shift = math.tan(math.radians(self.angle)) * yPos - offset
		return shift


	def italoObject(self, yPos, heightOfObject):
		'''
		ITALIC OFFSET
		'''
		### ROTATION around half object height
		offset = math.tan(math.radians(self.angle)) * heightOfObject/2
		shift = math.tan(math.radians(self.angle)) * yPos - offset
		return shift


	def DrawCross(self, x, y, width, height, color):
		self.xHeight = self.layer.glyphMetrics()[4]
		self.angle = self.layer.glyphMetrics()[5]

		### BOUNDS DIMENSIONS
		xCenter = (x + width/2)
		xRight = x + width
		yCenter = (y + height/2)
		yTop = y + height

		### LAYER/METRIC DIMENSIONS
		xLayerLeft = 0
		xLayerRight = self.layer.width
		yAscender = self.layer.glyphMetrics()[1]
		yDescender = self.layer.glyphMetrics()[3]

		'''outside bounds'''
		NSColor.colorWithCalibratedRed_green_blue_alpha_( *color ).set()
		self.drawLine( xLayerLeft + self.italo(yCenter), yCenter, xLayerRight + self.italo(yCenter), yCenter)
		### visual debugging:
		# self.drawTextAtPoint( u"x", (xLayerLeft + self.italo(yCenter), yCenter) )
		self.drawLine( xCenter + self.italoObject(yDescender-y, height), yDescender, xCenter + self.italoObject(yAscender-y, height), yAscender ) # without angle


		# Draw Outside Bounds
		#NSColor.colorWithCalibratedRed_green_blue_alpha_( 0.5, 0, 0, 0.12 ).set()
		# Horizontals
		#self.drawLine(xLayerLeft, y, xLayerRight, y)
		#self.drawLine(xLayerLeft, y+height, xLayerRight, y+height)
		# Verticlas
		#self.drawLine( x + self.italoObject(yDescender-y, height), yDescender, x + self.italoObject(yAscender-y, height), yAscender ) # without angle

		# self.drawLine(x + self.italo(yDescender), yDescender, x + self.italo(yAscender), yAscender)
		# self.drawLine(x+width + self.italo(yDescender), yDescender, x+width + self.italo(yAscender), yAscender)



	def DrawBounds(self, x, y, width, height):
		pass
		# check Skedge Sketch `Layer Bounds with Real Skew`
		# self.xHeight = self.layer.glyphMetrics()[4]
		# self.angle = self.layer.glyphMetrics()[5]

		# ### BOUNDS DIMENSIONS
		# xLeft = x + width
		# xCenter = (x + width/2)
		# xRight = x + width
		# yCenter = (y + height/2)
		# yTop = y + height
		# yBottom = y + height

		# ### LAYER/METRIC DIMENSIONS
		# xLayerLeft = 0
		# xLayerRight = self.layer.width
		# yAscender = self.layer.glyphMetrics()[1]
		# yDescender = self.layer.glyphMetrics()[3]

		# '''outside bounds'''
		# #self.drawLine( xLayerLeft + self.italo(yCenter), yCenter, xLayerRight + self.italo(yCenter), yCenter)
		# ### visual debugging:
		# # self.drawTextAtPoint( u"x", (xLayerLeft + self.italo(yCenter), yCenter) )

		# self.drawLine( xLeft + self.italoObject(yDescender-y, height), yDescender, xLeft + self.italoObject(yAscender-y, height), yAscender ) # without angle



	def drawBackgroundForLayer_( self, Layer ):
		try:
			self.layer = Layer
			pathColor = 1, 0, 0, 0.2
			componentColor = 0, 0, 0, 0.1
			selectionColor = 0, 0, 0.5, 0.2

			# Disable drawing plumblines when space is pressed and exit early
			currentController = self.controller.view().window().windowController()
			if currentController:
				if currentController.SpaceKey():
					return

			'''
			PATH
			'''
			self.dashed = False
			for path in Layer.paths:
				self.DrawCross( *self.BoundsRect(path.bounds), color=pathColor )
				#NSColor.orangeColor().set()
				#self.DrawBounds( *self.BoundsRect(path.bounds) )

			'''
			COMPONENT
			'''
			self.dashed = False
			for component in Layer.components:
				self.DrawCross( *self.BoundsRect(component.bounds), color=componentColor )

			'''
			SELECTION
			'''
			if Layer.selectionBounds.origin.x < 100000: # check if Selection
				self.dashed = True
				self.DrawCross( *self.BoundsRect(Layer.selectionBounds), color=selectionColor )

				### DRAW BOUNDS OF SELECTION **UC**
				# self.dashed = False
				# sX, sY, sWidth, sHeight = self.BoundsRect(Layer.selectionBounds)
				# sYCenter = (sY + sHeight/2)

				# selectionBoundsRect = NSBezierPath.bezierPath()
				# ### straight rect
				# # selectionBoundsRect.moveToPoint_((sX, sY))
				# # selectionBoundsRect.lineToPoint_((sX, sY + sHeight))
				# # selectionBoundsRect.lineToPoint_((sX + sWidth, sY + sHeight))
				# # selectionBoundsRect.lineToPoint_((sX + sWidth, sY))
				# ### italic angle rect
				# selectionBoundsRect.moveToPoint_((sX + self.italoObject(sY-sY, sHeight), sY))
				# selectionBoundsRect.lineToPoint_((sX + self.italoObject(sY-sY + sHeight, sHeight), sY + sHeight))
				# selectionBoundsRect.lineToPoint_((sX + sWidth + self.italoObject(sY-sY + sHeight, sHeight), sY + sHeight))
				# selectionBoundsRect.lineToPoint_((sX + sWidth + self.italoObject(sY-sY, sHeight) , sY))

				# selectionBoundsRect.closePath()
				# selectionBoundsRect.stroke()





		except Exception as e:
			self.logToConsole( "drawBackgroundForLayer_: %s" % str(e) )

	def drawBackgroundForInactiveLayer_( self, Layer ):
		try:
			pass
		except Exception as e:
			self.logToConsole( "drawBackgroundForInactiveLayer_: %s" % str(e) )


	def drawTextAtPoint( self, text, textPosition, fontSize=9.0, fontColor=NSColor.brownColor() ):
		try:
			glyphEditView = self.controller.graphicView()
			currentZoom = self.getScale()
			fontAttributes = {
				NSFontAttributeName: NSFont.labelFontOfSize_( fontSize/currentZoom ),
				NSForegroundColorAttributeName: fontColor }
			displayText = NSAttributedString.alloc().initWithString_attributes_( text, fontAttributes )
			textAlignment = 3 # top left: 6, top center: 7, top right: 8, center left: 3, center center: 4, center right: 5, bottom left: 0, bottom center: 1, bottom right: 2
			glyphEditView.drawText_atPoint_alignment_( displayText, textPosition, textAlignment )
		except Exception as e:
			self.logToConsole( "drawTextAtPoint: %s" % str(e) )

	def needsExtraMainOutlineDrawingForInactiveLayer_( self, Layer ):
		return True

	def getHandleSize( self ):
		try:
			Selected = NSUserDefaults.standardUserDefaults().integerForKey_( "GSHandleSize" )
			if Selected == 0:
				return 5.0
			elif Selected == 2:
				return 10.0
			else:
				return 7.0 # Regular
		except Exception as e:
			self.logToConsole( "getHandleSize: HandleSize defaulting to 7.0. %s" % str(e) )
			return 7.0

	def getScale( self ):
		try:
			return self.controller.graphicView().scale()
		except:
			self.logToConsole( "Scale defaulting to 1.0" )
			return 1.0

	def setController_( self, Controller ):
		try:
			self.controller = Controller
		except Exception as e:
			self.logToConsole( "Could not set controller" )

	def logToConsole( self, message ):
		myLog = "Show %s plugin:\n%s" % ( self.title(), message )
		NSLog( myLog )
