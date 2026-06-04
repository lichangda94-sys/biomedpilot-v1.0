// BioMedPilot LabTools built-in ImageJ macro template.
// Source: dev/labtools@f77bfe4 roi_intensity_batch.
// Runtime tasks generate a parameterized copy from cell_imagej_workflows.py.
// Requires an ROI zip. Missing ROI zip must remain a blocker, not a formal result.
setBatchMode(true);
inputDir = getDirectory("Choose input image folder");
outputDir = getDirectory("Choose output folder");
File.makeDirectory(outputDir);
outputCsv = outputDir + "roi_intensity_results.csv";
roi_zip_path = "";
background_roi_index = -1;
measurement_channel = 1;
File.saveString("image,status,roi_index,roi_name,area_px,mean_gray,integrated_density,background_mean,corrected_mean,corrected_integrated_density\n", outputCsv);
if (roi_zip_path == "")
    File.append("\"__config__\",missing_roi_zip,-1,\"\",0,0,0,0,0,0\n", outputCsv);
print("Use BioMedPilot runtime generation after selecting an ROI zip.");
