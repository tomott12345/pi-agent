/**
 * qcad_base.js — QCAD Detail Skill Helper
 * 
 * Provides helper functions for headless QCAD scripting.
 * Call newDoc() first, then draw on layers, then saveDoc().
 * 
 * For command-line execution, the script should include this file and call main().
 * 
 * @param {string} outputDir - Directory where the DWG/DXF file should be saved (default: "/Users/ottt/Documents/CAD")
 */

// --- Drawing standards (inches) ---
var TEXT_HEIGHT    = 0.12;
var TITLE_HEIGHT   = 0.24;
var SMALL_HEIGHT   = 0.08;

// --- Layer definitions: name -> {color, lineweight} ---
var _LAYER_DEFS = [
    { name: "OUTLINE",   color: "white",  lw: 0.35 },
    { name: "HIDDEN",    color: "green",  lw: 0.18 },
    { name: "CENTER",    color: "red",    lw: 0.18 },
    { name: "DIMENSION", color: "yellow", lw: 0.18 },
    { name: "TEXT",      color: "white",  lw: 0.18 },
    { name: "HATCH",     color: "grey",   lw: 0.09 },
    { name: "DETAIL",    color: "cyan",   lw: 0.35 },
    { name: "TITLE",     color: "white",  lw: 0.25 },
    { name: "BORDER",    color: "white",  lw: 0.50 }
];

// --- Hatch pattern constants ---
// Note: QCAD hatch patterns are defined by their name. Common ones:
 // EARTH = "EARTH", CONCRETE = "CONCRETE", STEEL = "ANSI31", etc.
var HATCH = {
    STEEL:      "ANSI31",    // 45° diagonal lines
    ALUMINUM:   "ANSI32",    // reverse 45° diagonal
    CONCRETE:   "CONCRETE",  // aggregate pattern
    BRICK:      "BRICK",     // horizontal rows
    EARTH:      "EARTH",     // earth/fill pattern
    GRAVEL:     "GRAVEL",    // square grid
    INSULATION: "SOLID",     // solid fill
    STEEL2:     "ANSI33",    // 45° cross-hatch
    STEEL3:     "ANSI34",    // 60° cross-hatch
};

// --- Global state (command-line mode) ---
var _storage = null;
var _spatialIndex = null;
var _document = null;
var _di = null;
var _currentLayer = "OUTLINE";
var _layerIds = {};
var _units = "in";

// --- Hatch pattern defaults ---
var HATCH_SCALES = {
    STEEL:      0.10,
    ALUMINUM:   0.10,
    CONCRETE:   0.02,
    BRICK:      0.04,
    EARTH:      0.06,
    GRAVEL:     0.04,
    INSULATION: 0.08,
};

// ============================================================================
// DOCUMENT INITIALIZATION
// ============================================================================

function newDoc(units) {
    units = units || "in";
    _units = units;

    _storage = new RMemoryStorage();
    _spatialIndex = new RSpatialIndexSimple();
    _document = new RDocument(_storage, _spatialIndex);
    _di = new RDocumentInterface(_document);

    // Create standard layers
    _layerIds = {};
    var continuousId = _document.getLinetypeId("CONTINUOUS");

    for (var i = 0; i < _LAYER_DEFS.length; i++) {
        var ld = _LAYER_DEFS[i];
        var color = new RColor(ld.color);
        var layer = new RLayer(_document, ld.name, false, false, color,
                               continuousId, RLineweight.Weight000);
        var op = new RAddObjectsOperation();
        op.addObject(layer);
        _di.applyOperation(op);
        _layerIds[ld.name] = layer.getId();
    }

    // Set default layer
    setCurrentLayer("OUTLINE");

    return _document;
}

function setOutputDir(outputDir) {
    // This function can be called to override the default output directory
    // The saveDoc function will use this directory
    _outputDir = outputDir;
}

// ============================================================================
// LAYER MANAGEMENT
// ============================================================================

function setCurrentLayer(name) {
    _currentLayer = name;
    _di.setCurrentLayer(name);
}

function hasLayer(name) {
    return name in _layerIds;
}

// ============================================================================
// GEOMETRY HELPERS
// ============================================================================

function addLine(x1, y1, x2, y2) {
    var op = new RAddObjectsOperation();
    var entity = new RLineEntity(_document, new RLineData(
        new RVector(x1, y1), new RVector(x2, y2)));
    entity.setLayerId(_layerIds[_currentLayer]);
    op.addObject(entity);
    _di.applyOperation(op);
    return entity;
}

function addPolygon(points) {
    var op = new RAddObjectsOperation();
    var polyline = new RPolylineEntity(_document,
        new RPolylineData(points.map(function(p) { return new RVector(p[0], p[1]); }), true));
    polyline.setLayerId(_layerIds[_currentLayer]);
    op.addObject(polyline);
    _di.applyOperation(op);
    return polyline;
}

function addCircle(cx, cy, r) {
    var op = new RAddObjectsOperation();
    var entity = new RCircleEntity(_document,
        new RCircleData(new RVector(cx, cy), r));
    entity.setLayerId(_layerIds[_currentLayer]);
    op.addObject(entity);
    _di.applyOperation(op);
    return entity;
}

function addArc(cx, cy, r, startDeg, endDeg, clockwise) {
    var op = new RAddObjectsOperation();
    var entity = new RArcEntity(_document,
        new RArcData(new RVector(cx, cy), r, startDeg, endDeg));
    entity.setLayerId(_layerIds[_currentLayer]);
    op.addObject(entity);
    _di.applyOperation(op);
    return entity;
}

function addCenterlines(cx, cy, size) {
    var origLayer = _currentLayer;
    setCurrentLayer("CENTER");
    addLine(cx - size, cy, cx + size, cy);
    addLine(cx, cy - size, cx, cy + size);
    setCurrentLayer(origLayer);
}

// ============================================================================
// HATCH HELPERS
// ============================================================================

function addHatchRegion(points, patternTuple, scale) {
    // QCAD's hatch support is limited in headless mode.
    // We'll create a closed polyline as the boundary and add a solid hatch.
    // Note: Full hatch support requires QCAD Professional and may need
    // the pattern file to be loaded.
    var boundary = points.map(function(p) { return new RVector(p[0], p[1]); });
    boundary.push(boundary[0]); // close

    var op = new RAddObjectsOperation();
    var polyline = new RPolylineEntity(_document,
        new RPolylineData(boundary, true));
    polyline.setLayerId(_layerIds[_currentLayer]);
    op.addObject(polyline);
    _di.applyOperation(op);

    // For hatch: we add a solid fill polyline with a grey color
    // since full hatch support is limited in headless mode
    setCurrentLayer("HATCH");
    addPolygon(points);
    setCurrentLayer(_currentLayer);
}

// ============================================================================
// DIMENSION HELPERS
// ============================================================================

function addLinearDim(x1, y1, x2, y2, offset, angle) {
    // angle: 0 = horizontal, 90 = vertical
    // Create dimension line as a polyline with tick marks
    var op = new RAddObjectsOperation();
    var dimColor = new RColor("yellow");

    var p1 = new RVector(x1, y1);
    var p2 = new RVector(x2, y2);
    var defPoint;
    var label;

    if (angle === 0) {
        // Horizontal dimension
        defPoint = new RVector((x1 + x2) / 2, y1 + offset);
        var dist = Math.abs(x2 - x1);
        label = String(Math.round(dist * 100) / 100);
        // Extension lines
        addExtensionLine(x1, y1, defPoint.y, dimColor);
        addExtensionLine(x2, y2, defPoint.y, dimColor);
        // Dimension line
        addLine(x1, defPoint.y, x2, defPoint.y);
    } else {
        // Vertical dimension
        defPoint = new RVector(x1 + offset, (y1 + y2) / 2);
        var dist = Math.abs(y2 - y1);
        label = String(Math.round(dist * 100) / 100);
        // Extension lines
        addExtensionLine(x1, y1, defPoint.x, dimColor, true);
        addExtensionLine(x2, y2, defPoint.x, dimColor, true);
        // Dimension line
        addLine(defPoint.x, y1, defPoint.x, y2);
    }

    // Dimension label
    addLabel(label, defPoint.x, defPoint.y + 0.15, TEXT_HEIGHT, "DIMENSION");
}

function addExtensionLine(x1, y1, extY, color, vertical) {
    if (vertical) {
        addLine(x1, y1, x1, y1 + (extY > y1 ? 0.3 : -0.3));
    } else {
        addLine(x1, y1, x1 + 0.3, y1);
    }
}

function addRadiusDim(cx, cy, r, angle) {
    var op = new RAddObjectsOperation();
    var rad = angle * Math.PI / 180;
    var defPoint = new RVector(cx + r * 1.5 * Math.cos(rad),
                                cy + r * 1.5 * Math.sin(rad));
    try {
        var entity = new RDimLinearEntity(_document,
            new RDimLinearData(new RVector(cx, cy), new RVector(cx + r, cy), defPoint));
        entity.setLayerId(_layerIds["DIMENSION"]);
        op.addObject(entity);
        _di.applyOperation(op);
    } catch (e) {
        print("Warning: Could not create radius dimension: " + e);
    }
}

function addDiameterDim(cx, cy, r, angle) {
    var op = new RAddObjectsOperation();
    var rad = angle * Math.PI / 180;
    var defPoint = new RVector(cx + r * 1.5 * Math.cos(rad),
                                cy + r * 1.5 * Math.sin(rad));
    try {
        var entity = new RDimLinearEntity(_document,
            new RDimLinearData(new RVector(cx - r, cy), new RVector(cx + r, cy), defPoint));
        entity.setLayerId(_layerIds["DIMENSION"]);
        op.addObject(entity);
        _di.applyOperation(op);
    } catch (e) {
        print("Warning: Could not create diameter dimension: " + e);
    }
}

// ============================================================================
// TEXT & LABEL HELPERS
// ============================================================================

function addLabel(text, x, y, height, layer) {
    height = height || TEXT_HEIGHT;
    layer = layer || "TEXT";
    var origLayer = _currentLayer;
    setCurrentLayer(layer);

    var op = new RAddObjectsOperation();
    var entity = new RTextEntity(_document,
        new RTextData(
            new RVector(x, y),
            new RVector(x, y),
            height,
            0.0,
            RS.VAlignBottom,
            RS.HAlignLeft,
            RS.LeftToRight,
            RS.Exact,
            1.0,
            text,
            "Arial",
            false,
            false,
            0.0,
            false
        ));
    entity.setLayerId(_layerIds[layer]);
    op.addObject(entity);
    _di.applyOperation(op);

    setCurrentLayer(origLayer);
}

function addLeader(points, text, height) {
    height = height || TEXT_HEIGHT;
    for (var i = 0; i < points.length - 1; i++) {
        addLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1]);
    }
    var end = points[points.length - 1];
    addLabel(text, end[0] + height * 0.5, end[1], height, "TEXT");
}

// ============================================================================
// BORDER & TITLE BLOCK
// ============================================================================

function addBorderAndTitle(w, h, title, scale, units, by) {
    var m = units === "in" ? 0.25 : 10;
    var boxH = units === "in" ? 0.5 : 13;
    var midX = m + (w - 2 * m) * 0.60;
    var cy = m + boxH / 2;

    var origLayer = _currentLayer;

    // Border
    setCurrentLayer("BORDER");
    addPolygon([[m, m], [w-m, m], [w-m, h-m], [m, h-m]]);
    addPolygon([[m, m], [w-m, m], [w-m, m+boxH], [m, m+boxH]]);
    addLine(midX, m, midX, m + boxH);

    // Title text
    addLabel(title.toUpperCase(), m + (midX - m) / 2, cy + TEXT_HEIGHT * 0.4,
             TITLE_HEIGHT, "TITLE");

    // Scale text
    addLabel("SCALE: " + scale, midX + (w - m - midX) / 2,
             cy + TEXT_HEIGHT * 0.5, TEXT_HEIGHT, "TITLE");

    // By text
    if (by) {
        addLabel("BY: " + by.toUpperCase(), midX + (w - m - midX) / 2,
                 cy - TEXT_HEIGHT * 0.5, SMALL_HEIGHT, "TITLE");
    }

    setCurrentLayer(origLayer);
}

// ============================================================================
// CURSOR STATE MACHINE
// ============================================================================

var Cursor = {
    x: 0,
    y: 0,
    moveTo: function(x, y) { this.x = x; this.y = y; },
    moveRel: function(dx, dy) { this.x += dx; this.y += dy; },
    lineTo: function(x, y) { addLine(this.x, this.y, x, y); this.x = x; this.y = y; }
};

// ============================================================================
// SAVE DOCUMENT
// ============================================================================

var _outputDir = "/Users/ottt/Documents/CAD"; // Default output directory

function saveDoc(filename) {
    var safe = filename.replace(/[^a-zA-Z0-9_-]/g, "_");
    var outputPath = _outputDir + "/" + safe + ".dwg";

    try {
        _di.exportFile(outputPath, "R24 (2010) DWG");
        print("Saved: " + outputPath);
    } catch (e) {
        print("DWG export failed, trying DXF: " + e);
        outputPath = _outputDir + "/" + safe + ".dxf";
        _di.exportFile(outputPath, "R24 (2010) DXF");
        print("Saved: " + outputPath);
    }

    return outputPath;
}

// ============================================================================
// TRANSACTION HELPERS
// ============================================================================

function startTransaction(di) {
    // No-op in headless mode; QCAD auto-commits operations
}

function endTransaction() {
    // No-op in headless mode
}

// ============================================================================
// LAYOUT
// ============================================================================

function validateLayers() {
    // Layers are already created in newDoc()
}