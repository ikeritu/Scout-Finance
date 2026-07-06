# Scout Finance ? v2.5F NYSE Endpoint Candidate Validation

- Phase: v2.5F
- Method: nyse_endpoint_candidate_validation_v1
- Created at: 2026-07-06T08:44:28+00:00
- Validation status: **NYSE_ENDPOINT_CANDIDATE_VALIDATION_JS_HINTS_FOUND**
- Readiness score: **70/100**
- Usability decision: **REQUIRES_DEEP_JS_PAYLOAD_REVIEW**
- Endpoint candidate: `https://www.nyse.com/api/sites/nyse/proxy`
- Endpoint status: **ENDPOINT_HTTP_FAILED**
- Endpoint HTTP OK: False
- Endpoint status code: 404
- Endpoint content type: `text/html; charset=utf-8`
- Endpoint response size bytes: 69809
- JS candidates available: 11
- JS assets inspected: 8
- JS findings: 143

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Network download performed: true
- Active outputs overwritten: false
- Expanded universe rebuilt: false

## Endpoint validation

- URL: `https://www.nyse.com/api/sites/nyse/proxy`
- Status: **ENDPOINT_HTTP_FAILED**
- Response sample: `outputs/full_universe_source_acquisition/nyse_endpoint_candidate_validation_proxy_response_v2_5f.txt`

## JavaScript assets inspected

- `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/01_Spinner-DwaMFcMk.js` ? ok: True ? status: 200 ? matches: 5
- `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? ok: True ? status: 200 ? matches: 16
- `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/03_main-Bg6Hb68w.js` ? ok: True ? status: 200 ? matches: 11
- `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/04_meta-BWKtRhNE.js` ? ok: True ? status: 200 ? matches: 11
- `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/05_replace-IbWvJqX2.js` ? ok: True ? status: 200 ? matches: 2
- `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/06_index-js-commonjs-es-import-N9QxKcO-.js` ? ok: True ? status: 200 ? matches: 2
- `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/07_index-js-commonjs-proxy-CNaJNpJV.js` ? ok: True ? status: 200 ? matches: 6
- `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/08_BreadCrumbContext-DDWejWVZ.js` ? ok: True ? status: 200 ? matches: 0

## JS findings

- `symbol` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/01_Spinner-DwaMFcMk.js` ? }},P=c.createContext(!1);var X=function(e,t){var n={};for(var r in e)Object.prototype.hasOwnProperty.call(e,r)&&t.indexOf(r)<0&&(n[r]=e[r]);if(e!=null&&typeof Object.getOwnPropertySymbols=="function")for(var o=0,r=Object.getOwnPropertySymbols(e);o<r.length;o++)t.indexOf(r[o])<0&&Object.prototype.propertyIsEnumerable.call(e,r[o])&&(n[r[o]]=e[r[o]]);return n};const
- `symbol` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/01_Spinner-DwaMFcMk.js` ? or(var r in e)Object.prototype.hasOwnProperty.call(e,r)&&t.indexOf(r)<0&&(n[r]=e[r]);if(e!=null&&typeof Object.getOwnPropertySymbols=="function")for(var o=0,r=Object.getOwnPropertySymbols(e);o<r.length;o++)t.indexOf(r[o])<0&&Object.prototype.propertyIsEnumerable.call(e,r[o])&&(n[r[o]]=e[r[o]]);return n};const j=c.forwardRef((e,t)=>{var{dock:n={},grow:r,intent:o="d
- `symbol` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/01_Spinner-DwaMFcMk.js` ? );j.displayName="Button";var G=function(e,t){var n={};for(var r in e)Object.prototype.hasOwnProperty.call(e,r)&&t.indexOf(r)<0&&(n[r]=e[r]);if(e!=null&&typeof Object.getOwnPropertySymbols=="function")for(var o=0,r=Object.getOwnPropertySymbols(e);o<r.length;o++)t.indexOf(r[o])<0&&Object.prototype.propertyIsEnumerable.call(e,r[o])&&(n[r[o]]=e[r[o]]);return n};const
- `payload` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/01_Spinner-DwaMFcMk.js` ? tener("load",h),p.addEventListener("error",()=>g(new Error("Unable to preload CSS for ".concat(u))))})}))}function i(l){const a=new Event("vite:preloadError",{cancelable:!0});if(a.payload=l,window.dispatchEvent(a),!a.defaultPrevented)throw l}return o.then(l=>{for(const a of l||[])a.status==="rejected"&&i(a.reason);return t().catch(i)})},te=({title:e,grow:t,hasError
- `query` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/01_Spinner-DwaMFcMk.js` ? eturn Promise.all(u.map(f=>Promise.resolve(f).then(m=>({status:"fulfilled",value:m}),m=>({status:"rejected",reason:m}))))};const l=document.getElementsByTagName("link"),a=document.querySelector("meta[property=csp-nonce]"),d=(a==null?void 0:a.nonce)||(a==null?void 0:a.getAttribute("nonce"));o=v(n.map(u=>{if(u=ee(u,r),u in L)return;L[u]=!0;const f=u.endsWith(".css"
- `query` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/01_Spinner-DwaMFcMk.js` ? n;L[u]=!0;const f=u.endsWith(".css"),m=f?'[rel="stylesheet"]':"";if(r)for(let h=l.length-1;h>=0;h--){const g=l[h];if(g.href===u&&(!f||g.rel==="stylesheet"))return}else if(document.querySelector('link[href="'.concat(u,'"]').concat(m)))return;const p=document.createElement("link");if(p.rel=f?"stylesheet":Z,f||(p.as="script"),p.crossOrigin="",p.href=u,d&&p.setAttrib
- `GET` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/01_Spinner-DwaMFcMk.js` ? eRoot,w}var ae=U();const V=e=>t=>{var n,r,o;if(e.href){if(t.stopPropagation(),(n=e.onClick)===null||n===void 0||n.call(e,t),e.href&&!t.isDefaultPrevented()){const i=(r=t.currentTarget)===null||r===void 0?void 0:r.closest("a");(i==null?void 0:i.getAttribute("href"))===e.href?i.click():(o=t.currentTarget.ownerDocument.defaultView)===null||o===void 0||o.location.a
- `GET` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/01_Spinner-DwaMFcMk.js` ? Propagation(),(n=e.onClick)===null||n===void 0||n.call(e,t),e.href&&!t.isDefaultPrevented()){const i=(r=t.currentTarget)===null||r===void 0?void 0:r.closest("a");(i==null?void 0:i.getAttribute("href"))===e.href?i.click():(o=t.currentTarget.ownerDocument.defaultView)===null||o===void 0||o.location.assign(e.href)}t.preventDefault()}},P=c.createContext(!1);var X=f
- `GET` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/01_Spinner-DwaMFcMk.js` ? ,t),e.href&&!t.isDefaultPrevented()){const i=(r=t.currentTarget)===null||r===void 0?void 0:r.closest("a");(i==null?void 0:i.getAttribute("href"))===e.href?i.click():(o=t.currentTarget.ownerDocument.defaultView)===null||o===void 0||o.location.assign(e.href)}t.preventDefault()}},P=c.createContext(!1);var X=function(e,t){var n={};for(var r in e)Object.prototype.ha
- `proxy` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/01_Spinner-DwaMFcMk.js` ? os-BOS4m3ic.js";import{f as F,Q as M,e as z}from"../../../../../../../../../../node_modules/-pnpm/react-router@6-30-1_react@18-3-1/node_modules/react-router/dist/index-js-commonjs-proxy-CNaJNpJV.js";var w={},N;function U(){if(N)return w;N=1;var e=B();return w.createRoot=e.createRoot,w.hydrateRoot=e.hydrateRoot,w}var ae=U();const V=e=>t=>{var n,r,o;if(e.href){if(t
- `instrument` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? "Real-Time Services Developer Support",null,null,null,null,null,null,null,null,null],["Reference Data",null,null,null,"We provide reference data for more than 35 million financial instruments, tracking key data points such as terms and conditions, corporate actions, entity linkages and identification information. For thousands of commercial market participants, our re
- `instrument` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? isplayName:"Basic Demo",content:{id:a(),name:"cms-component-quote-2025",props:{}}}},c2={basic:{displayName:"Basic Demo",content:{id:a(),name:"cms-component-quote-directory",props:{instrumentType:"EXCHANGE_TRADED_FUND",perPage:50}}}},d2={basic:{displayName:"Basic Demo",content:{id:a(),name:"cms-component-raw-html",props:{html:"</div></div></div></div><div id='counter'>
- `instruments` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? "Real-Time Services Developer Support",null,null,null,null,null,null,null,null,null],["Reference Data",null,null,null,"We provide reference data for more than 35 million financial instruments, tracking key data points such as terms and conditions, corporate actions, entity linkages and identification information. For thousands of commercial market participants, our ref
- `symbol` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? default"&&!(u in r)){const g=Object.getOwnPropertyDescriptor(m,u);g&&Object.defineProperty(r,u,g.get?g:{enumerable:!0,get:()=>m[u]})}}}return Object.freeze(Object.defineProperty(r,Symbol.toStringTag,{value:"Module"}))}var cA=typeof globalThis<"u"?globalThis:typeof window<"u"?window:typeof global<"u"?global:typeof self<"u"?self:{};function Yt(r){return r&&r.__esMod
- `symbol` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? ;Object.defineProperty(c,m,u.get?u:{enumerable:!0,get:function(){return r[m]}})}),c}var Rl={exports:{}},yi={},ql={exports:{}},re={};var tm;function y0(){if(tm)return re;tm=1;var r=Symbol.for("react.element"),s=Symbol.for("react.portal"),c=Symbol.for("react.fragment"),m=Symbol.for("react.strict_mode"),u=Symbol.for("react.profiler"),g=Symbol.for("react.provider"),k=
- `symbol` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? et?u:{enumerable:!0,get:function(){return r[m]}})}),c}var Rl={exports:{}},yi={},ql={exports:{}},re={};var tm;function y0(){if(tm)return re;tm=1;var r=Symbol.for("react.element"),s=Symbol.for("react.portal"),c=Symbol.for("react.fragment"),m=Symbol.for("react.strict_mode"),u=Symbol.for("react.profiler"),g=Symbol.for("react.provider"),k=Symbol.for("react.context"),b=
- `ticker` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? aptchaPublicKey:"6LcqnCgTAAAAAKyKekTRZEQ-UJltAbojrJHo5ynM"}}}},o1={basic:{displayName:"Basic Demo",content:{id:a(),name:"cms-component-global-giving",props:{source:[{name:"Amazon",ticker:"AMZN",companyUrl:"https://sustainability.aboutamazon.com/social/community",charity:"Amazon Community Impact",charityUrl:"https://sustainability.aboutamazon.com/social/community",
- `ticker` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? tamazon.com/social/community",description:"Amazon invests in Amazon Community Impact programs that support local communities and disaster relief efforts."},{name:"Bank of America",ticker:"BAC",companyUrl:"https://about.bankofamerica.com/en/making-an-impact",charity:"Bank of America Charitable Foundation",charityUrl:"https://about.bankofamerica.com/en/making-an-imp
- `ticker` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? famerica.com/en/making-an-impact",description:"Bank of America supports the Bank of America Charitable Foundation to advance economic opportunity in communities."},{name:"Chevron",ticker:"CVX",companyUrl:"https://www.chevron.com/sustainability/social",charity:"Chevron Community Engagement",charityUrl:"https://www.chevron.com/sustainability/social",description:"Che
- `exchange` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? e:"Basic Demo",content:{id:a(),name:"cms-component-bigfoot",props:{siteName:"ice",sectionRows:[{id:a(),sections:[{id:a(),showOnMobile:!0,links:[{id:a(),href:"#",title:"Markets and Exchanges"},{id:a(),href:"#",title:"Fixed Income and Data Services"},{id:a(),href:"#",title:"Mortgage Technology"},{id:a(),href:"#",title:"Benchmark Administration"}]},{id:a(),title:"Tools
- `exchange` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? ink",title:"Link",isButton:!1},{id:a(),href:"#link",title:"Link - Desktop Only",isButton:!1,hideOnMobile:!0}],menus:[{id:a(),title:"Solutions",baseUrl:"/",sections:[{id:"solutions-exchanges",href:"#",title:"Exchanges",links:[{id:a(),href:"#",title:"Markets"},{id:a(),href:"#",title:"Clearing"},{id:a(),href:"#",title:"Services",iconPath:"https://www.ice.com/publicdocs
- `exchange` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? !1},{id:a(),href:"#link",title:"Link - Desktop Only",isButton:!1,hideOnMobile:!0}],menus:[{id:a(),title:"Solutions",baseUrl:"/",sections:[{id:"solutions-exchanges",href:"#",title:"Exchanges",links:[{id:a(),href:"#",title:"Markets"},{id:a(),href:"#",title:"Clearing"},{id:a(),href:"#",title:"Services",iconPath:"https://www.ice.com/publicdocs/nyse/data/NYSE-Connect_Ico
- `quote` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? ein is subject to change and does not constitute any form of warranty, representation, or undertaking",onetrustCategoryId:"C0001"},{id:"f45c014c-01e5-4873-b4af-abe0dc50ce8f",type:"quote",quote:"For decades I have been trying to break through my barriers to writing, always with meager results. But there is something about your approach that works for me like nothi
- `quote` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? subject to change and does not constitute any form of warranty, representation, or undertaking",onetrustCategoryId:"C0001"},{id:"f45c014c-01e5-4873-b4af-abe0dc50ce8f",type:"quote",quote:"For decades I have been trying to break through my barriers to writing, always with meager results. But there is something about your approach that works for me like nothing else
- `quote` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? s-component-plain-text",props:{text:"This is the content for tab 3. Iste esse ut soluta aliquid quis aspernatur rerum et. Sed rerum unde. Quasi dolores earum dolorem."}}]}}}},blockquote:{displayName:"Blockquote",content:{id:a(),name:"cms-component-carousel-2022",props:{minHeight:100,maxHeight:300,variant:"blockquote",showControls:!0,showIndicators:!0,slides:[{id:
- `equity` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? raded crude and refined oil futures contracts; leading global natural gas markets"}]},{type:"list-item",children:[{text:"Operates the leading and most liquid group of equities and equity options exchanges: NYSE Group which saw $308 billion in capital raised in 2020 Global benchmarks in energy, ags, interest rates, FX and equity indexes"}]},{type:"list-item",childr
- `equity` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? nd most liquid group of equities and equity options exchanges: NYSE Group which saw $308 billion in capital raised in 2020 Global benchmarks in energy, ags, interest rates, FX and equity indexes"}]},{type:"list-item",children:[{text:"The world's leading clearer of energy and soft commodities futures and credit default"}]}]}],slots:{}}}]}}}],"929fa70e-311a-4dee-91b
- `equity` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? etime"}],yAxis:[{id:a(),title:{text:"Weight"},type:"linear",labels:{format:"{value:.0f}"}}],tooltip:{pointFormat:"{series.name}: {point.y:.2f}"},series:[{id:"eq",type:"area",name:"Equity",color:"#71c5e8"},{id:"10y",type:"area",name:"10Y Treasury",color:"#235F73"},{id:"usd",type:"area",name:"USD/Currency",color:"#4E4E4E"},{id:"gld",type:"area",name:"Gold",color:"#C
- `stock` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? mmunication Services",y:.052}]}],chart:{type:"bar"},title:{text:"There is no height setting for the chart"},className:"chart1"}}},nybacPerformance:{displayName:"NYBAC Performance (Stock Chart + Period Return)",content:{id:a(),name:"cms-component-chart",props:{useStockChart:!0,showPeriodReturn:!0,baseConfig:{chart:{type:"area"},title:{text:"NYSE Bonds & Commoditie
- `stock` in `data/raw/source_providers/nyse_listed_directory/endpoint_validation_js/02_demos-BOS4m3ic.js` ? setting for the chart"},className:"chart1"}}},nybacPerformance:{displayName:"NYBAC Performance (Stock Chart + Period Return)",content:{id:a(),name:"cms-component-chart",props:{useStockChart:!0,showPeriodReturn:!0,baseConfig:{chart:{type:"area"},title:{text:"NYSE Bonds & Commodities Index (NYBAC)"},subtitle:{text:"Data as of {{lastDate}}"},xAxis:[{id:a(),title:{t

## Positives

- v2.5E discovery artifact found: outputs/full_universe_source_acquisition/nyse_endpoint_discovery_review_v2_5e.json
- v2.5E discovery status accepted: NYSE_ENDPOINT_DISCOVERY_API_CANDIDATE_FOUND
- Candidate CSV loaded: 39 candidates
- API candidates available: 1
- JavaScript candidates available: 11
- JS findings detected: 143

## Blockers

- No blockers detected.

## Warnings

- Endpoint request failed: HTTPError 404: Not Found
- Endpoint candidate did not return OK: HTTPError 404: Not Found

## Recommendation

Proceed to v2.5G to decide whether NYSE remains raw-only, requires deeper JS payload review, or can become a provider after schema review.

Important: v2.5F validates endpoint and JS candidates only. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.