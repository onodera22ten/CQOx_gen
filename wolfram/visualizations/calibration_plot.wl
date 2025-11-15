#!/usr/bin/env wolframscript
(* Calibration Plot: Predicted vs Observed CATE *)

dataFile = $ScriptCommandLine[[2]];
outputFile = $ScriptCommandLine[[3]];

data = Import[dataFile, "JSON"];

predicted = data["predicted_means"];
observed = data["observed_means"];

(* Create scatter plot with diagonal line *)
plot = Show[
  (* Scatter points *)
  ListPlot[Transpose[{predicted, observed}],
    PlotStyle -> {PointSize[0.02], Blue},
    PlotMarkers -> Automatic
  ],

  (* Perfect calibration line (y=x) *)
  Plot[x, {x, Min[predicted], Max[predicted]},
    PlotStyle -> {Red, Dashed}
  ],

  (* Labels *)
  PlotLabel -> "Calibration: Predicted vs Observed CATE",
  FrameLabel -> {"Predicted CATE", "Observed CATE"},
  Frame -> True,
  GridLines -> Automatic,
  PlotLegends -> Placed[{"Actual", "Perfect Calibration"}, {0.2, 0.8}],
  ImageSize -> Large,
  AspectRatio -> 1
];

Export[outputFile, plot, "PNG", ImageResolution -> 300];

Print["Calibration plot saved to: ", outputFile];
