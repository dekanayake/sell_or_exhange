$(document).ready(function(){





    $( "#filterPriceFacetBtn" ).click(function() {
       var minPrice = $('#{{form.minPrice.id_for_label}}').val();
          var maxPrice = $('#{{form.maxPrice.id_for_label}}').val();
          var url = $("#filterPriceFacetBtn").data("filter-url");

          if (minPrice){
             url = url.concat('&minPrice=' + escape(minPrice));
          }

          if (maxPrice){
             url =  url.concat('&maxPrice=' + escape(maxPrice));
          }

          window.location.href = url;
    });

});
