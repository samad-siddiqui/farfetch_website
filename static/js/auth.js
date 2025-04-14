// document.addEventListener('DOMContentLoaded', function () {
//     const tab = document.querySelector(".tab-form");
//     const tabHeader = document.querySelector(".tab-header");
//     const tabHeaderElements = tab.querySelectorAll(".tab-header > div");
//     const tabBody = document.querySelector(".tab-body");
//     const tabBodyElements = tab.querySelectorAll(".tab-body > div");

//     // Log for debugging (optional, can remove in production)
//     console.log(tabBodyElements);
//     console.log(tabHeaderElements);

//     // SIGN IN tab (index 0)
//     tabHeaderElements[0].addEventListener("click", function () {
//         tabBodyElements[0].classList.add("active"); // Show login
//         tabBodyElements[1].classList.remove("active"); // Hide signup
//         tabHeaderElements[0].classList.add("active"); // Highlight SIGN IN
//         tabHeaderElements[1].classList.remove("active"); // Unhighlight I'M NEW HERE
//     });

//     // I'M NEW HERE tab (index 1)
//     tabHeaderElements[1].addEventListener("click", function () {
//         tabBodyElements[1].classList.add("active"); // Show signup
//         tabBodyElements[0].classList.remove("active"); // Hide login
//         tabHeaderElements[1].classList.add("active"); // Highlight I'M NEW HERE
//         tabHeaderElements[0].classList.remove("active"); // Unhighlight SIGN IN
//     });
// });
document.addEventListener('DOMContentLoaded', function () {
    const tab = document.querySelector(".tab-form");
    const tabHeader = document.querySelector(".tab-header");
    const tabHeaderElements = tab.querySelectorAll(".tab-header > div");
    const tabBody = document.querySelector(".tab-body");
    const tabBodyElements = tab.querySelectorAll(".tab-body > div");

    console.log(tabBodyElements);
    console.log(tabHeaderElements);

    tabHeaderElements[0].addEventListener("click", function () {
        tabBodyElements[0].classList.add("active");
        tabBodyElements[1].classList.remove("active");
        tabHeaderElements[0].classList.add("active");
        tabHeaderElements[1].classList.remove("active");
    });

    tabHeaderElements[1].addEventListener("click", function () {
        tabBodyElements[1].classList.add("active");
        tabBodyElements[0].classList.remove("active");
        tabHeaderElements[1].classList.add("active");
        tabHeaderElements[0].classList.remove("active");
    });
});