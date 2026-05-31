// BioMedPilot LabTools Western Blot fixed rectangle ROI measurement scaffold.
// Reads a ROI CSV generated in BioMedPilot and measures Area, Mean, IntDen, RawIntDen.
// First version is macro-ready scaffolding; it does not perform automatic lane/band detection.

roiCsvPath = getArgument();
if (roiCsvPath == "") {
    print("BioMedPilot WB ROI measurement scaffold: no ROI CSV supplied.");
    exit();
}
run("Set Measurements...", "area mean min integrated redirect=None decimal=3");
print("BioMedPilot WB ROI measurement scaffold");
print("Expected CSV columns include roi_id,image_path,roi_type,lane_index,sample_name,x,y,width,height.");
