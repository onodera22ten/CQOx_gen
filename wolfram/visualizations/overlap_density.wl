#!/usr/bin/env wolframscript
(* Propensity Score Overlap Density Plot *)

dataFile = $ScriptCommandLine[[2]];
outputFile = $ScriptCommandLine[[3]];

data = Import[dataFile, "JSON"];

psTreated = data["ps_treated"];
psControl = data["ps_control"];

(* Create density plots *)
plot = Show[
  (* Control group *)
  SmoothHistogram[psControl,
    PlotStyle -> {Blue, Opacity[0.5]},
    PlotRange -> {{0, 1}, All},
    Filling -> Axis
  ],

  (* Treated group *)
  SmoothHistogram[psTreated,
    PlotStyle -> {Red, Opacity[0.5]},
    PlotRange -> {{0, 1}, All},
    Filling -> Axis
  ],

  (* Threshold lines *)
  Graphics[{Dashed, Gray,
    Line[{{0.1, 0}, {0.1, 10}}],
    Line[{{0.9, 0}, {0.9, 10}}]
  }],

  (* Labels *)
  PlotLabel -> "Propensity Score Distribution by Treatment Group",
  FrameLabel -> {"Propensity Score", "Density"},
  Frame -> True,
  PlotLegends -> Placed[{"Control", "Treated"}, {0.8, 0.8}],
  ImageSize -> Large
];

Export[outputFile, plot, "PNG", ImageResolution -> 300];

Print["Overlap density plot saved to: ", outputFile];
