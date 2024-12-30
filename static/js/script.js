function downloadRecap() {
  const recapElement = document.getElementById("recap");
  html2canvas(recapElement).then((canvas) => {
    const link = document.createElement("a");
    link.download = "anime_recap_2024.png";
    link.href = canvas.toDataURL();
    link.click();
  });
}
