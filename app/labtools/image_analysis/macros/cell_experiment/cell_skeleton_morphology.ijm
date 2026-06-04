// BioMedPilot LabTools built-in Fiji macro template.
// Source: dev/labtools@f77bfe4 cell_skeleton_morphology.
// Requires Fiji with Skeletonize/Analyze Skeleton commands available.
// Runtime tasks generate a parameterized copy from cell_imagej_workflows.py.
setBatchMode(true);
inputDir = getDirectory("Choose input image folder");
outputDir = getDirectory("Choose output folder");
File.makeDirectory(outputDir);
outputCsv = outputDir + "cell_skeleton_morphology_results.csv";
threshold_method = "Default";
foreground_polarity = "dark";
blur_sigma = 0.0;
prune_method = "none";
save_skeleton_image = "true";
File.saveString("image,status,skeleton_image,summary_csv,branch_csv\n", outputCsv);
print("Fiji plugin gate required before formal use.");
