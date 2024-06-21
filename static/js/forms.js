const form = document.querySelector("form");

form.addEventListener("submit", function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    
    fetch(`${form.getAttribute("action")}`, {
        method: 'POST',
        body: formData
      });
    console.log("formDataSent")
})