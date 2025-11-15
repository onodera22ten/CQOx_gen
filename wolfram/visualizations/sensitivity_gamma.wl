#!/usr/bin/env wolframscript
(* Sensitivity Analysis (Gamma) Plot *)

dataFile = $ScriptCommandLine[[2]];
outputFile = $ScriptCommandLine[[3]];

data = Import[dataFile, "JSON"];

gammaValues = data["gamma_values"];
pValuesUpper = data["p_values_upper"];
pValuesLower = data["p_values_lower"];
criticalGamma = data["critical_gamma"];

(* Create plot *)
plot = ListLinePlot[
  {Transpose[{gammaValues, pValuesUpper}], Transpose[{gammaValues, pValuesLower}]},
  PlotStyle -> {{Thick, Blue}, {Thick, Red}},
  PlotLegends -> {"Upper Bound", "Lower Bound"},
  PlotLabel -> "Rosenbaum Sensitivity Analysis",
  FrameLabel -> {"\[CapitalGamma] (Sensitivity Parameter)", "p-value"},
  Frame -> True,
  GridLines -> {{criticalGamma}, {0.05}},
  GridLinesStyle -> Directive[Dashed, Gray],
  ImageSize -> Large,
  Epilog -> {
    Text[Style["Critical \[CapitalGamma] = " <> ToString[NumberForm[criticalGamma, 2]], 14],
      Scaled[{0.7, 0.3}]]
  }
];

Export[outputFile, plot, "PNG", ImageResolution -> 300];

Print["Sensitivity analysis plot saved to: ", outputFile];
