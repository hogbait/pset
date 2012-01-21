var map;
var mit_coord =  new google.maps.LatLng(42.35886, -71.09356);
var top_left = new google.maps.LatLng(42.36425, -71.10798);
var bottom_right = new google.maps.LatLng(42.35068, -71.07030);
var my_loc = new google.maps.LatLng(0,0);
var valid_loc = false;

var tmp_loc;

var last_query={};

function init_map(){
    var mapdiv = $("#mapdiv");
    MAP_TYPE_ID = 'MY_MAP_TYPE';

    var stylez = [{
        featureType: "landscape.man_made",
        elementType: "geometry",
        stylers: [
            { hue: "#FFF5D9" },
            { gamma: .6},
            { saturation: 30},
        ]
        },{
        featureType: "landscape.man_made",
        elementType: "labels",
        stylers: [
        ]
        },{
        featureType: "road",
        elementType: "all",
        stylers: [
            { hue: "#DCB6B5" },
            { gamma: 2},
            { saturation: -30 },
        ]
        },{
        featureType: "road",
        elementType: "labels",
        stylers: [
            {saturation: -60},
            {lightness: 60},
        ]
        },{
        featureType: "poi.sports_complex",
        elementType: "geometry",
        stylers: [
            {saturation: 30},
            {lightness: -10},
        ]
        },{
        featureType: "poi",
        elementType: "geometry",
        stylers: [
            {hue: "#40E83A"},
            {lightness: 40},
        ]
        }];
    mapoptions= {
        zoom: 16,
        maxZoom: 18,
        minZoom: 14,
        center:mit_coord,
        mapTypeControl: false,
        mapTypeId: MAP_TYPE_ID,
        overviewMapControl: false,
        backgroundColor: '#FFF5D9',
        streetViewControl: false,
    };
    mapStyle = new google.maps.StyledMapType(stylez, {});
    map = new google.maps.Map(mapdiv.get(0), mapoptions);
    map.mapTypes.set(MAP_TYPE_ID, mapStyle);
}

function showCoords(position) {
    my_loc = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
    console.log("Latitude:" + my_loc.lat() + "\nLongitude:" + my_loc.lng());
    if (in_box(my_loc, top_left, bottom_right)){
        me = new google.maps.Marker({
            map: map,
            position: my_loc,
            title:"My Location",
        });
        valid_loc = true;
    }
}
//Function automatically triggered on error
function showError(error) {
    console.log(error.code);
}

function in_box(coord, tl, br){
    return coord.lat() < tl.lat() && coord.lng() > tl.lng() && coord.lat() > br.lat() && coord.lng() < br.lng();
}

//This callback function gets called when a successful location query has been made
var on_loc_query = function(){console.log("location query made" + last_query);};

function query_whereis(loc){
    if (!loc.lat) return false;
    tmp_loc = loc;
    $.ajax({
        type: 'GET',
        url:"http://whereis.mit.edu/search",
        dataType: 'jsonp',
        data: {
            type: 'coord',
            output: 'json',
            q: loc.lng()+','+loc.lat(),
        },
        success: function(data){
            d = data[0];
            last_query={}
            last_query['bldg_img'] = (d.bldgimg) ? d.bldgimg : null;
            last_query['bldg_name'] = d.name;
            last_query['bldg_num'] = d.bldgnum;
            last_query['bldg_loc'] = new google.maps.LatLng(d.lat_wgs84,d.long_wgs84);
            last_query['query_loc'] = tmp_loc;
            on_loc_query();
        }
    });
}

//the click function get an event object with an attr latLng
function add_marker(loc, text, click){
    text = text || "";
    marker = new google.maps.Marker({
        map: map,
        position: loc,
        title: text,
    });
    if (click){
        google.maps.event.addListener(marker, 'click', click);
    }
}

on_loc_query = function(){
    add_marker(last_query['query_loc'], last_query['bldg_name']);
};

$(document).ready(function(){
    navigator.geolocation.getCurrentPosition(showCoords,showError);
    init_map();
    google.maps.event.addListener(map, 'click', function(ob){
        query_whereis(ob.latLng);
    });
});
