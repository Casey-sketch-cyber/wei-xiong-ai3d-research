import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const buildDir =
  "D:\\AutoResearch\\manuscripts\\m03_jcde\\02_figures_tables\\confirmatory_4model_20260729\\fig1_build";
const assetDir =
  "D:\\AutoResearch\\manuscripts\\m03_jcde\\02_figures_tables\\confirmatory_4model_20260729\\fig1_framework_assets";
const outputDir =
  "D:\\AutoResearch\\manuscripts\\m03_jcde\\02_figures_tables\\publication_figures";
const starterPath = path.join(buildDir, "template-starter.pptx");
const outputPath = path.join(
  outputDir,
  "fig1_framework_confirmatory_4model_editable.pptx",
);

async function bytes(name) {
  const buffer = await fs.readFile(path.join(assetDir, name));
  return buffer.buffer.slice(
    buffer.byteOffset,
    buffer.byteOffset + buffer.byteLength,
  );
}

async function writeBlob(output, blob) {
  await fs.mkdir(path.dirname(output), { recursive: true });
  await fs.writeFile(output, new Uint8Array(await blob.arrayBuffer()));
}

async function replaceImage(presentation, id, fileName, alt, frame) {
  const image = presentation.resolve(id);
  image.replace({
    blob: await bytes(fileName),
    contentType: "image/png",
    alt,
    fit: "contain",
  });
  if (frame) image.frame = frame;
  image.crop = { left: 0, top: 0, right: 0, bottom: 0 };
  image.geometry = "rect";
  image.lockAspectRatio = false;
}

function updateText(presentation, id, text, options = {}) {
  const shape = presentation.resolve(id);
  shape.text = text;
  if (options.position) shape.position = options.position;
  shape.text.style = {
    fontSize: options.fontSize ?? 15,
    bold: options.bold ?? false,
    color: options.color ?? "#111111",
    alignment: options.alignment ?? "center",
    verticalAlignment: options.verticalAlignment ?? "middle",
    fontFamily: "Arial",
  };
  return shape;
}

async function main() {
  const presentation = await PresentationFile.importPptx(
    await FileBlob.load(starterPath),
  );
  const slide = presentation.slides.items[0];
  const inspection = await presentation.inspect({
    kind: "slide,textbox,shape,image",
    maxChars: 20000,
  });
  const records = inspection.ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  const textId = (text) => {
    const matches = records.filter(
      (record) => record.kind === "textbox" && record.text === text,
    );
    if (matches.length !== 1) {
      throw new Error(`Expected one textbox for ${JSON.stringify(text)}, found ${matches.length}`);
    }
    return matches[0].id;
  };
  const imageRecords = records
    .filter((record) => record.kind === "image")
    .sort((left, right) => left.bbox[1] - right.bbox[1] || left.bbox[0] - right.bbox[0]);
  const topImageIds = imageRecords.slice(0, 7).map((record) => record.id);
  const lowerImageIds = imageRecords.slice(7).map((record) => record.id);
  const lowerBorderIds = records
    .filter(
      (record) =>
        record.kind === "shape" &&
        Math.abs(record.bbox[1] - 474.67) < 1 &&
        Math.abs(record.bbox[2] - 130.67) < 1,
    )
    .sort((left, right) => left.bbox[0] - right.bbox[0])
    .map((record) => record.id);
  if (topImageIds.length !== 7 || lowerImageIds.length !== 6 || lowerBorderIds.length !== 6) {
    throw new Error(
      `Unexpected source inventory: top=${topImageIds.length}, lower=${lowerImageIds.length}, borders=${lowerBorderIds.length}`,
    );
  }

  const topAssets = [
    [topImageIds[0], "gt_reference.png", "Known solid ground-truth geometry"],
    [topImageIds[1], "input_photo.png", "Matched photo input"],
    [topImageIds[2], "input_edge.png", "Matched edge input"],
    [topImageIds[3], "input_flat.png", "Matched flat-colour input"],
    [topImageIds[4], "input_low_detail.png", "Matched low-detail input"],
    [topImageIds[5], "input_sketch.png", "Matched sketch input"],
    [topImageIds[6], "input_watercolor.png", "Matched watercolour input"],
  ];
  for (const [id, fileName, alt] of topAssets) {
    await replaceImage(presentation, id, fileName, alt);
  }
  slide.images.add({
    blob: await bytes("gt_reference.png"),
    contentType: "image/png",
    alt: "Known solid ground-truth geometry",
    fit: "contain",
    position: { left: 48, top: 69.33, width: 141.33, height: 141.33 },
    geometry: "rect",
  });

  updateText(
    presentation,
    textId("Matched inputs from the same object"),
    "Matched depictions of one known object",
    {
      position: { left: 57.33, top: 22.67, width: 560, height: 25.85 },
      fontSize: 20,
      bold: true,
      alignment: "left",
    },
  );
  updateText(presentation, textId("Reference object"), "3D reference", { fontSize: 14 });
  updateText(presentation, textId("Photo"), "Photo", { fontSize: 14 });
  updateText(presentation, textId("Edge"), "Edge", { fontSize: 14 });
  updateText(presentation, textId("Flat colour"), "Flat colour", { fontSize: 14 });
  updateText(presentation, textId("Low detail"), "Low detail", { fontSize: 14 });
  updateText(presentation, textId("Sketch"), "Sketch", { fontSize: 14 });
  updateText(presentation, textId("Watercolour"), "Watercolour", { fontSize: 14 });

  updateText(
    presentation,
    textId("Same TripoSR pipeline"),
    "Same object and view across four fixed models",
    { fontSize: 22, bold: true },
  );
  updateText(
    presentation,
    textId("same object, same view, same model"),
    "TripoSR  |  InstantMesh  |  Hunyuan3D 2.1  |  TRELLIS",
    { fontSize: 13.5 },
  );
  updateText(
    presentation,
    textId("TripoSR outputs by input style"),
    "Paired outputs expose model-specific style responses",
    {
      position: { left: 57.33, top: 436, width: 650, height: 28 },
      fontSize: 19,
      bold: true,
      alignment: "left",
    },
  );

  const columns = [132, 326, 520, 714];
  const imageSize = 104;
  const photoTop = 488;
  const sketchTop = 600;
  const frames = [
    { left: columns[0], top: photoTop, width: imageSize, height: imageSize },
    { left: columns[1], top: photoTop, width: imageSize, height: imageSize },
    { left: columns[2], top: photoTop, width: imageSize, height: imageSize },
    { left: columns[3], top: photoTop, width: imageSize, height: imageSize },
    { left: columns[0], top: sketchTop, width: imageSize, height: imageSize },
    { left: columns[1], top: sketchTop, width: imageSize, height: imageSize },
    { left: columns[2], top: sketchTop, width: imageSize, height: imageSize },
    { left: columns[3], top: sketchTop, width: imageSize, height: imageSize },
  ];
  const existingBorderIds = lowerBorderIds;
  for (let index = 0; index < existingBorderIds.length; index += 1) {
    const border = presentation.resolve(existingBorderIds[index]);
    border.position = frames[index];
    border.fill = "none";
    border.line = { style: "solid", fill: "#b7b7b7", width: 0.8 };
  }

  const outputAssets = [
    [lowerImageIds[0], "triposr_photo.png", "TripoSR output from photo"],
    [
      lowerImageIds[1],
      "instantmesh_photo.png",
      "InstantMesh output from photo",
    ],
    [
      lowerImageIds[2],
      "hunyuan21_photo.png",
      "Hunyuan3D 2.1 output from photo",
    ],
    [lowerImageIds[3], "trellis_photo.png", "TRELLIS output from photo"],
    [lowerImageIds[4], "triposr_sketch.png", "TripoSR output from sketch"],
    [
      lowerImageIds[5],
      "instantmesh_sketch.png",
      "InstantMesh output from sketch",
    ],
  ];
  for (let index = 0; index < outputAssets.length; index += 1) {
    const [id, fileName, alt] = outputAssets[index];
    await replaceImage(presentation, id, fileName, alt, frames[index]);
  }

  for (const index of [6, 7]) {
    slide.shapes.add({
      geometry: "rect",
      name: `confirmatory-output-border-${index + 1}`,
      position: frames[index],
      fill: "#ffffff",
      line: { style: "solid", fill: "#b7b7b7", width: 0.8 },
    });
  }
  slide.images.add({
    blob: await bytes("hunyuan21_sketch.png"),
    contentType: "image/png",
    alt: "Hunyuan3D 2.1 output from sketch",
    fit: "contain",
    position: frames[6],
    geometry: "rect",
  });
  slide.images.add({
    blob: await bytes("trellis_sketch.png"),
    contentType: "image/png",
    alt: "TRELLIS output from sketch",
    fit: "contain",
    position: frames[7],
    geometry: "rect",
  });

  const modelLabels = [
    [textId("from Photo"), "TripoSR", columns[0]],
    [textId("from Edge"), "InstantMesh", columns[1]],
    [textId("from Flat colour"), "Hunyuan3D 2.1", columns[2]],
    [textId("from Low detail"), "TRELLIS", columns[3]],
  ];
  for (const [id, label, left] of modelLabels) {
    updateText(presentation, id, label, {
      position: { left: left - 19, top: 468, width: 130, height: 20 },
      fontSize: 13.5,
      bold: true,
    });
  }
  updateText(presentation, textId("from Sketch"), "Photo", {
      position: { left: 50, top: 528, width: 66, height: 24 },
    fontSize: 13.5,
    bold: true,
    alignment: "right",
  });
  updateText(presentation, textId("from Watercolour"), "Sketch", {
      position: { left: 50, top: 634, width: 66, height: 24 },
    fontSize: 13.5,
    bold: true,
    alignment: "right",
  });

  updateText(presentation, textId("Paired diagnostics"), "Paired evaluation", {
    position: { left: 1097.33, top: 453, width: 155, height: 30 },
    fontSize: 16,
    bold: true,
    alignment: "left",
  });
  updateText(
    presentation,
    textId("Volume ratio\nz-extent ratio\nChamfer change\nF-score change"),
    "Surface: F-score, Chamfer\nSolid: IoU, volume\nTopology: parts, edges\nSix-view: silhouette, normals",
    {
      position: { left: 1097.33, top: 491, width: 151, height: 96 },
      fontSize: 10.5,
      alignment: "left",
      verticalAlignment: "top",
    },
  );

  slide.speakerNotes.textFrame.setText(
    [
      "[Sources]",
      "- Experimental inputs and outputs: M03 C120 object c120_017, generated by the frozen confirmatory protocol.",
      "- Model outputs: official TripoSR, InstantMesh, Hunyuan3D 2.1, and TRELLIS checkpoints recorded in the experiment manifest.",
      "- Ground truth: Google Scanned Objects asset processed with the frozen solid-GT construction pipeline.",
      "[/Sources]",
    ].join("\n"),
  );

  await writeBlob(
    path.join(buildDir, "final-slide-01.png"),
    await slide.export({ format: "png", scale: 2 }),
  );
  await fs.writeFile(
    path.join(buildDir, "final-slide-01.layout.json"),
    await (await slide.export({ format: "layout" })).text(),
  );
  await writeBlob(
    path.join(buildDir, "final-montage.webp"),
    await presentation.export({ format: "webp", montage: true, scale: 1 }),
  );

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outputPath);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
