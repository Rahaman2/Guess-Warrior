"use strict";

var form = document.querySelector("form");
form.addEventListener("submit", function (e) {
  e.preventDefault();
  var formData = new FormData(this);
  fetch("".concat(form.getAttribute("action")), {
    method: 'POST',
    body: formData
  });
  console.log("formDataSent");
});