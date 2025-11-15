#!/usr/bin/env wolframscript
(* CATE Distribution Histogram *)

dataFile = $ScriptCommandLine[[2]];
outputFile = $ScriptCommandLine[[3]];

data = Import[dataFile, "JSON"];

cateValues = data["cate_values"];

(* Create histogram *)
plot = Histogram[cateValues,
  20,
  ChartStyle -> "Pastel",
  PlotLabel -> "Distribution of CATE Estimates",
  FrameLabel -> {"CATE", "Frequency"},
  Frame -> True,
  GridLines -> {{0}, None},
  GridLinesStyle -> Directive[Red, Dashed],
  ImageSize -> Large
];

(* Add statistics *)
stats = Grid[{
  {"Mean:", NumberForm[Mean[cateValues], {5, 2}]},
  {"Std:", NumberForm[StandardDeviation[cateValues], {5, 2}]},
  {"Negative %:", NumberForm[100 * Count[cateValues, x_ /; x < 0] / Length[cateValues], {4, 1}]}
}, Frame -> All];

combined = Show[plot,
  Epilog -> Inset[stats, Scaled[{0.75, 0.75}]]
];

Export[outputFile, combined, "PNG", ImageResolution -> 300];

Print["CATE distribution plot saved to: ", outputFile];
