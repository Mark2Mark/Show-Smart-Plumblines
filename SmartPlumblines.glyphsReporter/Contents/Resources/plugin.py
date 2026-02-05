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
    def deslantedX(self, px, py, t, halfXHeight):
        """Single point's x in italic-compensated space."""
        return px - t * (py - halfXHeight)

    @objc.python_method
    def deslantedCenter(self, points, transform=None):
        """X-center of points in italic-compensated space."""
        t = tan(radians(self.angle))
        halfXHeight = self.xHeight / 2
        min_x = float("inf")
        max_x = float("-inf")

        def update(px, py):
            x_desl = self.deslantedX(px, py, t, halfXHeight)
            return min(min_x, x_desl), max(max_x, x_desl)

        for pt in points:
            # Expand selected components into their transformed source nodes
            if hasattr(pt, "componentLayer"):
                try:
                    tr = pt.transform
                    for path in pt.componentLayer.paths:
                        for node in path.nodes:
                            nx, ny = node.position.x, node.position.y
                            min_x, max_x = update(
                                tr[0] * nx + tr[2] * ny + tr[4],
                                tr[1] * nx + tr[3] * ny + tr[5],
                            )
                except Exception:
                    pass
                continue
            try:
                px, py = pt.position.x, pt.position.y
            except AttributeError:
                continue
            if transform is not None:
                px, py = (
                    transform[0] * px + transform[2] * py + transform[4],
                    transform[1] * px + transform[3] * py + transform[5],
                )
            min_x, max_x = update(px, py)
        if min_x == float("inf"):
            return None
        return (min_x + max_x) / 2

    @objc.python_method
    def DrawCross(self, x, y, width, height, color, offset=False, italicCenter=None):
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
        if italicCenter is not None:
            self.drawLine(
                italicCenter + self.italo(yDescender),
                yDescender,
                italicCenter + self.italo(yAscender),
                yAscender,
                offset,
            )
        else:
            # Original behavior for components: pivot around object's own center
            t = tan(radians(self.angle))
            self.drawLine(
                xCenter + t * (yDescender - yCenter),
                yDescender,
                xCenter + t * (yAscender - yCenter),
                yAscender,
                offset,
            )

    @objc.python_method
    def background(self, Layer):
        try:
            self.layer = Layer
            if Layer.isKindOfClass_(GSBackgroundLayer):
                self.xHeight = Layer.foreground().master.xHeight
                self.angle = Layer.foreground().master.italicAngle
            else:
                self.xHeight = Layer.master.xHeight
                self.angle = Layer.master.italicAngle

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
                    *self.BoundsRect(path.bounds), color=pathColor, offset=True,
                    italicCenter=self.deslantedCenter(path.nodes),
                )

            """
			COMPONENT
			"""
            self.dashed = True
            for component in Layer.components:
                ic = None
                try:
                    nodes = []
                    for path in component.componentLayer.paths:
                        nodes.extend(path.nodes)
                    if nodes:
                        ic = self.deslantedCenter(nodes, component.transform)
                except Exception:
                    pass
                self.DrawCross(
                    *self.BoundsRect(component.bounds), color=componentColor,
                    italicCenter=ic,
                )

            """
			SELECTION
			"""
            if Layer.selectionBounds.origin.x < 100000:  # check if Selection
                self.dashed = True
                self.DrawCross(
                    *self.BoundsRect(Layer.selectionBounds), color=selectionColor,
                    italicCenter=self.deslantedCenter(Layer.selection),
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
