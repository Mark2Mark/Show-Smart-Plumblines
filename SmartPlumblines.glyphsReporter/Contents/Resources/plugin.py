# encoding: utf-8
from __future__ import division, print_function, unicode_literals

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from math import tan, radians
from AppKit import (
    NSColor,
    NSCommandKeyMask,
    NSControlKeyMask,
    NSAlternateKeyMask,
    NSBezierPath,
)


class SmartPlumblines(ReporterPlugin):

    @objc.python_method
    def settings(self):
        self.menuName = Glyphs.localize(
            {
                "en": "Smart Plumblines",
                "de": "Intelligente Lotschnur",
                "fr": "lignes intelligentes de construction",
                "es": "líneas inteligentes de construcción",
            }
        )
        self.keyboardShortcut = "p"
        self.keyboardShortcutModifier = (
            NSCommandKeyMask | NSControlKeyMask | NSAlternateKeyMask
        )

    @objc.python_method
    def BoundsRect(self, rect):
        x, y = rect.origin
        width, height = rect.size
        return x, y, width, height

    @objc.python_method
    def drawLine(self, x1, y1, x2, y2, offset=False):
        scale = self.getScale()
        strokeWidth = 0.5 / scale
        myPath = NSBezierPath.bezierPath()
        myPath.moveToPoint_((x1, y1))
        myPath.lineToPoint_((x2, y2))
        myPath.setLineWidth_(strokeWidth)
        dash_a = float(6.0 / scale)
        if self.dashed:
            myPath.setLineDash_count_phase_(
                (dash_a, dash_a), 2, dash_a if offset else 0.0
            )
        myPath.stroke()

    @objc.python_method
    def italo(self, yPos):
        """
        ITALIC OFFSET
        """
        offset = tan(radians(self.angle)) * self.xHeight / 2
        shift = tan(radians(self.angle)) * yPos - offset
        return shift

    @objc.python_method
    def italoObject(self, yPos, heightOfObject):
        """
        ITALIC OFFSET
        """
        ### ROTATION around half object height
        offset = tan(radians(self.angle)) * heightOfObject / 2
        shift = tan(radians(self.angle)) * yPos - offset
        return shift

    @objc.python_method
    def DrawCross(self, x, y, width, height, color, offset=False):
        if self.layer.isKindOfClass_(GSBackgroundLayer):
            self.xHeight = self.layer.foreground().master.xHeight
            self.angle = self.layer.foreground().master.italicAngle
        else:
            self.xHeight = self.layer.master.xHeight
            self.angle = self.layer.master.italicAngle

        ### BOUNDS DIMENSIONS
        xCenter = x + width / 2
        xRight = x + width
        yCenter = y + height / 2
        yTop = y + height

        ### LAYER/METRIC DIMENSIONS
        xLayerLeft = 0
        xLayerRight = self.layer.width
        yAscender = self.layer.glyphMetrics()[1]
        yDescender = self.layer.glyphMetrics()[3]

        """outside bounds"""
        # NSColor.colorWithCalibratedRed_green_blue_alpha_( *color ).set()
        color.set()
        self.drawLine(
            xLayerLeft + self.italo(yCenter),
            yCenter,
            xLayerRight + self.italo(yCenter),
            yCenter,
            offset,
        )
        ### visual debugging:
        # self.drawTextAtPoint( u"x", (xLayerLeft + self.italo(yCenter), yCenter) )
        self.drawLine(
            xCenter + self.italoObject(yDescender - y, height),
            yDescender,
            xCenter + self.italoObject(yAscender - y, height),
            yAscender,
            offset,
        )  # without angle

    @objc.python_method
    def background(self, Layer):
        try:
            self.layer = Layer
            pathColor = (
                NSColor.textColor()
                .blendedColorWithFraction_ofColor_(0.7, NSColor.systemPinkColor())
                .colorWithAlphaComponent_(0.7)
            )
            componentColor = NSColor.textColor().colorWithAlphaComponent_(0.3)
            selectionColor = (
                NSColor.textColor()
                .blendedColorWithFraction_ofColor_(0.7, NSColor.systemMintColor())
                .colorWithAlphaComponent_(0.7)
            )

            # Disable drawing plumblines when space is pressed and exit early
            currentController = self.controller.view().window().windowController()
            if currentController:
                if currentController.SpaceKey():
                    return

            """
			PATH
			"""
            self.dashed = True
            for path in Layer.paths:
                self.DrawCross(
                    *self.BoundsRect(path.bounds), color=pathColor, offset=True
                )

            """
			COMPONENT
			"""
            self.dashed = True
            for component in Layer.components:
                self.DrawCross(*self.BoundsRect(component.bounds), color=componentColor)

            """
			SELECTION
			"""
            if Layer.selectionBounds.origin.x < 100000:  # check if Selection
                self.dashed = True
                self.DrawCross(
                    *self.BoundsRect(Layer.selectionBounds), color=selectionColor
                )

        except Exception as e:
            print(e)
            import traceback

            print(traceback.format_exc())
            self.logToConsole("drawBackgroundForLayer_: %s" % str(e))

    def needsExtraMainOutlineDrawingForInactiveLayer_(self, Layer):
        return True

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
