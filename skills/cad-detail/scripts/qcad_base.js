/**
 * qcad_base.js — CAD-detail skill helper built on the QCad simple API.
 * https://www.qcad.org/doc/qcad/latest/developer/group__ecma__simple.html
 *
 * Script structure:
 *
 *   include("/Users/ottt/.pi/agent/skills/cad-detail/scripts/qcad_base.js");
 *   newDoc("in");                // "in" (default) or "mm"
 *   startTransaction(_doc);
 *
 *   setCurrentLayer("OUTLINE");
 *   addLine(0,0, 6,0);
 *   addCircle(3,4, 1);
 *   addHatchRegion([[0,0],[6,0],[6,8],[0,8]], HATCH.STEEL);
 *   addLinearDim(0,0, 6,0, -0.5, 0);    // horizontal, 0.5 below
 *   addLinearDim(0,0, 0,8, -0.5, 90);   // vertical, 0.5 left
 *   addLabel("PLATE", 3, 4);
 *   addBorderAndTitle(11, 8.5, "DETAIL TITLE", "1:1", "in");
 *
 *   endTransaction();
 *   var path = saveDoc("filename");      // ~/Documents/CAD/filename.dwg
 *
 * Run headless:
 *   /Applications/QCAD.app/Contents/MacOS/QCAD -no-gui -allow-multiple-instances \
 *       -autostart /tmp/script.js
 *
 * View:
 *   open ~/Documents/CAD/filename.dwg
 *
 * Requires QCAD Professional for DWG write support.
 */

include("scripts/simple.js");

// ---------------------------------------------------------------------------
// Standards
// ---------------------------------------------------------------------------
var TEXT_HEIGHT  = 0.12;   // Leroy No. 120 — labels, notes, dim text
var TITLE_HEIGHT = 0.24;   // Leroy No. 240 — title block
var SMALL_HEIGHT = 0.08;   // Leroy No. 80  — secondary notes

var HATCH = {
    STEEL:      "ANSI31",
    STEEL_CROSS:"ANSI32",
    ALUMINUM:   "ANSI38",
    CONCRETE:   "AR-CONC",
    BRICK:      "AR-BRSTD",
    EARTH:      "EARTH",
    GRAVEL:     "GRAVEL",
    INSULATION: "INSUL",
    SCALE: {
        "ANSI31":  0.10,
        "ANSI32":  0.10,
        "ANSI38":  0.10,
        "AR-CONC": 0.02,
        "AR-BRSTD":0.04,
        "EARTH":   0.06,
        "GRAVEL":  0.04,
        "INSUL":   0.08
    }
};

// ---------------------------------------------------------------------------
// Document — global _doc used by hatch/dim helpers
// ---------------------------------------------------------------------------
var _doc   = null;
var _units = "in";

/**
 * Create a new off-screen document and set up standard layers.
 * @param {string} units  "in" (default) or "mm"
 */
function newDoc(units) {
    _units = units || "in";
    _doc   = createDocument();
    _doc.setUnit(_units === "mm" ? RS.Millimeter : RS.Inch);
    _setupLayers();
    return _doc;
}

function _setupLayers() {
    //            name         color       linetype      lineweight
    addLayer("OUTLINE",   "#ffffff", "Continuous",  RLineweight.Weight050);
    addLayer("HIDDEN",    "#00cc00", "HIDDEN",      RLineweight.Weight025);
    addLayer("CENTER",    "#cc0000", "CENTER",      RLineweight.Weight018);
    addLayer("DIMENSION", "#cccc00", "Continuous",  RLineweight.Weight018);
    addLayer("TEXT",      "#ffffff", "Continuous",  RLineweight.Weight018);
    addLayer("HATCH",     "#888888", "Continuous",  RLineweight.Weight009);
    addLayer("DETAIL",    "#00cccc", "Continuous",  RLineweight.Weight035);
    addLayer("TITLE",     "#ffffff", "Continuous",  RLineweight.Weight025);
    addLayer("BORDER",    "#ffffff", "Continuous",  RLineweight.Weight070);
}

// ---------------------------------------------------------------------------
// Save as DWG  (requires QCAD Professional)
// ---------------------------------------------------------------------------

/**
 * Save to ~/Documents/CAD/<filename>.dwg
 * @param {string} filename  Base name, no extension.
 * @returns {string}  Absolute path.
 */
function saveDoc(filename) {
    var safe = filename.replace(/[^a-zA-Z0-9_\-]/g, "_");
    var dir  = QDir.homePath() + "/Documents/CAD";
    var qd   = new QDir(dir);
    if (!qd.exists()) { qd.mkpath(dir); }
    var path = dir + "/" + safe + ".dwg";
    var di   = new RDocumentInterface(_doc);
    di.exportFile(path);
    print("Saved: " + path);
    return path;
}

// ---------------------------------------------------------------------------
// Geometry helpers
// ---------------------------------------------------------------------------

/**
 * Draw a closed polygon outline on the current layer.
 * Set the layer with setCurrentLayer() before calling.
 * @param {Array} points  [[x,y], ...]
 */
function addPolygon(points) {
    var pts = [];
    for (var i = 0; i < points.length; i++) {
        pts.push([points[i][0], points[i][1], 0, false]);
    }
    addPolyline(pts, true);
}

/**
 * Draw crosshair centerlines on the CENTER layer.
 * @param {number} cx, cy  Centre point
 * @param {number} size    Half-arm length
 */
function addCenterlines(cx, cy, size) {
    setCurrentLayer("CENTER");
    addLine(cx - size, cy, cx + size, cy);
    addLine(cx, cy - size, cx, cy + size);
}

// ---------------------------------------------------------------------------
// Hatch  (simple API: addEntity)
// ---------------------------------------------------------------------------

/**
 * Fill a closed polygonal region with a hatch pattern.
 * @param {Array}  boundary  [[x,y], ...]
 * @param {string} pattern   HATCH.* constant (default HATCH.STEEL)
 * @param {number} scale     null → use HATCH.SCALE default
 * @param {number} angle     degrees (default 0)
 */
function addHatchRegion(boundary, pattern, scale, angle) {
    pattern = pattern || HATCH.STEEL;
    scale   = (scale !== undefined && scale !== null) ? scale
                                                      : (HATCH.SCALE[pattern] || 0.10);
    angle   = angle || 0;

    var hd = new RHatchData();
    hd.setDocument(_doc);
    hd.setPatternName(pattern);
    hd.setScale(scale);
    hd.setAngle(angle * Math.PI / 180);
    hd.newLoop();

    for (var i = 0; i < boundary.length; i++) {
        var p1 = boundary[i];
        var p2 = boundary[(i + 1) % boundary.length];
        hd.addBoundary(new RLine(
            new RVector(p1[0], p1[1]),
            new RVector(p2[0], p2[1])
        ).clone());
    }

    setCurrentLayer("HATCH");
    addEntity(new RHatchEntity(_doc, hd));
}

// ---------------------------------------------------------------------------
// Dimensions  (simple API: addEntity)
// ---------------------------------------------------------------------------

/**
 * Add a horizontal (angle=0) or vertical (angle=90) linear dimension.
 * @param {number} x1,y1   First measured point
 * @param {number} x2,y2   Second measured point
 * @param {number} offset  + = above/right, − = below/left
 * @param {number} angle   0 = horizontal, 90 = vertical
 */
function addLinearDim(x1, y1, x2, y2, offset, angle) {
    angle = angle || 0;

    var defPt = (angle === 0)
        ? new RVector((x1 + x2) / 2, y1 + offset)
        : new RVector(x1 + offset, (y1 + y2) / 2);

    var dd = new RDimRotatedData();
    dd.setExtensionPoint1(new RVector(x1, y1));
    dd.setExtensionPoint2(new RVector(x2, y2));
    dd.setDefinitionPoint(defPt);
    dd.setRotation(angle * Math.PI / 180);

    setCurrentLayer("DIMENSION");
    addEntity(new RDimRotatedEntity(_doc, dd));
}

/**
 * Add a radius dimension leader.
 * @param {number} cx,cy   Circle centre
 * @param {number} radius
 * @param {number} angle   Leader direction in degrees from +X (default 45)
 */
function addRadiusDim(cx, cy, radius, angle) {
    angle = (angle !== undefined) ? angle : 45;

    var dd = new RDimRadialData();
    dd.setCenter(new RVector(cx, cy));
    dd.setChordPoint(RVector.createPolar(radius, angle * Math.PI / 180)
                              .operator_add(new RVector(cx, cy)));

    setCurrentLayer("DIMENSION");
    addEntity(new RDimRadialEntity(_doc, dd));
}

/**
 * Add a diameter dimension across a circle.
 * @param {number} cx,cy   Circle centre
 * @param {number} radius
 * @param {number} angle   Chord axis angle in degrees from +X (default 45)
 */
function addDiameterDim(cx, cy, radius, angle) {
    angle = (angle !== undefined) ? angle : 45;
    var rad = angle * Math.PI / 180;
    var ctr = new RVector(cx, cy);

    var dd = new RDimDiametricData();
    dd.setChordPoint(   RVector.createPolar(radius,  rad).operator_add(ctr));
    dd.setFarChordPoint(RVector.createPolar(radius,  rad + Math.PI).operator_add(ctr));

    setCurrentLayer("DIMENSION");
    addEntity(new RDimDiametricEntity(_doc, dd));
}

// ---------------------------------------------------------------------------
// Annotations
// ---------------------------------------------------------------------------

/**
 * Add a text label.
 * @param {string} text
 * @param {number} x, y
 * @param {number} height  Default TEXT_HEIGHT (0.12)
 * @param {string} align   "MC" middle-center (default), "ML", "MR",
 *                         "BL", "BR", "TL", "TR"
 * @param {string} layer   Default "TEXT"
 */
function addLabel(text, x, y, height, align, layer) {
    height = height || TEXT_HEIGHT;
    layer  = layer  || "TEXT";
    align  = align  || "MC";

    var h = RS.HAlignCenter, v = RS.VAlignMiddle;
    if      (align === "ML") { h = RS.HAlignLeft; }
    else if (align === "MR") { h = RS.HAlignRight; }
    else if (align === "BL") { h = RS.HAlignLeft;  v = RS.VAlignBottom; }
    else if (align === "BR") { h = RS.HAlignRight; v = RS.VAlignBottom; }
    else if (align === "TL") { h = RS.HAlignLeft;  v = RS.VAlignTop; }
    else if (align === "TR") { h = RS.HAlignRight; v = RS.VAlignTop; }

    setCurrentLayer(layer);
    addSimpleText(text, x, y, height, 0, "standard", v, h, false, false);
}

/**
 * Draw a leader line with annotation text at the tail.
 * Arrowhead is at the first vertex.
 * @param {Array}  pts   [[x,y], ...]
 * @param {string} text
 * @param {number} height  Default TEXT_HEIGHT
 */
function addLeader(pts, text, height) {
    height = height || TEXT_HEIGHT;
    setCurrentLayer("DIMENSION");
    for (var i = 0; i < pts.length - 1; i++) {
        addLine(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1]);
    }
    var end = pts[pts.length - 1];
    setCurrentLayer("TEXT");
    addSimpleText(text, end[0] + height * 0.5, end[1], height, 0,
                  "standard", RS.VAlignMiddle, RS.HAlignLeft, false, false);
}

// ---------------------------------------------------------------------------
// Border and title block
// ---------------------------------------------------------------------------

/**
 * Add a sheet border and simple title block.  Call last.
 * @param {number} w, h    Sheet size in drawing units (1:1)
 * @param {string} title   Detail title (auto upper-cased)
 * @param {string} scale   Default "1:1"
 * @param {string} units   "in" or "mm"
 * @param {string} by      Optional drafter initials
 */
function addBorderAndTitle(w, h, title, scale, units, by) {
    scale = scale || "1:1";
    units = units || _units;
    by    = by    || "";

    var m     = (units === "in") ? 0.5  : 13.0;
    var box_h = (units === "in") ? 0.75 : 19.0;
    var mid_x = m + (w - 2 * m) * 0.60;
    var cy    = m + box_h / 2;

    setCurrentLayer("BORDER");
    addPolyline([[m,m,0,false],[w-m,m,0,false],[w-m,h-m,0,false],[m,h-m,0,false]], true);
    addPolyline([[m,m,0,false],[w-m,m,0,false],[w-m,m+box_h,0,false],[m,m+box_h,0,false]], true);
    addLine(mid_x, m, mid_x, m + box_h);

    setCurrentLayer("TITLE");
    addSimpleText(title.toUpperCase(),
                  m + (mid_x - m) / 2, cy + TEXT_HEIGHT * 0.4,
                  TITLE_HEIGHT, 0, "standard",
                  RS.VAlignMiddle, RS.HAlignCenter, false, false);
    addSimpleText("SCALE: " + scale,
                  mid_x + (w - m - mid_x) / 2, cy + TEXT_HEIGHT * 0.5,
                  TEXT_HEIGHT, 0, "standard",
                  RS.VAlignMiddle, RS.HAlignCenter, false, false);
    if (by) {
        addSimpleText("BY: " + by,
                      mid_x + (w - m - mid_x) / 2, cy - TEXT_HEIGHT * 0.5,
                      SMALL_HEIGHT, 0, "standard",
                      RS.VAlignMiddle, RS.HAlignCenter, false, false);
    }
}
