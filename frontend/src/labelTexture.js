import { CanvasTexture, SRGBColorSpace } from "three";

export function createLabelTexture(title, subtitle, background = "#f0eadc") {
  const canvas = document.createElement("canvas");
  canvas.width = 768;
  canvas.height = 192;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Could not create a campus sign texture.");

  context.fillStyle = background;
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.strokeStyle = "rgba(49, 76, 65, 0.28)";
  context.lineWidth = 6;
  context.strokeRect(7, 7, canvas.width - 14, canvas.height - 14);
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillStyle = "#30493f";
  context.font = "700 39px sans-serif";
  context.fillText(title, canvas.width / 2, 75, canvas.width - 40);
  context.fillStyle = "#647b6c";
  context.font = "500 24px sans-serif";
  context.fillText(subtitle, canvas.width / 2, 137, canvas.width - 40);

  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace;
  return texture;
}

