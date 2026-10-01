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
    params:{downburst:"86 km/h",strike:"Very High",flash:"32 flashes/min",density:"12.8 flashes/km²",temperature:"25 °C",humidity:"91%",cloudDirection:"NW",cloudDensity:"97%",cloudVelocity:"74 km/h",cloudType:"Overshooting Top",windSpeed:"81 km/h",windDirection:"NW",monsoon:"Active"},
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
const street=L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap contributors"});
let radarLayer=null;

const stormOverlays=[];
const stormAreas=[
  [[30.25,78.9],[30.8,79.1],[30.65,79.65],[30.1,79.5]],
  [[28.0,93.0],[27.7,93.8],[27.2,93.55],[27.45,92.8]],
  [[27.0,88.2],[27.5,88.4],[27.6,89.0],[27.1,89.1]]
];
stormAreas.forEach(function(points,i){
  stormOverlays.push(L.polygon(points,{color:"transparent",fillColor:i===0?"#f36b32":"#f4c23e",fillOpacity:.28,weight:0}));
  stormOverlays[stormOverlays.length-1].addTo(map);
});

const labelData=[["JAMMU & KASHMIR",34.2,75.3],["LADAKH",34.3,78.1],["HIMACHAL PRADESH",31.8,77.2],["PUNJAB",31.0,75.3],["HARYANA",29.2,76.0],["DELHI",28.6,77.2],["RAJASTHAN",27.2,73.8],["UTTAR PRADESH",27.3,80.6],["UTTARAKHAND",30.2,79.3],["BIHAR",25.8,85.3],["SIKKIM",27.5,88.5],["ARUNACHAL PRADESH",28.5,94.0],["ASSAM",26.1,92.6],["NAGALAND",26.2,94.4],["MANIPUR",24.9,93.8],["MEGHALAYA",25.6,91.4]];
labelData.forEach(function(x){
  L.marker([x[1],x[2]],{interactive:false,icon:L.divIcon({
    className:"map-state-label",html:x[0].replace("\n","<br>"),iconSize:[100,30],iconAnchor:[50,15]
  })}).addTo(map);
});

const marker=L.marker([locations.chamoli.lat,locations.chamoli.lng]).addTo(map);
marker.bindTooltip(locations.chamoli.name,{direction:"top",offset:[0,-8]});

function byId(id){
  return document.getElementById(id);
}

function hideRadar(){
  if(radarLayer&&map.hasLayer(radarLayer))map.removeLayer(radarLayer);
}

async function showRadar(){
  hideRadar();
  try{
    const response=await fetch("https://api.rainviewer.com/public/weather-maps.json",{cache:"no-store"});
    if(!response.ok)throw new Error("Radar service unavailable");
    const data=await response.json();
    const frames=data.radar&&data.radar.past;
    const frame=frames&&frames[frames.length-1];
    if(!data.host||!frame||!frame.path)throw new Error("No radar frame available");
    radarLayer=L.tileLayer(
      data.host+frame.path+"/256/{z}/{x}/{y}/2/1_1.png",
      {tileSize:256,maxNativeZoom:7,maxZoom:8,opacity:.68,attribution:"Weather data © RainViewer"}
    ).addTo(map);
  }catch(error){
    console.warn("Radar View unavailable:",error);
  }
}

function setText(id,value){
  const el=byId(id);
  if(el)el.textContent=value;
}

function setParamValue(id,value){
  const el=byId(id);
  if(!el)return;
  el.textContent=value;
  el.classList.remove(
    "value-low","value-moderate","value-high","value-very-high",
    "value-active","value-inactive","value-normal","value-clear",
    "value-elevated","value-critical"
  );
  const v=String(value||"").toLowerCase().trim().replace(/\s+/g,"-");
  if(v==="low"||v==="normal"||v==="clear"||v==="inactive"){
    el.classList.add(
      v==="low"?"value-low":
      v==="normal"?"value-normal":
      v==="clear"?"value-clear":"value-inactive"
    );
  }else if(v==="moderate"||v==="elevated"){
    el.classList.add(v==="moderate"?"value-moderate":"value-elevated");
  }else if(v==="high"||v==="active"){
    el.classList.add(v==="high"?"value-high":"value-active");
  }else if(v==="very-high"||v==="critical"){
    el.classList.add(v==="very-high"?"value-very-high":"value-critical");
  }
}

function formatTime(date){
  return date.toLocaleTimeString("en-IN",{hour:"2-digit",minute:"2-digit",hour12:true});
}

function formatDateTime(date){
  return date.toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"})+", "+formatTime(date);
}

function getUpdatedTime(){
  return new Date(Date.now()-30*60*1000);
}

function addHours(date,hours){
  return new Date(date.getTime()+hours*60*60*1000);
}

let currentLocationKey="chamoli";

function renderTimeWindow(locationData){
  const updated=getUpdatedTime();
  setText("lastUpdatedTime",formatDateTime(updated));
  setText("validityTime","("+formatDateTime(updated)+" – "+formatDateTime(addHours(updated,6))+")");

  const forecastGrid=byId("forecastGrid");
  if(forecastGrid&&locationData&&locationData.forecast){
    forecastGrid.innerHTML=locationData.forecast.map(function(item,index){
      const start=addHours(updated,index);
      const end=addHours(updated,index+1);
      const severityIcon={low:"☁️",moderate:"🌧️",high:"⛈️","very-high":"🌩️"}[item[3]]||item[1];
      return '<div class="forecast-item"><div class="time">'+formatTime(start)+" – "+formatTime(end)+'</div><div class="wx">'+severityIcon+'</div><span class="level '+item[3]+'">'+item[2]+'</span></div>';
    }).join("");
  }
}

function riskClass(value){
  const v=String(value||"").toLowerCase().replace(/\s+/g,"-");
  if(v==="low")return "low";
  if(v==="moderate")return "moderate";
  if(v==="high")return "high";
  if(v==="very-high")return "very-high";
  return "";
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

  setText("selectedLocation",x.name);
  setText("coordinates",x.coords);
  setText("thunderstormRisk",x.risk.thunderstorm);
  setText("hailstormRisk",x.risk.hailstorm);
  setText("cloudburstRisk",x.risk.cloudburst);

  const thunderstorm=byId("thunderstormRisk");
  const hailstorm=byId("hailstormRisk");
  const cloudburst=byId("cloudburstRisk");
  if(thunderstorm)thunderstorm.className=riskClass(x.risk.thunderstorm);
  if(hailstorm)hailstorm.className=riskClass(x.risk.hailstorm);
  if(cloudburst)cloudburst.className=riskClass(x.risk.cloudburst);

  currentLocationKey=key;
  renderTimeWindow(x);
  setParamValue("downburstVelocity",x.params.downburst);
  setParamValue("lightningStrikeIntensity",x.params.strike);
  setParamValue("lightningFlashRate",x.params.flash);
  setParamValue("lightningDensity",x.params.density);
  setParamValue("temperature",x.params.temperature);
  setParamValue("humidity",x.params.humidity);
  setParamValue("cloudDirection",x.params.cloudDirection);
  setParamValue("cloudDensity",x.params.cloudDensity);
  setParamValue("cloudVelocity",x.params.cloudVelocity);
  setParamValue("cloudType",x.params.cloudType);
  setParamValue("windSpeed",x.params.windSpeed);
  setParamValue("windDirection",x.params.windDirection);
  setParamValue("monsoonStatus",x.params.monsoon);

  if(key==="shimla"){
    const cloudType=byId("cloudType");
    if(cloudType)cloudType.classList.add("value-very-high");
  }

  const search=byId("locationSearch");
  if(search){
    search.value=x.name;
    search.setCustomValidity("");
  }

  marker.setLatLng([x.lat,x.lng]);
  marker.setTooltipContent(x.name);
  map.flyTo([x.lat,x.lng],8,{duration:1});
  setTimeout(function(){map.invalidateSize();},250);
}

function searchDashboard(){
  const input=byId("locationSearch");
  const key=findLocation(input ? input.value : "");
  if(key){
    selectLocation(key);
  }else if(input && input.value.trim()){
    input.setCustomValidity("Supported demo locations: Chamoli, Shimla, Gangtok, Itanagar.");
    input.reportValidity();
  }
}

byId("searchBtn").onclick=searchDashboard;
byId("locationSearch").addEventListener("keydown",function(e){
  if(e.key==="Enter"){
    e.preventDefault();
    searchDashboard();
  }
});

document.querySelectorAll(".tab").forEach(function(btn){
  btn.onclick=function(){
    document.querySelectorAll(".tab").forEach(function(b){b.classList.remove("active")});
    btn.classList.add("active");
    const mode=btn.dataset.mode;

    if(mode==="satellite"){
      if(!map.hasLayer(satellite))map.addLayer(satellite);
      if(map.hasLayer(street))map.removeLayer(street);
      hideRadar();
    }else if(mode==="radar"){
      if(!map.hasLayer(street))map.addLayer(street);
      if(map.hasLayer(satellite))map.removeLayer(satellite);
      showRadar();
    }

    stormOverlays.forEach(function(layer){
      const shouldShow=mode==="satellite";
      const has=map.hasLayer(layer);
      if(shouldShow&&!has)map.addLayer(layer);
      if(!shouldShow&&has)map.removeLayer(layer);
    });
    setTimeout(function(){map.invalidateSize();},100);
  };
});

const initialLocation=findLocation(new URLSearchParams(window.location.search).get("location"))||"chamoli";
selectLocation(initialLocation);
setInterval(function(){
  renderTimeWindow(locations[currentLocationKey]);
},60000);
