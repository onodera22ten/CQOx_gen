#!/usr/bin/env wolframscript
(* Pareto Frontier Visualization *)

(* Load data from JSON *)
dataFile = $ScriptCommandLine[[2]];
outputFile = $ScriptCommandLine[[3]];

data = Import[dataFile, "JSON"];

allPolicies = data["all_policies"];
paretoFrontier = data["pareto_frontier"];

allX = allPolicies["x"];
allY = allPolicies["y"];
allIDs = allPolicies["policy_ids"];

paretoX = paretoFrontier["x"];
paretoY = paretoFrontier["y"];
paretoIDs = paretoFrontier["policy_ids"];

obj1Name = data["obj1_name"];
obj2Name = data["obj2_name"];

(* Create plot *)
plot = Show[
  (* All policies as gray points *)
  ListPlot[
    Transpose[{allX, allY}],
    PlotStyle -> {Gray, Opacity[0.5], PointSize[0.015]},
    PlotMarkers -> Automatic
  ],

  (* Pareto frontier as red line and points *)
  ListPlot[
    Transpose[{paretoX, paretoY}],
    PlotStyle -> {Red, PointSize[0.02]},
    Joined -> True,
    PlotMarkers -> Automatic
  ],

  (* Labels and styling *)
  FrameLabel -> {obj1Name, obj2Name},
  PlotLabel -> "Multi-Objective Pareto Frontier",
  Frame -> True,
  GridLines -> Automatic,
  ImageSize -> Large,
  PlotRange -> All
];

(* Export *)
Export[outputFile, plot, "PNG", ImageResolution -> 300];

Print["Pareto frontier visualization saved to: ", outputFile];
