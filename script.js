const locations={
  chamoli:{
    name:"Chamoli, Uttarakhand",coords:"30.41° N, 79.32° E",lat:30.41,lng:79.32,
    risk:{thunderstorm:"Moderate",hailstorm:"Low",cloudburst:"High"},
    params:{downburst:"68 km/h",strike:"High",flash:"18 flashes/min",density:"7.4 flashes/km²",temperature:"21 °C",humidity:"78%",cloudDirection:"NW",cloudDensity:"82%",cloudVelocity:"42 km/h",cloudType:"Deep Convective",windSpeed:"42 km/h",windDirection:"NW",monsoon:"Active"},
    validity:"29 Sep 2026, 02:30 PM – 08:30 PM",
    forecast:[["02:30 – 03:30 PM","🌧️","Low","low"],["03:30 – 04:30 PM","⛈️","Moderate","moderate"],["04:30 – 05:30 PM","⛈️","High","high"],["05:30 – 06:30 PM","🌧️","High","high"],["06:30 – 07:30 PM","🌧️","Moderate","moderate"],["07:30 – 08:30 PM","☁️","Low","low"]]
  },
  shimla:{
    name:"Shimla, Himachal Pradesh",coords:"31.10° N, 77.17° E",lat:31.10,lng:77.17,
    risk:{thunderstorm:"High",hailstorm:"Moderate",cloudburst:"Moderate"},
    params:{downburst:"54 km/h",strike:"Moderate",flash:"11 flashes/min",density:"4.9 flashes/km²",temperature:"18 °C",humidity:"72%",cloudDirection:"W",cloudDensity:"69%",cloudVelocity:"48 km/h",cloudType:"Cumulonimbus",windSpeed:"48 km/h",windDirection:"W",monsoon:"Active"},
    validity:"29 Sep 2026, 03:00 PM – 09:00 PM",
    forecast:[["03:00 – 04:00 PM","⛈️","Moderate","moderate"],["04:00 – 05:00 PM","⛈️","High","high"],["05:00 – 06:00 PM","⛈️","High","high"],["06:00 – 07:00 PM","🌧️","High","high"],["07:00 – 08:00 PM","🌧️","Moderate","moderate"],["08:00 – 09:00 PM","☁️","Low","low"]]
  },
  gangtok:{
    name:"Gangtok, Sikkim",coords:"27.33° N, 88.61° E",lat:27.33,lng:88.61,
    risk:{thunderstorm:"Moderate",hailstorm:"High",cloudburst:"High"},
    params:{downburst:"73 km/h",strike:"Very High",flash:"24 flashes/min",density:"9.1 flashes/km²",temperature:"17 °C",humidity:"86%",cloudDirection:"SW",cloudDensity:"91%",cloudVelocity:"36 km/h",cloudType:"Overshooting Top",windSpeed:"36 km/h",windDirection:"SW",monsoon:"Active"},
    validity:"29 Sep 2026, 02:45 PM – 08:45 PM",
    forecast:[["02:45 – 03:45 PM","🌧️","Moderate","moderate"],["03:45 – 04:45 PM","⛈️","High","high"],["04:45 – 05:45 PM","⛈️","Very High","very-high"],["05:45 – 06:45 PM","⛈️","High","high"],["06:45 – 07:45 PM","🌧️","High","high"],["07:45 – 08:45 PM","🌧️","Moderate","moderate"]]
  },
  itanagar:{
    name:"Itanagar, Arunachal Pradesh",coords:"27.08° N, 93.62° E",lat:27.08,lng:93.62,
    risk:{thunderstorm:"High",hailstorm:"Low",cloudburst:"Very High"},
    params:{downburst:"61 km/h",strike:"High",flash:"21 flashes/min",density:"8.2 flashes/km²",temperature:"24 °C",humidity:"84%",cloudDirection:"E",cloudDensity:"88%",cloudVelocity:"31 km/h",cloudType:"Deep Convective",windSpeed:"31 km/h",windDirection:"E",monsoon:"Active"},
    validity:"29 Sep 2026, 03:15 PM – 09:15 PM",
    forecast:[["03:15 – 04:15 PM","🌧️","Moderate","moderate"],["04:15 – 05:15 PM","⛈️","High","high"],["05:15 – 06:15 PM","⛈️","Very High","very-high"],["06:15 – 07:15 PM","⛈️","Very High","very-high"],["07:15 – 08:15 PM","🌧️","High","high"],["08:15 – 09:15 PM","🌧️","Moderate","moderate"]]
  }
};

const map=L.map("map",{zoomControl:true}).setView([29.8,82.4],5.7);
const satellite=L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",{maxZoom:18,attribution:"Tiles © Esri"}).addTo(map);
const terrain=L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",{maxZoom:17,attribution:"© OpenTopoMap contributors"});
const street=L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap contributors"});

const stormAreas=[
  [[30.25,78.9],[30.8,79.1],[30.65,79.65],[30.1,79.5]],
  [[28.0,93.0],[27.7,93.8],[27.2,93.55],[27.45,92.8]],
  [[27.0,88.2],[27.5,88.4],[27.6,89.0],[27.1,89.1]]
];
stormAreas.forEach(function(points,i){
  L.polygon(points,{color:"transparent",fillColor:i===0?"#f36b32":"#f4c23e",fillOpacity:.28,weight:0}).addTo(map);
});

const labelData=[
  ["JAMMU & KASHMIR",34.2,75.3],["LADAKH",34.3,78.1],["HIMACHAL\nPRADESH",31.8,77.2],
  ["PUNJAB",31.0,75.3],["HARYANA",29.2,76.0],["DELHI",28.6,77.2],["RAJASTHAN",27.2,73.8],
  ["UTTAR PRADESH",27.3,80.6],["UTTARAKHAND",30.2,79.3],["BIHAR",25.8,85.3],["SIKKIM",27.5,88.5],
  ["ARUNACHAL\nPRADESH",28.5,94.0],["ASSAM",26.1,92.6],["NAGALAND",26.2,94.4],
  ["MANIPUR",24.9,93.8],["MEGHALAYA",25.6,91.4]
];
labelData.forEach(function(x){
  L.marker([x[1],x[2]],{interactive:false,icon:L.divIcon({
    className:"map-state-label",html:x[0].replace("\n","<br>"),iconSize:[100,30],iconAnchor:[50,15]
  })}).addTo(map);
});

const marker=L.marker([locations.chamoli.lat,locations.chamoli.lng]).addTo(map);

function riskClass(value){
  const v=value.toLowerCase().replace(/\s+/g,"-");
  if(v==="low")return "low";
  if(v==="moderate")return "moderate";
  if(v==="high")return "high";
  return "very-high";
}

function findLocation(q){
  q=(q||"").trim().toLowerCase();
  if(!q)return null;
  return Object.keys(locations).find(function(k){
    const name=locations[k].name.toLowerCase();
    const city=name.split(",")[0].trim();
    return k===q || city===q || name===q || name.includes(q) || q.includes(k);
  });
}

function selectLocation(key){
  const x=locations[key];
  if(!x)return;
  document.getElementById("selectedLocation").textContent=x.name;
  document.getElementById("coordinates").textContent=x.coords;
  document.getElementById("thunderstormRisk").textContent=x.risk.thunderstorm;
  document.getElementById("thunderstormRisk").className=riskClass(x.risk.thunderstorm);
  document.getElementById("hailstormRisk").textContent=x.risk.hailstorm;
  document.getElementById("hailstormRisk").className=riskClass(x.risk.hailstorm);
  document.getElementById("cloudburstRisk").textContent=x.risk.cloudburst;
  document.getElementById("cloudburstRisk").className=riskClass(x.risk.cloudburst);
  document.getElementById("validityTime").textContent="("+x.validity+")";
  document.getElementById("cloudTemp").textContent=x.params.temp;
  document.getElementById("cloudHeight").textContent=x.params.height;
  document.getElementById("precipIntensity").textContent=x.params.precip;
  document.getElementById("cloudType").textContent=x.params.cloud;
  document.getElementById("windSpeed").textContent=x.params.wind;
  document.getElementById("windDirection").textContent=x.params.direction;
  document.getElementById("forecastGrid").innerHTML=x.forecast.map(function(item){
    return '<div class="forecast-item"><div class="time">'+item[0]+'</div><div class="wx">'+item[1]+'</div><span class="level '+item[3]+'">'+item[2]+'</span></div>';
  }).join("");
  marker.setLatLng([x.lat,x.lng]);
  map.flyTo([x.lat,x.lng],8,{duration:1});
}

function searchDashboard(){
  const key=findLocation(document.getElementById("locationSearch").value);
  if(key)selectLocation(key);
}

document.getElementById("searchBtn").onclick=searchDashboard;
document.getElementById("locationSearch").addEventListener("keydown",function(e){
  if(e.key==="Enter")searchDashboard();
});

document.querySelectorAll(".tab").forEach(function(btn){
  btn.onclick=function(){
    document.querySelectorAll(".tab").forEach(function(b){b.classList.remove("active")});
    btn.classList.add("active");
    const mode=btn.dataset.mode;
    if(mode==="nowcast"||mode==="satellite"){
      if(!map.hasLayer(satellite))map.addLayer(satellite);
      if(map.hasLayer(terrain))map.removeLayer(terrain);
      if(map.hasLayer(street))map.removeLayer(street);
    }else{
      if(!map.hasLayer(street))map.addLayer(street);
      if(map.hasLayer(satellite))map.removeLayer(satellite);
      if(map.hasLayer(terrain))map.removeLayer(terrain);
    }
  };
});

const initialLocation=findLocation(new URLSearchParams(window.location.search).get("location"))||"chamoli";
selectLocation(initialLocation);