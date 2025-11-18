#!/usr/bin/env wolframscript
(* Qini Curve Plot *)

dataFile = $ScriptCommandLine[[2]];
outputFile = $ScriptCommandLine[[3]];

data = Import[dataFile, "JSON"];

fractions = data["fractions"];
qiniValues = data["qini_values"];
randomValues = data["random_values"];

(* Create plot *)
plot = ListLinePlot[
  {Transpose[{fractions, qiniValues}], Transpose[{fractions, randomValues}]},
  PlotStyle -> {{Thick, Blue}, {Dashed, Gray}},
  PlotLegends -> {"Qini Curve (Targeting by CATE)", "Random Targeting"},
  PlotLabel -> "Qini Curve: Cumulative Uplift vs. Targeting Fraction",
  FrameLabel -> {"Fraction Targeted", "Cumulative Uplift"},
  Frame -> True,
  GridLines -> Automatic,
  ImageSize -> Large,
  Filling -> {1 -> {2}},
  FillingStyle -> Directive[Blue, Opacity[0.2]]
];

Export[outputFile, plot, "PNG", ImageResolution -> 300];

Print["Qini curve saved to: ", outputFile];
