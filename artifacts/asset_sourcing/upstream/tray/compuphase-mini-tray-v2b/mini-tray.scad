/* mini-tray version 2B
 *
 * Trays for surface mount components, similar to JEDEC trays, but at one
 * third of the size, such that three mini-trays fit in a pick-&-place
 * machine that is designed to take a single JEDEC tray.
 *
 * Copyright 2020-2023, CompuPhase
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
use <shapes.scad>

/* [Parameters] */

// Combined design, or separate top & bottom parts.
Part = 2; // [0:Tray, 1:Cover, 2:Both]
// Type of component.
Type = "QFN"; // [BGA, QFN, QFP, SOIC, SOT223, SO6L, SPDIP, STSOP, TSOP-I, TSSOP]
// Pin count (optional, only used for the engraved text at the tab).
PinCount = 20;
// Style of the pins (use "no lead" for BGA/LGA and castellated).
PinStyle = 0; // [0:No lead, 1:Gull-wing, 2:Lug-lead (flat lead), 3:J-lead]
// X-axis size of the component body (without pins).
BodySizeX = 5;    // 0.1
// Y-axis size of the component body (without pins).
BodySizeY = 5;    // 0.1
// Lead-to-lead X-axis size of the component (so including pins); this value is ignored for the "no-lead" pin style.
PackageSizeX = 5; // 0.1
// Lead-to-lead Y-axis size of the component (so including pins); this value is ignored for the "no-lead" pin style.
PackageSizeY = 5; // 0.1
// Lead-to-lead X-axis tolerance, added on each side (so pocket is twice this value wider than PackageSizeX).
ToleranceX = 0.25;
// Lead-to-lead Y-axis tolerance, added on each side (so pocket is twice this value higher than PackageSizeY).
ToleranceY = 0.25;
// Pocket height; the total of PocketDepth + Separation is also the maximum component height.
PocketDepth = 0.9;
// Separation between the platter and the bottom of the stacked tray, minimum component height.
Separation = 0.5;
// Number of pockets in the X-axis.
PackageColumns = 14;
// Number of pockets in the Y-axis.
PackageRows = 11;
// Spacing of the pockets in the X-axis.
PackageColumnSpacing = 9.25;
// Spacing of the pockets in the Y-axis.
PackageRowSpacing = 8.85;
// Whether the tray is stackable (non-stackable trays are easier to 3D print because no supports are needed).
Stackable = false;
// Whether to set text on the tab.
Description = 2;  // [0:None, 1:Type only, 2:Type & body size, 3:Type & pin count, 4:Custom]
// Custom caption to put at the tab; only used if "Description" parameter is set to "Custom".
TabText = "";
// How high the text is "embossed" (and the recessed frame inside it sinks).
TabEmbossed = 0.4;
// The font for the text on the tab (Geert font by Geert Keteleer can be found on https://www.uantwerpen.be/nl/personeel/geert-keteleer/manuals/)
TabFont = "Geert";

/* [Hidden] */

// JEDEC tray = 135.9 x 322.6 x 6.35 mm
// mini tray  = 135.9 x 106.5 x 5.5 mm
trayLength = 135.9;
trayWidth  = 106.5;
trayHeight = 5.5;       // magnets are 4 mm

// stacking edges are 5 mm wide on top/bottom and 3 mm wide on left/right side
// stacking depth is 1.5 mm
stkWidthHor = 3;
stkWidthVer = 5;
stkDepth = 1.5;
stkSpacing = 0.1;       // stack bottom plate is slightly smaller, for a good fit

thinWallThickness = 0.85; // recommended by PruseSlicer for 0.2mm layer height and 0.4mm nozzle

// tab extends by 3.1 mm and is 3 mm thick; the tab width and horizontal position
// are copied from the JEDEC tray
tabExtent = 3.1;        // the tab exceeds the edge of the frame by this amount
tabHeight = 3;          // thickness of the tab
tabLength = 91;
tabOffs = 18;           // offset from the left edge
tabTolerance = 0.1;     // added to the length (left & right) of the counter-tab
tabSizeDescr = (Type == "TSOP-I") ? str(BodySizeY, "x", BodySizeX) : str(BodySizeX, "x", BodySizeY);
tabText =   (Description == 1) ? Type   // Package name / description
          : (Description == 2) ? str(Type, " ", tabSizeDescr)
          : (Description == 3) ? str(Type, PinCount)
          : TabText;
tabTextSize = 3.5;

// holes for magnets are in the stacking frame, the horizontal placement is not
// critical
holeDiameter = 2.1;     // magnets are 2 x 4 mm, holes are overdimensioned because printing reduces their side
holeOffsX = 4;
holeOffsY = 2.6;

// lead-to-lead size depends on the pin style
LtoL_X = (PinStyle == 0) ? BodySizeX : PackageSizeX;
LtoL_Y = (PinStyle == 0) ? BodySizeY : PackageSizeY;

// the PocketDepth value is from the top of the platter to the support, but the
// support in the middle of a pocket is raised relative to the platter; on small
// pockets, there is no raised support, however
SupportHeight = (LtoL_X > 4.5 && LtoL_Y > 4.5) ? 0.2 : 0;

// sizes for the bottom part, that are also used for the top part
meshLength = trayLength - 2 * (stkWidthHor + stkSpacing);
meshWidth = trayWidth - 2 * (stkWidthVer + stkSpacing);
meshHeight = trayHeight - stkDepth - Separation - PocketDepth - SupportHeight;
meshFrameHeight = trayHeight - stkDepth - Separation; // total height of the frame around the honeycomb mesh

epsilon = 0.05;

// check for conflicting parameters
assert(PinStyle == 0 || (LtoL_X > BodySizeX + 0.1 || LtoL_Y > BodySizeY + 0.1), "WARNING: PackageSize should be greater than BodySize");

// frame creates a hollow cube, but if the wall thickness leaves no space for
// a hole, it makes a cube
module frame(xsize, ysize, zsize, wall) {
  difference() {
    cube([xsize, ysize, zsize]);
    if (xsize - 2 * wall > 0 && ysize - 2 * wall > 0) {
      translate([wall, wall, -epsilon])
        cube([xsize - 2 * wall, ysize - 2 * wall, zsize + 2*epsilon]);
    }
  }
}

module rounded_cube(cx, cy, cz, radius) {
  hull() {
    cube([cx, cy - radius, cz]);
    translate([radius, cy - radius, 0])
      cylinder(r = radius, h = cz, $fn = 40);
    translate([cx - radius, cy - radius, 0])
      cylinder(r = radius, h = cz, $fn = 40);
  }
}

module componentgrid() {
  MeshBarWidth = 1.5;
  union() {
    // frame around the mesh
    frame(meshLength, meshWidth, meshFrameHeight, thinWallThickness);

    // thicker area of the frame
    meshRimDelta = 0.3;                               // thickness added the the mesh frame to fit inside the top part
    meshRimOffset = Stackable ? stkDepth : 0;
    meshRimHeight = meshFrameHeight - meshRimOffset;  // height of the rim
    translate([-meshRimDelta, -meshRimDelta, meshRimOffset])
      frame(meshLength + 2*meshRimDelta, meshWidth + 2*meshRimDelta, meshRimHeight, thinWallThickness + meshRimDelta);

    // some calculations for the pockets
    pocket_cx = LtoL_X + 2*ToleranceX;
    pocket_cy = LtoL_Y + 2*ToleranceY;
    pocket_bounds_cx = (PackageColumns - 1) * PackageColumnSpacing + pocket_cx;
    pocket_bounds_cy = (PackageRows - 1) * PackageRowSpacing + pocket_cy;
    pocket_offs_x = (meshLength - pocket_bounds_cx) / 2;
    pocket_offs_y = (meshWidth - pocket_bounds_cy) / 2;

    pinsize_x = (pocket_cx - BodySizeX) / 2;
    pinsize_y = (pocket_cy - BodySizeY) / 2;

    SupportMinHole = min((LtoL_X + LtoL_Y) / 2, 2);
    hole_cx = min((pocket_cx - 2 * MeshBarWidth) - SupportMinHole, 0);
    hole_cy = min((pocket_cy - 2 * MeshBarWidth) - SupportMinHole, 0);

    // calculations for the supports and the bars below the supports
    support_ridge = (PinStyle == 1 || PinStyle == 3) ? 0.45 : 0; /* for gull-wing & J-lead */
    support_offs_x = (pinsize_x > 0.3) ? max(pinsize_x - support_ridge, 1) : -support_ridge;
    support_offs_y = (pinsize_y > 0.3) ? max(pinsize_y - support_ridge, 1) : -support_ridge;
    support_cx = (SupportHeight > 0.01) ? pocket_cx - 2 * support_offs_x : pocket_cx;
    support_cy = (SupportHeight > 0.01) ? pocket_cy - 2 * support_offs_y : pocket_cy;

    // mesh holding the component "supports"
    for (x = [0 : PackageColumns - 1]) {
      xpos = pocket_offs_x + x * PackageColumnSpacing + support_offs_x;
      translate([xpos + hole_cx, 0, 0])
        cube([MeshBarWidth, meshWidth, meshHeight]);
      translate([xpos + support_cx - hole_cx - MeshBarWidth, 0, 0])
        cube([MeshBarWidth, meshWidth, meshHeight]);

    }
    for (y = [0 : PackageRows - 1]) {
      ypos = pocket_offs_y + y * PackageRowSpacing + support_offs_y;
      translate([0, ypos + hole_cy, 0])
        cube([meshLength, MeshBarWidth, meshHeight]);
      translate([0, ypos + support_cy - hole_cy - MeshBarWidth, 0])
        cube([meshLength, MeshBarWidth, meshHeight]);
    }

    // supports
    for (y = [0 : PackageRows - 1]) {
      ypos = pocket_offs_y + y * PackageRowSpacing + support_offs_y;
      for (x = [0 : PackageColumns - 1]) {
        xpos = pocket_offs_x + x * PackageColumnSpacing + support_offs_x;
        translate([xpos + hole_cx/2, ypos + hole_cy/2, meshHeight - epsilon]) {
          frame(support_cx - hole_cx, support_cy - hole_cy, SupportHeight + 2*epsilon, MeshBarWidth);
          if (PinStyle == 1 || PinStyle == 3)  /* gull-wing or J-lead */
            frame(support_cx - hole_cx, support_cy - hole_cy, SupportHeight + 0.6, support_ridge);
        }
      }
    }

    // the platter with the pockets
    difference() {
      cube([meshLength, meshWidth, meshFrameHeight]);
      for (y = [0 : PackageRows - 1]) {
        ypos = pocket_offs_y + y * PackageRowSpacing;
        for (x = [0 : PackageColumns - 1]) {
          xpos = pocket_offs_x + x * PackageColumnSpacing;
          translate([xpos, ypos, -epsilon])
            cube([pocket_cx, pocket_cy, meshFrameHeight + 2*epsilon]);
        }
      }
    }
  }
}

module outerframe(stackOffset) {
  difference() {
    // top frame, basic block with the tab
    union() {
      cube([trayLength, trayWidth, trayHeight - stackOffset]);
      tab_z = Stackable ? trayHeight - stackOffset - tabHeight : 0;
      translate([tabOffs, trayWidth - epsilon, tab_z])
        rounded_cube(tabLength, tabExtent + epsilon, tabHeight, 1.5);
    }
    // lowering the tab
    if (!Stackable) {
      tab_width = 6 - tabExtent;
      assert(tab_width < (trayWidth - meshWidth) / 2 - thinWallThickness);
      tab_z = Stackable ? trayHeight - stackOffset : tabHeight;
      translate([tabOffs, trayWidth - tab_width, tab_z])
        cube([tabLength, tab_width + epsilon, 5]);
    }
    // Sunken window for the embossed text (see further down for the text itself)
    if (Description > 0) {
      tab_z = Stackable ? trayHeight - stackOffset : tabHeight;
      tab_width = 6 - tabExtent;
      tab_margin = 1;
      // the calculation for text extent is based on Geert font; it needs tweaking for other fonts
      text_extent = tabTextSize * len(tabText) * 0.85;
      translate([tabOffs + 3 - tab_margin, trayWidth - tab_width, tab_z - TabEmbossed])
        cube([text_extent + 2*tab_margin, tabTextSize + 1.2*tab_margin, TabEmbossed + epsilon]);
    }

    // hole, with the same size as the size of the platter
    stacking_tolerance = 0.1;
    offsx = (trayLength - meshLength) / 2;
    offsy = (trayWidth - meshWidth) / 2;
    translate([offsx - stacking_tolerance, offsy - stacking_tolerance, -epsilon])
      cube([meshLength + 2*stacking_tolerance, meshWidth + 2*stacking_tolerance, trayHeight - stackOffset + 2*epsilon]);

    // chamfer on the inside of the hole, for easier stacking
    stacking_chamfer = thinWallThickness;
    hull() {
      translate([offsx - stacking_chamfer, offsy - stacking_chamfer, trayHeight - stackOffset])
        cube([meshLength + 2*stacking_chamfer, meshWidth + 2*stacking_chamfer, epsilon]);
      translate([offsx, offsy, trayHeight - stackOffset - stacking_chamfer])
        cube([meshLength, meshWidth, epsilon]);
    }

    // chamfer on top-left corner
    translate([-0.1, trayWidth+0.1, trayHeight/2])
      rotate([0,0,45])
        cube([4.3, 4.3, trayHeight+0.2], center=true);

    // the holes for the magnets
    for (h = [0 : 3]) {
      holeX = (h % 2) == 0 ? holeOffsX : trayLength-holeOffsX;
      holeY = (h >= 2) ? holeOffsY : trayWidth-holeOffsY;
      translate([holeX, holeY, trayHeight/2])
        cylinder(d=holeDiameter, trayHeight+0.2, $fn=16, center=true);
    }

    // counter-tab, where the tab of another mini-tray fits in
    tabZolerance = 0.3;
    translate([tabOffs - tabTolerance, -0.1, -0.1])
      cube([tabLength + 2*tabTolerance, tabExtent + 0.1, trayHeight + 0.2]);
  }

  // embossed text (raised)
  if (Description > 0) {
    tab_z = Stackable ? trayHeight - stackOffset : tabHeight;
    translate([tabOffs + 3, trayWidth - 2.5, tab_z - TabEmbossed - epsilon])
      linear_extrude(TabEmbossed + epsilon)
        text(tabText, size=tabTextSize, spacing=1.25, font=TabFont);
  }
}

module traycover() {
  coverHeight = stkDepth + 2;   // special magnets of 2mm
  MeshCoverHeight = coverHeight;

  MeshBarWidth = 1.2;
  MeshOffsX = (trayLength - meshLength) / 2;
  MeshOffsY = (trayWidth - meshWidth) / 2;

  union() {
    // mesh
    pocket_cx = BodySizeX - 2*ToleranceX;
    pocket_cy = BodySizeY - 2*ToleranceY;
    pocket_bounds_cx = (PackageColumns - 1) * PackageColumnSpacing + pocket_cx;
    pocket_bounds_cy = (PackageRows - 1) * PackageRowSpacing + pocket_cy;
    pocket_offs_x = (meshLength - pocket_bounds_cx) / 2;
    pocket_offs_y = (meshWidth - pocket_bounds_cy) / 2;

    // inner frame (with the pockets)
    translate([MeshOffsX, MeshOffsY, 0]) {
      difference() {
        cube([meshLength, meshWidth, coverHeight]);
        for (y = [0 : PackageRows - 1]) {
          ypos = pocket_offs_y + y * PackageRowSpacing;
          for (x = [0 : PackageColumns - 1]) {
            xpos = pocket_offs_x + x * PackageColumnSpacing;
            translate([xpos, ypos, -0.1])
              cube([pocket_cx, pocket_cy, coverHeight + 0.2]);
          }
        }
      }
    }

    // outer frame
    translate([0, 0, stkDepth]) {
      difference() {
        // main frame with small tabs and a hole in the middle
        union () {
          cube([trayLength, trayWidth, coverHeight - stkDepth]);
          if (Stackable) {
            translate([tabOffs - tabExtent, trayWidth - 0.01, 0])
              cube([tabExtent, tabExtent, coverHeight - stkDepth]);
            translate([tabOffs - tabExtent + 0.01, trayWidth - 0.01, 0])
              rotate([0, 0, 90])
                prism(tabExtent, tabExtent, coverHeight - stkDepth);
            translate([tabOffs + tabLength, trayWidth - 0.01, 0])
              cube([tabExtent, tabExtent, coverHeight - stkDepth]);
            translate([tabOffs + tabLength + tabExtent - 0.01, trayWidth - 0.01, 0])
              prism(tabExtent, tabExtent, coverHeight - stkDepth);
          }
        }
        translate([MeshOffsX, MeshOffsY, -epsilon])
          cube([meshLength, meshWidth, coverHeight - stkDepth + 0.1]);

        // the holes for the magnets
        for (h = [0 : 3]) {
          holeX = (h % 2) == 0 ? holeOffsX : trayLength-holeOffsX;
          holeY = (h >= 2) ? holeOffsY : trayWidth-holeOffsY;
          translate([holeX, holeY, stkDepth - 0.1])
            cylinder(d=holeDiameter, trayHeight+0.2, $fn=16, center=true);
        }

        // cutouts for tabs
        tabCutout = Stackable ? 2.5 : 1.5;
        translate([tabOffs, trayWidth - tabCutout, -epsilon])
          cube([tabLength, tabCutout + 0.1, coverHeight - stkDepth + 0.1]);
        cutoutWidth = 2.5;
        translate([tabOffs, -0.1, -epsilon])
          cube([tabLength, tabExtent + 0.1, coverHeight - stkDepth + 0.1]);

        // chamfered corner
        translate([-0.1, trayWidth+0.1, 0])
          rotate([0,0,45])
            cube([4.3, 4.3, trayHeight+0.2], center=true);
      }
    }
  }
}

if (Part == 0 || Part == 2) {
  union() {
    stackOffset = Stackable ? stkDepth : 0;
    translate([0, 0, stackOffset])
      outerframe(stackOffset);
    translate([stkWidthHor, stkWidthVer, 0])
      componentgrid();
  }
}
if (Part == 1 || Part == 2) {
  rotate_y = Stackable ? 0 : 180;
  offs_x = Stackable ? 0 : trayLength;
  offs_y = (Part == 1) ? 0 : trayWidth + 5;
  offs_z = Stackable ? 0 : 2 + stkDepth;
  translate([offs_x, offs_y, offs_z])
    rotate([0, rotate_y, 0])
      traycover();
}
