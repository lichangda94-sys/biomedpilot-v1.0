// BioMedPilot LabTools Transwell ImageJ workflow template.
// Runtime task workspaces render this template with concrete input/output paths.
setBatchMode(true);
inputDir = "";
outputDir = "";
outputCsv = outputDir + "transwell_results.csv";
threshold_method = "Default";
cell_polarity = "dark";
blur_sigma = 1.0;
min_particle_area_px = 30;
max_particle_area_px = "Infinity";
watershed = "true";
File.saveString("image,particle_count,total_particle_area_px,mean_particle_area_px\n", outputCsv);
list = getFileList(inputDir);
for (i = 0; i < list.length; i++) {
    if (!isImageFile(list[i])) continue;
    imagePath = inputDir + list[i];
    open(imagePath);
    run("Duplicate...", "title=analysis");
    selectWindow("analysis");
    run("8-bit");
    run("Gaussian Blur...", "sigma=" + blur_sigma);
    if (cell_polarity == "dark")
        setAutoThreshold(threshold_method + " dark");
    else
        setAutoThreshold(threshold_method + " light");
    run("Convert to Mask");
    if (watershed == "true")
        run("Watershed");
    run("Clear Results");
    run("Analyze Particles...", "size=" + min_particle_area_px + "-" + max_particle_area_px + " display clear");
    totalParticleArea = 0;
    for (row = 0; row < nResults; row++)
        totalParticleArea = totalParticleArea + getResult("Area", row);
    particleCount = nResults;
    meanParticleArea = 0;
    if (particleCount > 0)
        meanParticleArea = totalParticleArea / particleCount;
    File.append(csvEscape(list[i]) + "," + particleCount + "," + totalParticleArea + "," + meanParticleArea + "\n", outputCsv);
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
