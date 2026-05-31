// BioMedPilot LabTools Western Blot preprocessing macro scaffold.
// Parameters are supplied through generated_parameters.json / RunRequest.
// First version intentionally avoids automatic lane or band detection.

inputDir = getArgument();
if (inputDir == "") {
    print("BioMedPilot WB preprocess scaffold: no direct arguments supplied.");
    exit();
}
print("BioMedPilot WB preprocess scaffold");
print("Open images from input_dir, optionally convert to 8-bit, invert, subtract background, and save processed images.");
