const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const sourcePath = path.join(__dirname, 'public', 'routine.html');
const tempPath = path.join(__dirname, 'temp_export.html');
const outputPath = path.join(__dirname, 'public', 'routine_export.png');

console.log('Reading source routine HTML...');
let html = fs.readFileSync(sourcePath, 'utf8');

// Insert style override to hide everything except the offscreen export container
const styleOverride = `
<style>
  body > *:not(#exportOffscreenContainer) {
    display: none !important;
  }
  #exportOffscreenContainer {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 1400px !important;
    height: 787.5px !important;
    background-color: #ffffff !important;
    display: block !important;
    z-index: 999999 !important;
  }
  /* Ensure the main cards wrapper fills height and doesn't scroll */
  .export-card {
    height: 100% !important;
  }
</style>
`;

html = html.replace('</head>', styleOverride + '</head>');

// Force immediate execution of buildExportOffscreenTemplate
const callImmediate = `
// Force immediate population
buildExportOffscreenTemplate();
`;
html = html.replace('buildExportOffscreenTemplate(); // Pre-populate the landscape canvas elements', 'buildExportOffscreenTemplate();\n' + callImmediate);

// Write modified HTML to temp file
fs.writeFileSync(tempPath, html, 'utf8');
console.log('Temporary export HTML written to:', tempPath);

// Run Google Chrome in headless mode to capture screenshot
const chromePath = '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"';
const cmd = `${chromePath} --headless --disable-gpu --screenshot="${outputPath}" --window-size=1400,788 "file:///${tempPath.replace(/\\/g, '/')}"`;

console.log('Running headless Google Chrome to export 16:9 PNG image...');
try {
  execSync(cmd, { stdio: 'inherit' });
  console.log('Routine exported successfully to:', outputPath);
} catch (e) {
  console.error('Failed to run Chrome headless:', e);
} finally {
  if (fs.existsSync(tempPath)) {
    fs.unlinkSync(tempPath);
    console.log('Cleaned up temporary export HTML.');
  }
}
