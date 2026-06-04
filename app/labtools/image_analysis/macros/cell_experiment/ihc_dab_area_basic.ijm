// BioMedPilot LabTools IHC/DAB ImageJ workflow template.
// Runtime task workspaces render this template with concrete input/output paths.
setBatchMode(true);
inputDir = "";
outputDir = "";
outputCsv = outputDir + "ihc_dab_area_results.csv";
threshold_method = "Default";
positive_polarity = "dark";
blur_sigma = 1.0;
min_positive_area_px = 50;
saturated_percent = 0.35;
File.saveString("image,positive_area_px,total_area_px,positive_fraction,mean_gray\n", outputCsv);
list = getFileList(inputDir);
for (i = 0; i < list.length; i++) {
    if (!isImageFile(list[i])) continue;
    imagePath = inputDir + list[i];
    open(imagePath);
    width = getWidth();
    height = getHeight();
    totalArea = width * height;
    run("Duplicate...", "title=analysis");
    selectWindow("analysis");
    run("8-bit");
    run("Enhance Contrast", "saturated=" + saturated_percent);
    run("Gaussian Blur...", "sigma=" + blur_sigma);
    getStatistics(area, meanGray);
    if (positive_polarity == "dark")
        setAutoThreshold(threshold_method + " dark");
    else
        setAutoThreshold(threshold_method + " light");
    run("Convert to Mask");
    run("Clear Results");
    run("Analyze Particles...", "size=" + min_positive_area_px + "-Infinity display clear");
    positiveArea = 0;
    for (row = 0; row < nResults; row++)
        positiveArea = positiveArea + getResult("Area", row);
    positiveFraction = positiveArea / totalArea;
    File.append(csvEscape(list[i]) + "," + positiveArea + "," + totalArea + "," + positiveFraction + "," + meanGray + "\n", outputCsv);
    close("*");
}

function isImageFile(name) {
    lower = toLowerCase(name);
    return endsWith(lower, ".tif") || endsWith(lower, ".tiff") || endsWith(lower, ".jpg") || endsWith(lower, ".jpeg") || endsWith(lower, ".png");
}

function csvEscape(value) {
    escaped = replace(value, "\"", "\"\"");
    return "\"" + escaped + "\"";
}
