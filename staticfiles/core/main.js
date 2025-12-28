
function openModal(){document.getElementById("enquiryModal").style.display="block";}
function closeModal(){document.getElementById("enquiryModal").style.display="none";}

/* FADE-IN ON SCROLL */
const sections = document.querySelectorAll("section");

const reveal = () => {
    sections.forEach(section => {
        const top = section.getBoundingClientRect().top;
        if (top < window.innerHeight - 100) {
            section.classList.add("show");
        }
    });
};

window.addEventListener("scroll", reveal);
reveal();

function openModal(){
    document.getElementById("enquiryModal").style.display="block";
}
function closeModal(){
    document.getElementById("enquiryModal").style.display="none";
}
