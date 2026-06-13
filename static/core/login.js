function togglePassword() {
    const pwd = document.getElementById("password");
    const toggleBtn = document.getElementById("eyeToggleBtn");
    const icon = toggleBtn.querySelector("i");

    if (pwd.type === "password") {
        pwd.type = "text";
        icon.className = "fa-solid fa-eye-slash";
    } else {
        pwd.type = "password";
        icon.className = "fa-solid fa-eye";
    }
}

// Add load transition on submit
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("loginForm");
    const submitBtn = document.getElementById("loginSubmitBtn");
    
    if (form && submitBtn) {
        form.addEventListener("submit", function() {
            const btnText = submitBtn.querySelector(".btn-text");
            const btnLoader = submitBtn.querySelector(".btn-loader");
            
            if (btnText && btnLoader) {
                btnText.style.display = "none";
                btnLoader.style.display = "flex";
                submitBtn.disabled = true;
            }
        });
    }
});
