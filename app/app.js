(function(){
  var DATA = null;
  var state = { mode:null, round:[], idx:0, streak:0, bestStreak:0, correct:0, lastFeedback:null, step:"class", lastRoundIds:{}, attempts:[] };
  function $(id){ return document.getElementById(id); }
  function escapeHtml(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\"/g,"&quot;").replace(/\'/g,"&#039;"); }
  function shuffle(arr){ for(var i=arr.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=arr[i]; arr[i]=arr[j]; arr[j]=t; } return arr; }
  function sampleUnique(arr,n,avoid){ var pool=[]; for(var i=0;i<arr.length;i++){ var it=arr[i]; if(avoid && avoid[it.id]) continue; pool.push(it);} shuffle(pool); return pool.slice(0,n); }
  function pickChoicesCorrectPlusPool(correct,pool,k){ var uniq={}; uniq[correct]=true; var others=[]; for(var i=0;i<pool.length;i++){ var v=pool[i]; if(!uniq[v]){ uniq[v]=true; others.push(v);} } shuffle(others); var out=[correct]; for(var j=0;j<others.length && out.length<k;j++) out.push(others[j]); while(out.length<k) out.push(correct); return shuffle(out); }
  function setSubtitle(){ var t=(DATA&&DATA.title)?DATA.title:"NL Defence Speaking Trainer"; document.title=t; $("subtitle").textContent="Landmacht • "+(DATA?DATA.quizLength:10)+" questions"; }
  function updateTop(){ $("roundPill").textContent="Round: "+state.idx+"/"+state.round.length; }
  function resetAll(){ state.mode=null; state.round=[]; state.idx=0; state.streak=0; state.bestStreak=0; state.correct=0; state.lastFeedback=null; state.step="class"; state.attempts=[]; updateTop(); renderStart(); }
  function startNewRound(){ if(!state.mode){ renderStart(); return; } var all=DATA.questions.slice(); var avoid=state.lastRoundIds||{}; var n=DATA.quizLength||10; var picked=sampleUnique(all,n,avoid); if(picked.length<n) picked=sampleUnique(all,n,null); var ids={}; for(var i=0;i<picked.length;i++) ids[picked[i].id]=true; state.lastRoundIds=ids; state.round=picked; state.idx=0; state.streak=0; state.correct=0; state.lastFeedback=null; state.step="class"; state.attempts=[]; updateTop(); renderQuestion(); }
  function renderStart(){ var el=$("screen"); el.innerHTML="<div class='screen-title'>What do you want to practise today?</div><div class='lead'>Choose one mode. You can change this any time.</div><div class='footer-actions'><button class='btn' id='modeClass'>Classification only</button><button class='btn' id='modeClassName'>Classification + naming</button></div><div class='small'>Tip: keep speaking while you choose. Use the prompts under the image.</div>"; $("modeClass").onclick=function(){ state.mode='class'; startNewRound(); }; $("modeClassName").onclick=function(){ state.mode='class_name'; startNewRound(); }; updateTop(); }
  function imgTag(asset){ var src="images/"+asset+".jpg"; return "<img src='"+src+"' alt='' onerror=\"this.onerror=null;this.src='images/missing.jpg';\" />"; }
  function renderPrompts(){ var prompts=(DATA&&DATA.speakingPrompts)?DATA.speakingPrompts:[]; var html="<div class='hint'><strong>Speak:</strong><br/>"; for(var i=0;i<prompts.length;i++) html+="• "+escapeHtml(prompts[i])+"<br/>"; html+="</div>"; return html; }
  function setFeedback(ok){ if(ok){ state.streak+=1; state.correct+=1; if(state.streak>state.bestStreak) state.bestStreak=state.streak; state.lastFeedback={ok:true,text:"Correct. Streak intact ✅"}; } else { state.streak=0; state.lastFeedback={ok:false,text:"Not correct. Streak reset ✖"}; } }
  function feedbackBox(){ if(!state.lastFeedback) return ""; return "<div class='feedback "+(state.lastFeedback.ok?"good":"bad")+"'>"+escapeHtml(state.lastFeedback.text)+"</div>"; }
  function scoreBadge(){ return "<div class='badge'><span>✅ <strong>"+state.correct+"</strong></span><span>🔥 Streak <strong>"+state.streak+"</strong> (best "+state.bestStreak+")</span></div>"; }
  function renderChoices(values,onPick){ var html="<div class='grid'>"; for(var i=0;i<values.length;i++) html+="<button class='choice' data-v='"+escapeHtml(values[i])+"'>"+escapeHtml(values[i])+"</button>"; html+="</div>"; setTimeout(function(){ var buttons=document.querySelectorAll(".choice"); for(var j=0;j<buttons.length;j++){ buttons[j].onclick=function(){ onPick(this.getAttribute("data-v"), this); }; } },0); return html; }
  function markChoiceButtons(correct,picked){ var buttons=document.querySelectorAll(".choice"); for(var i=0;i<buttons.length;i++){ var v=buttons[i].getAttribute("data-v"); if(v===correct) buttons[i].className="choice correct"; else if(v===picked) buttons[i].className="choice wrong"; else buttons[i].disabled=true; } }
  function nextAuto(){ state.idx+=1; updateTop(); if(state.idx>=state.round.length) renderEnd(); else { state.step="class"; renderQuestion(); } }
  function renderQuestion(){ updateTop(); var q=state.round[state.idx]; if(!q){ renderEnd(); return; } var k=DATA.mcqOptions||6; var el=$("screen"); var html="<div class='row'><div class='media'>"+imgTag(q.asset)+"</div></div>"+scoreBadge()+renderPrompts();
    if(state.mode==="class"){ var classChoices=pickChoicesCorrectPlusPool(q["class"], DATA.vehicleClasses, k); html+="<div class='hint'><strong>Step:</strong> choose the classification.</div>"; html+=renderChoices(classChoices,function(picked){ var ok=(picked===q["class"]); setFeedback(ok); state.attempts.push({id:q.id,asset:q.asset,correctClass:q["class"],correctName:q.answer,pickedClass:picked,pickedName:null,okClass:ok,okName:null}); markChoiceButtons(q["class"], picked); el.insertAdjacentHTML("beforeend", feedbackBox()); setTimeout(function(){ nextAuto(); },650); }); el.innerHTML=html; return; }
    if(state.step==="class"){ var classChoices2=pickChoicesCorrectPlusPool(q["class"], DATA.vehicleClasses, k); html+="<div class='hint'><strong>Step 1:</strong> choose the classification.</div>"; html+=renderChoices(classChoices2,function(picked){ var ok=(picked===q["class"]); setFeedback(ok); state.attempts.push({id:q.id,asset:q.asset,correctClass:q["class"],correctName:q.answer,pickedClass:picked,pickedName:null,okClass:ok,okName:null}); state.step="name"; markChoiceButtons(q["class"], picked); el.insertAdjacentHTML("beforeend", feedbackBox()); setTimeout(function(){ renderQuestion(); },450); }); el.innerHTML=html; return; }
    if(state.step==="name"){ var allNames=[]; for(var i=0;i<DATA.questions.length;i++) allNames.push(DATA.questions[i].answer); var nameChoices=pickChoicesCorrectPlusPool(q.answer, allNames, k); html+="<div class='hint'><strong>Step 2:</strong> choose the platform name.</div>"; html+=renderChoices(nameChoices,function(picked){ var ok=(picked===q.answer); setFeedback(ok); var last=state.attempts[state.attempts.length-1]; if(last && last.id===q.id){ last.pickedName=picked; last.okName=ok; } markChoiceButtons(q.answer, picked); state.step="reveal"; el.insertAdjacentHTML("beforeend", feedbackBox()); setTimeout(function(){ renderQuestion(); },450); }); el.innerHTML=html; return; }
    html+="<div class='reveal'><strong>Correct answer</strong><div class='kv'><span class='tag'>Class: "+escapeHtml(q["class"])+"</span><span class='tag'>Name: "+escapeHtml(q.answer)+"</span></div></div><div class='footer-actions'><button class='btn' id='nextBtn'>Next</button></div>";
    el.innerHTML=html; $("nextBtn").onclick=function(){ nextAuto(); };
  }
  function getTeacherPin(){ var p=localStorage.getItem("teacherPin"); if(!p){ p="1357"; localStorage.setItem("teacherPin", p); } return p; }
  function openTeacherModal(){ $("teacherModal").style.display="flex"; }
  function closeTeacherModal(){ $("teacherModal").style.display="none"; $("teacherModalBody").innerHTML=""; }

  function openTheoryModal(){ $("theoryModal").style.display="flex"; renderTheoryContent(); }
  function closeTheoryModal(){ $("theoryModal").style.display="none"; }
  function renderTheoryContent(){
    if(!DATA) return;
    var desc = {
      "Battle Tank (BT)": "Heavily armoured tracked combat vehicle with a large-calibre main gun.",
      "Armoured Infantry Fighting Vehicle (AIFV)": "Carries infantry and can fight: cannon/AT weapons, tracked or wheeled.",
      "Armoured Patrol Vehicle (AP)": "Light armoured patrol / security vehicle, usually wheeled.",
      "Armoured Personnel Carrier (APC)": "Protected troop transport; weapon is usually lighter than an AIFV.",
      "Heavy Armament Combat Vehicle (HACV)": "Heavily armed combat vehicle that is not a tank (e.g., heavy gun/missile platform).",
      "(Armoured) Engineer Vehicle ((A)EV)": "Engineer support: breaching, earthmoving, route clearance, CBRN, etc.",
      "(Armoured) Vehicle Laying Bridge ((A)VLB)": "Bridge-layer vehicle to create crossings quickly.",
      "(Armoured) Recovery Vehicle ((A)RV)": "Recovery/repair/towing vehicle for damaged armour.",
      "Artillery (Art)": "Indirect fire systems (howitzers, rocket artillery).",
      "Air Defence (AD)": "Air defence systems (SHORAD/SAM) to protect against aircraft/helos/UAS.",
      "Reconnaissance Vehicle (RV)": "Recon/scout platform for observation and target acquisition.",
      "Armoured Cars (AC)": "Other (often wheeled) vehicles in the set: cars/trucks/support platforms."
    };
    var html = "<div class='lead'>Quick refresher of the 12 categories used in this trainer:</div>";
    html += "<div class='theory-grid'>";
    for(var i=0;i<DATA.vehicleClasses.length;i++){
      var k = DATA.vehicleClasses[i];
      html += "<div class='theory-card'><div class='theory-k'>"+escapeHtml(k)+"</div><div class='small'>"+escapeHtml(desc[k]||"")+"</div></div>";
    }
    html += "</div>";
    html += "<div class='small' style='margin-top:10px'>Teaching tip: ask students to say <em>why</em> (tracks/wheels, turret, weapon size, role) before clicking.</div>";
    $("theoryContent").innerHTML = html;
  }

  function teacherModalLocked(){ return "<div class='field'><input class='input' id='pinInput' type='password' placeholder='Teacher PIN' /><button class='btn' id='unlockBtn' type='button'>Unlock</button></div><div class='small'>Default PIN: <strong>1357</strong> (change it after unlocking).</div>"; }
  function teacherModalUnlocked(){ var html="<div class='field'><span class='small'>PIN unlocked.</span><input class='input' id='newPin' type='text' placeholder='Set new PIN' /><button class='btn' id='setPinBtn' type='button'>Update PIN</button></div>"; html+="<table class='table'><thead><tr><th>#</th><th>Asset</th><th>Correct class</th><th>Student class</th><th>Correct name</th><th>Student name</th><th>OK</th></tr></thead><tbody>";
    for(var i=0;i<state.attempts.length;i++){ var a=state.attempts[i]; var okOverall=(state.mode==='class')?a.okClass:(a.okClass && a.okName); html+="<tr><td>"+(i+1)+"</td><td>"+escapeHtml(a.asset)+"</td><td>"+escapeHtml(a.correctClass)+"</td><td>"+escapeHtml(a.pickedClass||"")+"</td><td>"+escapeHtml(a.correctName)+"</td><td>"+escapeHtml(a.pickedName||"")+"</td><td class='"+(okOverall?"ok":"no")+"'>"+(okOverall?"✓":"✖")+"</td></tr>"; }
    html+="</tbody></table>"; return html; }
  function showTeacherModal(){ openTeacherModal(); $("teacherModalBody").innerHTML=teacherModalLocked(); $("unlockBtn").onclick=function(){ var v=$("pinInput").value; if(v===getTeacherPin()){ $("teacherModalBody").innerHTML=teacherModalUnlocked(); $("setPinBtn").onclick=function(){ var nv=$("newPin").value; if(nv && nv.length>=4){ localStorage.setItem("teacherPin", nv); $("newPin").value=""; $("newPin").placeholder="PIN updated ✓"; } else { $("newPin").value=""; $("newPin").placeholder="Use 4+ digits"; } }; } else { $("pinInput").value=""; $("pinInput").placeholder="Wrong PIN"; } }; }
  function renderEnd(){ var el=$("screen"); el.innerHTML="<div class='screen-title'>Round finished</div><div class='lead'>Totals only. Detailed answers are hidden (teacher-only).</div><div class='badge'><span>✅ Correct <strong>"+state.correct+"</strong> / "+state.round.length+"</span><span>🔥 Best streak <strong>"+state.bestStreak+"</strong></span></div><div class='footer-actions'><button class='btn' id='endNewRound'>New round</button><button class='btn ghost' id='endChange'>Change practice</button><button class='btn' id='teacherBtn'>Teacher results</button></div><div class='small' style='margin-top:10px'>Tip: set your own PIN in Teacher results.</div>";
    $("endNewRound").onclick=function(){ startNewRound(); }; $("endChange").onclick=function(){ state.mode=null; renderStart(); }; $("teacherBtn").onclick=function(){ showTeacherModal(); }; updateTop(); }
  function init(){ fetch("data.json").then(function(r){ return r.json(); }).then(function(d){ DATA=d; setSubtitle(); $("resetBtn").onclick=function(){ resetAll(); }; $("newRoundBtn").onclick=function(){ startNewRound(); }; $("changePracticeBtn").onclick=function(){ state.mode=null; renderStart(); };
          var tb=$("theoryBtn"); if(tb){ tb.onclick=function(){ openTheoryModal(); }; }
          var ctb=$("closeTheoryBtn"); if(ctb){ ctb.onclick=function(){ closeTheoryModal(); }; }
          var tm=$("theoryModal"); if(tm){ tm.addEventListener("click", function(e){ if(e.target && e.target.id==="theoryModal") closeTheoryModal(); }); } $("closeTeacherModal").onclick=function(){ closeTeacherModal(); }; $("teacherModal").addEventListener("click", function(e){ if(e.target && e.target.id==="teacherModal") closeTeacherModal(); }); renderStart(); updateTop(); }).catch(function(err){ $("screen").innerHTML="<div class='screen-title'>Error</div><div class='lead'>Could not load data.json.</div><pre class='small'>"+escapeHtml(String(err))+"</pre>"; }); }
  document.addEventListener("DOMContentLoaded", init);
})();