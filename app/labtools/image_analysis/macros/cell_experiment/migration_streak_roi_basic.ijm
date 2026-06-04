// BioMedPilot LabTools built-in ImageJ macro template.
// Source: dev/labtools@2fa005d migration_streak_roi.
// Runtime tasks generate a parameterized copy from cell_imagej_workflows.py.
// The ROI threshold strategy must be validated on real migration/scratch images.
setBatchMode(true);
inputDir = getDirectory("Choose input image folder");
outputDir = getDirectory("Choose output folder");
File.makeDirectory(outputDir);
outputCsv = outputDir + "migration_streak_roi_results.csv";
streak_threshold_method = "Default";
streak_polarity = "bright";
streak_blur_sigma = 2.0;
streak_min_area_px = 500;
signal_threshold_method = "Default";
signal_polarity = "dark";
signal_min_area_px = 30;
signal_max_area_px = "Infinity";
File.saveString("image,status,streak_roi_count,streak_area_px,signal_particle_count,signal_area_px,residual_streak_area_px,residual_fraction\n", outputCsv);
print("Use BioMedPilot runtime generation for batch execution with fixed paths.");
