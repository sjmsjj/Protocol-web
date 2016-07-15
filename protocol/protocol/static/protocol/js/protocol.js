function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function highLightNavbar(){
    var page_titile = document.title
    $("#" + page_titile).addClass("header-item");


    // if(page_titile === "Protocol_List"){
    //     $("#" + page_titile).addClass("active");
    // }

}