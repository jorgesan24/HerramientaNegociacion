$(function(){

    $("#btnMenu").on("click",function(){

        $("#sidebarMenu").toggleClass("open");

        $("#overlayMenu").toggleClass("open");

    });

    $("#overlayMenu").on("click",function(){

        $("#sidebarMenu").removeClass("open");

        $("#overlayMenu").removeClass("open");

    });

});