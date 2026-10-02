(function () {
  "use strict";

  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  var search = document.getElementById("article-search");
  var list = document.getElementById("article-search-results");
  if (search && list) {
    var cards = Array.prototype.slice.call(list.querySelectorAll("[data-search-text]"));
    search.addEventListener("input", function () {
      var q = search.value.trim().toLowerCase();
      cards.forEach(function (card) {
        var text = card.getAttribute("data-search-text");
        card.style.display = !q || text.indexOf(q) !== -1 ? "" : "none";
      });
    });
  }
})();
