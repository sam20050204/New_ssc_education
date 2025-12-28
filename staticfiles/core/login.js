function togglePassword(){
    const pwd = document.getElementById("password");
    const text = event.target;

    if(pwd.type === "password"){
        pwd.type = "text";
        text.innerText = "Hide";
    }else{
        pwd.type = "password";
        text.innerText = "Show";
    }
}
