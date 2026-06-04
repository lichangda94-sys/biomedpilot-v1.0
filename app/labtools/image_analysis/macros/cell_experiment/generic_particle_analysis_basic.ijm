// BioMedPilot LabTools built-in ImageJ macro template.
// Source: dev/labtools@f77bfe4 generic_particle_analysis.
// Runtime tasks generate a parameterized copy from cell_imagej_workflows.py.
// Review thresholds, masks and CSV results before scientific use.
setBatchMode(true);
inputDir = getDirectory("Choose input image folder");
outputDir = getDirectory("Choose output folder");
File.makeDirectory(outputDir);
outputCsv = outputDir + "generic_particle_results.csv";
threshold_method = "Default";
particle_polarity = "dark";
background_rolling_px = 0;
blur_sigma = 1.0;
min_particle_area_px = 30;
max_particle_area_px = "Infinity";
min_circularity = 0.0;
max_circularity = 1.0;
watershed = "true";
File.saveString("image,particle_count,total_area_px,mean_area_px,mean_circularity,mean_feret_px\n", outputCsv);
print("Use BioMedPilot runtime generation for batch execution with fixed paths.");
