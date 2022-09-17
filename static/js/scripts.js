/*!
* Start Bootstrap - Shop Homepage v5.0.5 (https://startbootstrap.com/template/shop-homepage)
* Copyright 2013-2022 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-shop-homepage/blob/master/LICENSE)
*/
// This file is intentionally blank
// Use this file to add JavaScript to your project
var myModal = document.getElementById('myModal')
var myInput = document.getElementById('myInput')

myModal.addEventListener('shown.bs.modal', function () {
  myInput.focus()
})

$(document).ready(function() {
  var visEle = $(".card-border:visible");
  var hidEle = $(".card-border:not(:visible)");

  if (hidEle.length > 0) {
    $('.card-border:last').after('<button class="showMore">Show more</button>')
  }

  $(document).on("click", ".showMore", function() {
    hidEle.first().show();
    hidEle = $(".card-border:not(:visible)");
    if (hidEle.length == 0) {
      $(".showMore").hide();
    }
  });
});


$(document).ready(function() {
  var visEle = $(".card-border:visible");
  var hidEle = $(".card-border:not(:visible)");

  if (hidEle.length > 0) {
    $('.card-border:last').after('<button class="showMore">Show more</button>')
  }

  $(document).on("click", ".showMore", function() {
    hidEle.first().show();
    hidEle = $(".card-border:not(:visible)");
    if (hidEle.length == 0) {
      $(".showMore").hide();
    }
  });
});



