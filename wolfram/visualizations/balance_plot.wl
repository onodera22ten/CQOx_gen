#!/usr/bin/env wolframscript
(* Covariate Balance (Love Plot) Visualization *)

dataFile = $ScriptCommandLine[[2]];
outputFile = $ScriptCommandLine[[3]];

data = Import[dataFile, "JSON"];

covariates = data["covariates"];
smds = data["smd"];
threshold = 0.1;

(* Create horizontal bar chart *)
plot = BarChart[
  smds,
  ChartLabels -> Placed[covariates, Axis],
  ChartStyle -> Function[{val}, If[Abs[val] > threshold, Red, Green]],
  BarOrigin -> Left,
  PlotLabel -> "Covariate Balance (SMD)",
  FrameLabel -> {"Standardized Mean Difference", "Covariate"},
  ChartLegends -> None,
  GridLines -> {{-threshold, 0, threshold}, None},
  GridLinesStyle -> Directive[Dashed, Gray],
  ImageSize -> Large,
  AspectRatio -> 1/GoldenRatio
];

Export[outputFile, plot, "PNG", ImageResolution -> 300];

Print["Balance plot saved to: ", outputFile];
