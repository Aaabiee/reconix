document.addEventListener("DOMContentLoaded", function () {
  var overlay = document.createElement("div");
  overlay.className = "lightbox-overlay";
  overlay.innerHTML = '<span class="lightbox-close">&times;</span><img />';
  document.body.appendChild(overlay);

  var overlayImg = overlay.querySelector("img");
  var closeBtn = overlay.querySelector(".lightbox-close");

  document.querySelectorAll('.document img[src*="assets/img/"]').forEach(function (img) {
    img.addEventListener("click", function () {
      overlayImg.src = img.src;
      overlayImg.alt = img.alt;
      overlay.classList.add("active");
    });
  });

  overlay.addEventListener("click", function () {
    overlay.classList.remove("active");
  });

  closeBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    overlay.classList.remove("active");
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      overlay.classList.remove("active");
    }
  });
});
