(function(){
  "use strict";

  /* ================= progress bar + scrollspy ================= */
  var sections = Array.prototype.slice.call(document.querySelectorAll('section, header.hero'));
  var progressBar = document.getElementById('progressBar');
  var topLinks = document.querySelectorAll('.topnav a');
  var dotLinks = document.querySelectorAll('.dotnav a');

  function onScroll(){
    var h = document.documentElement;
    var scrolled = h.scrollTop || document.body.scrollTop;
    var height = (h.scrollHeight || document.body.scrollHeight) - h.clientHeight;
    progressBar.style.width = (height > 0 ? (scrolled/height*100) : 0) + '%';

    var current = sections[0] ? sections[0].id : '';
    sections.forEach(function(sec){
      var rect = sec.getBoundingClientRect();
      if(rect.top <= 140) current = sec.id;
    });
    topLinks.forEach(function(a){ a.classList.toggle('active', a.dataset.sec === current); });
    dotLinks.forEach(function(a){ a.classList.toggle('active', a.dataset.sec === current); });
  }
  window.addEventListener('scroll', onScroll, {passive:true});
  onScroll();

  /* ================= mobile nav ================= */
  var burger = document.getElementById('burger');
  var topnav = document.getElementById('topnav');
  burger.addEventListener('click', function(){ topnav.classList.toggle('open'); });
  topLinks.forEach(function(a){ a.addEventListener('click', function(){ topnav.classList.remove('open'); }); });

  /* ================= reveal on scroll ================= */
  // rootMargin duong o day "mo rong" vung tinh giao cat xuong duoi man
  // hinh 220px - khoi .reveal duoc coi la "da vao khung nhin" va bat dau
  // hien ra TRUOC khi nguoi dung thuc su cuon toi do, nen luc cuon toi
  // noi dung da hien san, khong con khoang trong cho hieu ung fade-in
  // chay kip nhu truoc (threshold thap + rootMargin duong).
  var revealEls = document.querySelectorAll('.reveal');
  if(window.IntersectionObserver){
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){ if(en.isIntersecting){ en.target.classList.add('in'); io.unobserve(en.target); } });
    }, {threshold:.01, rootMargin:'0px 0px 220px 0px'});
    revealEls.forEach(function(el){ io.observe(el); });
  } else {
    revealEls.forEach(function(el){ el.classList.add('in'); });
  }

  /* ================= hero dial ================= */
  var heroMap = {0:{bit:0,basis:'+',label:'ngang/dọc'}, 45:{bit:0,basis:'x',label:'chéo'}, 90:{bit:1,basis:'+',label:'ngang/dọc'}, 135:{bit:1,basis:'x',label:'chéo'}};
  var heroBtns = document.querySelectorAll('.dial-btn');
  var heroNeedle = document.getElementById('needle');
  var heroReadout = document.getElementById('dialReadout');
  function setHero(angle){
    heroNeedle.style.transform = 'rotate(' + angle + 'deg)';
    var m = heroMap[angle];
    heroReadout.innerHTML = 'Góc <b>' + angle + '&deg;</b> — basis <b>' + m.label + '</b> — mã hoá bit <b>' + m.bit + '</b>';
    heroBtns.forEach(function(b){ b.classList.toggle('active', Number(b.dataset.angle) === angle); });
  }
  heroBtns.forEach(function(b){ b.addEventListener('click', function(){ setHero(Number(b.dataset.angle)); }); });
  setHero(0);

  /* ================= malus's law demo ================= */
  var malusSlider = document.getElementById('malusSlider');
  var malusAngleLabel = document.getElementById('malusAngleLabel');
  var malusIntensity = document.getElementById('malusIntensity');
  var malusCallout = document.getElementById('malusCallout');
  var beamFill = document.getElementById('beamFill');
  var filter2line = document.getElementById('filter2line');

  function updateMalus(){
    var deg = Number(malusSlider.value);
    var rad = deg * Math.PI / 180;
    var intensity = Math.pow(Math.cos(rad), 2);
    malusAngleLabel.textContent = deg + '°';
    malusIntensity.textContent = Math.round(intensity*100) + '%';
    beamFill.style.opacity = Math.max(intensity, 0.06);
    filter2line.style.transform = 'rotate(' + deg + 'deg)';
    var note;
    if(deg === 0) note = 'Hai kính cùng hướng — ánh sáng truyền qua gần như trọn vẹn, tương ứng lúc Bob đo đúng basis Alice đã dùng.';
    else if(deg === 90) note = 'Hai kính vuông góc — gần như không có ánh sáng lọt qua, đúng bằng khoảng cách giữa hai basis vuông góc trong BB84 (⊕ và ✕).';
    else if(deg > 40 && deg < 50) note = 'Ở 45°, khoảng một nửa ánh sáng lọt qua — đây chính là lý do đo sai basis cho kết quả 50/50 ngẫu nhiên.';
    else note = 'Cường độ giảm dần theo cos²(Δθ) khi hai kính lệch hướng.';
    malusCallout.textContent = note;
  }
  malusSlider.addEventListener('input', updateMalus);
  updateMalus();

  /* ================= protocol stepper ================= */
  var steps = [
    {t:'Sinh khoá thô', d:'Alice sinh một chuỗi bit ngẫu nhiên và, độc lập, một chuỗi basis ngẫu nhiên (⊕ hoặc ✕) cho từng bit — cả hai chuỗi này ban đầu chỉ Alice biết.'},
    {t:'Servo mã hoá góc', d:'Ứng với mỗi cặp (bit, basis), phần mềm tra ra một trong bốn góc 0/45/90/135° rồi ra lệnh cho ESP32 xoay servo tới đúng góc đó.'},
    {t:'Truyền qua kênh quang', d:'Trạng thái góc được &quot;phát&quot; đi. Trong thiết bị thật đây là bước Alice gửi dữ liệu qua TCP Socket tới máy Sơn trong cùng mạng LAN.'},
    {t:'Bob đo bằng LDR', d:'Bob tự chọn một basis ngẫu nhiên của riêng mình — độc lập với Alice — rồi đọc cảm biến LDR để suy ra bit, dựa trên góc kỳ vọng của basis đó.'},
    {t:'So sánh basis (sifting)', d:'Hai bên công khai so sánh basis đã dùng cho từng bit — không tiết lộ giá trị bit — và chỉ giữ lại những vị trí basis trùng nhau.'},
    {t:'Ước lượng QBER & dùng khoá', d:'Một phần khoá được công khai so sánh để tính QBER. Nếu dưới ngưỡng an toàn, phần khoá còn lại được dùng làm keystream mã hoá/giải mã ảnh bằng XOR.'}
  ];
  var stepTabs = document.getElementById('stepTabs');
  var stepNumBg = document.getElementById('stepNumBg');
  var stepTitle = document.getElementById('stepTitle');
  var stepDesc = document.getElementById('stepDesc');
  var stepPrev = document.getElementById('stepPrev');
  var stepNext = document.getElementById('stepNext');
  var curStep = 0;

  steps.forEach(function(s, i){
    var b = document.createElement('button');
    b.className = 'step-tab';
    b.textContent = (i+1) + '. ' + s.t;
    b.addEventListener('click', function(){ showStep(i); });
    stepTabs.appendChild(b);
  });

  function showStep(i){
    curStep = Math.max(0, Math.min(steps.length-1, i));
    var s = steps[curStep];
    stepTitle.textContent = 'Bước ' + (curStep+1) + ' / ' + steps.length + ' — ' + s.t;
    stepDesc.innerHTML = s.d;
    stepNumBg.textContent = String(curStep+1).padStart(2,'0');
    Array.prototype.forEach.call(stepTabs.children, function(el, idx){ el.classList.toggle('active', idx === curStep); });
    stepPrev.disabled = curStep === 0;
    stepNext.disabled = curStep === steps.length-1;
  }
  stepPrev.addEventListener('click', function(){ showStep(curStep-1); });
  stepNext.addEventListener('click', function(){ showStep(curStep+1); });
  showStep(0);

  /* ================= simulator ================= */
  var angleFor = function(basis, bit){ if(basis === '+') return bit === 0 ? 0 : 90; return bit === 0 ? 45 : 135; };
  var randBit = function(){ return Math.random() < 0.5 ? 0 : 1; };
  var randBasis = function(){ return Math.random() < 0.5 ? '+' : 'x'; };
  function measure(sentBasis, sentBit, measureBasis){ if(sentBasis === measureBasis) return sentBit; return randBit(); }

  var rounds = [], keyBits = [], errCount = 0, keptCount = 0;
  var logBody = document.getElementById('logBody');
  var keyBitsEl = document.getElementById('keyBits');
  var qberValueEl = document.getElementById('qberValue');
  var qberFillEl = document.getElementById('qberFill');
  var verdictEl = document.getElementById('verdict');
  var eveToggle = document.getElementById('eveToggle');
  var eveBadge = document.getElementById('eveBadge');
  var aliceNeedle = document.getElementById('aliceNeedle');
  var aliceReadout = document.getElementById('aliceReadout');
  var aliceTag = document.getElementById('aliceTag');
  var bobReadout = document.getElementById('bobReadout');
  var bobTag = document.getElementById('bobTag');
  var ldrFill = document.getElementById('ldrFill');
  var photon = document.getElementById('photon');
  var railSteps = document.querySelectorAll('.rail-step');
  var imgDemo = document.getElementById('imgDemo');

  eveToggle.addEventListener('change', function(){ eveBadge.classList.toggle('on', eveToggle.checked); });
  function setRail(n){ railSteps.forEach(function(el){ el.classList.toggle('on', Number(el.dataset.step) === n); }); }

  function animatePhoton(cb){
    photon.style.transition = 'none';
    photon.setAttribute('cy', 4);
    photon.style.opacity = 1;
    requestAnimationFrame(function(){ photon.style.transition = 'cy .6s linear'; photon.setAttribute('cy', 96); });
    setTimeout(function(){ photon.style.opacity = 0; if(cb) cb(); }, 620);
  }

  function runRound(animated, done){
    var aliceBit = randBit(), aliceBasis = randBasis();
    var angle = angleFor(aliceBasis, aliceBit);
    var txBasis = aliceBasis, txBit = aliceBit, eveUsed = eveToggle.checked;
    if(eveUsed){
      var eveBasis = randBasis();
      var eveBit = measure(aliceBasis, aliceBit, eveBasis);
      txBasis = eveBasis; txBit = eveBit;
    }
    var bobBasis = randBasis();
    var bobBit = measure(txBasis, txBit, bobBasis);
    var kept = aliceBasis === bobBasis;
    var error = kept && aliceBit !== bobBit;

    function finish(){
      rounds.push({aliceBit:aliceBit, aliceBasis:aliceBasis, bobBit:bobBit, bobBasis:bobBasis, kept:kept, error:error});
      if(kept){ keptCount++; keyBits.push(bobBit); if(error) errCount++; }
      renderRound(rounds.length, aliceBit, aliceBasis, bobBit, bobBasis, kept, error);
      renderMetrics();
      if(done) done();
    }

    if(animated){
      setRail(0);
      aliceTag.textContent = 'bit ' + aliceBit + ' / ' + (aliceBasis==='+'?'⊕':'✕');
      aliceReadout.textContent = 'Sinh bit ' + aliceBit + ', basis ' + (aliceBasis==='+'?'⊕ (ngang/dọc)':'✕ (chéo)');
      setTimeout(function(){ setRail(1); aliceNeedle.style.transform = 'rotate(' + angle + 'deg)'; aliceReadout.textContent = 'Servo xoay tới ' + angle + '°'; }, 150);
      setTimeout(function(){ setRail(2); eveBadge.classList.toggle('on', eveUsed); animatePhoton(); }, 700);
      setTimeout(function(){ setRail(3); bobTag.textContent = 'basis ' + (bobBasis==='+'?'⊕':'✕'); ldrFill.setAttribute('width', bobBit === 1 ? 48 : 14); bobReadout.textContent = 'Đo bằng basis ' + (bobBasis==='+'?'⊕':'✕') + ' → đọc bit ' + bobBit; }, 1350);
      setTimeout(function(){ setRail(4); finish(); }, 1750);
      setTimeout(function(){ setRail(5); }, 2100);
    } else {
      finish();
    }
  }

  function renderRound(n, ab, absis, bb, bbasis, kept, error){
    var tr = document.createElement('tr');
    tr.className = error ? 'error' : (kept ? 'kept' : 'discarded');
    tr.innerHTML = '<td>'+n+'</td><td>'+ab+' / '+(absis==='+'?'⊕':'✕')+'</td><td>'+bb+' / '+(bbasis==='+'?'⊕':'✕')+'</td>' +
      '<td>'+(absis===bbasis?'trùng':'khác')+'</td><td>'+(kept ? (error ? 'giữ — LỖI' : 'giữ') : 'loại')+'</td>';
    logBody.appendChild(tr);
    logBody.parentElement.scrollTop = logBody.parentElement.scrollHeight;
  }

  function renderMetrics(){
    keyBitsEl.textContent = keyBits.length ? keyBits.join('') : '—';
    if(keptCount === 0){
      qberValueEl.textContent = '—'; qberFillEl.style.width = '0%';
      verdictEl.className = 'verdict idle'; verdictEl.textContent = 'Chưa đủ dữ liệu — chạy vài vòng để ước lượng QBER.';
      return;
    }
    var qber = errCount / keptCount, pct = (qber*100).toFixed(1);
    qberValueEl.textContent = pct + '%';
    qberFillEl.style.width = Math.min(qber*100, 100) + '%';
    var safe = qber <= 0.11;
    qberFillEl.classList.toggle('bad', !safe);
    verdictEl.className = 'verdict ' + (safe ? 'safe' : 'bad');
    verdictEl.textContent = safe ? 'An toàn — QBER dưới ngưỡng 11%, không phát hiện dấu hiệu nghe lén.' : 'QBER vượt ngưỡng 11% — nghi ngờ có nghe lén, khoá bị huỷ.';
    if(keptCount >= 8){ imgDemo.style.display = 'flex'; runImageDemo(keyBits); }
  }

  document.getElementById('stepBtn').addEventListener('click', function(){ runRound(true); });
  document.getElementById('autoBtn').addEventListener('click', function(){
    var i = 0;
    (function next(){ if(i >= 24) return; runRound(false); i++; setTimeout(next, 15); })();
  });
  document.getElementById('resetBtn').addEventListener('click', function(){
    rounds = []; keyBits = []; errCount = 0; keptCount = 0;
    logBody.innerHTML = ''; renderMetrics(); imgDemo.style.display = 'none'; setRail(-1);
    aliceReadout.textContent = 'Sẵn sàng'; bobReadout.textContent = 'Sẵn sàng';
    aliceTag.textContent = '—'; bobTag.textContent = '—'; eveBadge.classList.remove('on');
  });

  var GRID = 8, CELL = 8;
  var samplePattern = [1,1,1,1,1,1,1,1, 1,0,0,1,1,0,0,1, 1,0,1,1,1,1,0,1, 1,1,1,0,0,1,1,1, 1,1,1,0,0,1,1,1, 1,0,1,1,1,1,0,1, 1,0,0,1,1,0,0,1, 1,1,1,1,1,1,1,1];
  function drawGrid(canvasId, cells){
    var cv = document.getElementById(canvasId); var ctx = cv.getContext('2d');
    for(var y=0;y<GRID;y++){ for(var x=0;x<GRID;x++){ var v = cells[y*GRID+x]; ctx.fillStyle = v ? '#DCE8EA' : '#123A66'; ctx.fillRect(x*CELL, y*CELL, CELL, CELL); } }
  }
  function runImageDemo(bits){
    if(!bits.length) return;
    var enc = samplePattern.map(function(v,i){ return v ^ bits[i % bits.length]; });
    var dec = enc.map(function(v,i){ return v ^ bits[i % bits.length]; });
    drawGrid('imgOrig', samplePattern); drawGrid('imgEnc', enc); drawGrid('imgDec', dec);
  }

  renderMetrics(); setRail(-1);

  /* ================= qber analytical calculator ================= */
  var interceptSlider = document.getElementById('interceptSlider');
  var interceptLabel = document.getElementById('interceptLabel');
  var analyticQberFill = document.getElementById('analyticQberFill');
  var analyticVerdict = document.getElementById('analyticVerdict');
  function updateAnalytic(){
    var pct = Number(interceptSlider.value);
    interceptLabel.textContent = pct + '%';
    var qber = 0.25 * (pct/100);
    analyticQberFill.style.width = Math.min(qber*100,100) + '%';
    var safe = qber <= 0.11;
    analyticQberFill.classList.toggle('bad', !safe);
    analyticVerdict.className = 'verdict ' + (pct===0 ? 'idle' : (safe ? 'safe' : 'bad'));
    analyticVerdict.textContent = pct + '% bị chặn → QBER lý thuyết ' + (qber*100).toFixed(1) + '%' + (pct===0 ? ', an toàn.' : (safe ? ', vẫn dưới ngưỡng.' : ', VƯỢT ngưỡng — bị phát hiện.'));
  }
  interceptSlider.addEventListener('input', updateAnalytic);
  updateAnalytic();

  /* ================= xor degrade demo ================= */
  var xorSample = [];
  for(var i=0;i<64;i++) xorSample.push(samplePattern[i % samplePattern.length]);
  var xorKeyBase = [];
  for(var j=0;j<64;j++) xorKeyBase.push(randBit());
  var wrongBitsSlider = document.getElementById('wrongBitsSlider');
  var wrongBitsLabel = document.getElementById('wrongBitsLabel');
  function updateXorDemo(){
    var n = Number(wrongBitsSlider.value);
    wrongBitsLabel.textContent = n;
    var encKey = xorKeyBase.slice();
    var decKey = xorKeyBase.slice();
    for(var k=0;k<n;k++) decKey[k] = 1 - decKey[k];
    var enc = xorSample.map(function(v,idx){ return v ^ encKey[idx]; });
    var dec = enc.map(function(v,idx){ return v ^ decKey[idx]; });
    drawGrid('xorOrig', xorSample);
    drawGrid('xorResult', dec);
  }
  wrongBitsSlider.addEventListener('input', updateXorDemo);
  updateXorDemo();

})();
