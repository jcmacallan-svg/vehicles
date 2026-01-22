
(function(){
  var DATA = null;

  var state = {
    mode: null, // "class" or "class_name"
    round: [],
    idx: 0,
    streak: 0,
    bestStreak: 0,
    correct: 0,
    lastFeedback: null,
    awaitingNext: false,
    step: "class", // for class_name mode: "class" or "name" or "reveal"
    currentChoices: [],
    lastRoundIds: {}
  };

  function $(id){ return document.getElementById(id); }

  function shuffle(arr){
    for(var i=arr.length-1;i>0;i--){
      var j = Math.floor(Math.random()*(i+1));
      var t = arr[i]; arr[i]=arr[j]; arr[j]=t;
    }
    return arr;
  }

  function sampleUnique(arr, n, avoidMap){
    var pool = [];
    for(var i=0;i<arr.length;i++){
      var it = arr[i];
      if(avoidMap && avoidMap[it.id]) continue;
      pool.push(it);
    }
    shuffle(pool);
    return pool.slice(0, n);
  }

  function pickChoicesCorrectPlusPool(correctValue, poolValues, k){
    // returns array of size k, includes correctValue once, others random unique
    var unique = {};
    unique[correctValue] = true;
    var others = [];
    for(var i=0;i<poolValues.length;i++){
      var v = poolValues[i];
      if(!unique[v]){
        unique[v]=true;
        others.push(v);
      }
    }
    shuffle(others);
    var out = [correctValue];
    for(var j=0;j<others.length && out.length<k;j++){
      out.push(others[j]);
    }
    // if not enough (shouldn't happen), pad with correct (but we try not to)
    while(out.length<k){ out.push(correctValue); }
    return shuffle(out);
  }

  function setSubtitle(){
    var t = (DATA && DATA.title) ? DATA.title : "NL Defence Speaking Trainer";
    document.title = t;
    $(".title"); // noop for lint
    $("subtitle").textContent = "Landmacht \u2022 " + (DATA ? DATA.quizLength : 10) + " questions";
  }

  function updateTop(){
    $("roundPill").textContent = "Round: " + state.idx + "/" + state.round.length;
    $("newRoundBtn").textContent = "New round";
  }

  function resetAll(){
    state.mode = null;
    state.round = [];
    state.idx = 0;
    state.streak = 0;
    state.bestStreak = 0;
    state.correct = 0;
    state.lastFeedback = null;
    state.awaitingNext = false;
    state.step = "class";
    state.currentChoices = [];
    updateTop();
    renderStart();
  }

  function startNewRound(){
    if(!state.mode){
      renderStart();
      return;
    }
    // build new round of quizLength, avoid repeating exact last round if possible
    var all = DATA.questions.slice();
    var avoid = state.lastRoundIds || {};
    var n = DATA.quizLength || 10;

    var picked = sampleUnique(all, n, avoid);
    if(picked.length < n){
      // fallback: allow repeats
      picked = sampleUnique(all, n, null);
    }
    var ids = {};
    for(var i=0;i<picked.length;i++){ ids[picked[i].id]=true; }
    state.lastRoundIds = ids;

    state.round = picked;
    state.idx = 0;
    state.streak = 0;
    state.correct = 0;
    state.lastFeedback = null;
    state.awaitingNext = false;
    state.step = "class";
    updateTop();
    renderQuestion();
  }

  function renderStart(){
    var el = $("screen");
    el.innerHTML = ""
      + "<div class='screen-title'>What do you want to practise today?</div>"
      + "<div class='lead'>Choose one mode. You can change this any time.</div>"
      + "<div class='footer-actions'>"
      + "  <button class='btn' id='modeClass'>Classification only</button>"
      + "  <button class='btn' id='modeClassName'>Classification + naming</button>"
      + "</div>"
      + "<div class='small'>Tip: keep speaking while you choose. Use the prompts under the image.</div>";

    $("modeClass").onclick = function(){
      state.mode = "class";
      startNewRound();
    };
    $("modeClassName").onclick = function(){
      state.mode = "class_name";
      startNewRound();
    };
    updateTop();
  }

  function imgTag(asset){
    var src = "images/" + asset + ".jpg";
    return "<img src='" + src + "' alt='' onerror=\"this.onerror=null;this.src='images/missing.jpg';\" />";
  }

  function renderPrompts(){
    var prompts = (DATA && DATA.speakingPrompts) ? DATA.speakingPrompts : [];
    var html = "<div class='hint'><strong>Speak:</strong><br/>";
    for(var i=0;i<prompts.length;i++){
      html += "• " + escapeHtml(prompts[i]) + "<br/>";
    }
    html += "</div>";
    return html;
  }

  function escapeHtml(s){
    return String(s)
      .replace(/&/g,"&amp;")
      .replace(/</g,"&lt;")
      .replace(/>/g,"&gt;")
      .replace(/\"/g,"&quot;")
      .replace(/\'/g,"&#039;");
  }

  function setFeedback(isGood){
    if(isGood){
      state.streak += 1;
      state.correct += 1;
      if(state.streak > state.bestStreak) state.bestStreak = state.streak;
      state.lastFeedback = { ok:true, text:"Correct. Streak intact ✅" };
    }else{
      state.streak = 0;
      state.lastFeedback = { ok:false, text:"Not correct. Streak reset ✖" };
    }
  }

  function feedbackBox(){
    if(!state.lastFeedback) return "";
    var cls = state.lastFeedback.ok ? "feedback good" : "feedback bad";
    return "<div class='"+cls+"'>" + escapeHtml(state.lastFeedback.text) + "</div>";
  }

  function scoreBadge(){
    return "<div class='badge'>"
      + "<span>✅ <strong>"+state.correct+"</strong></span>"
      + "<span>🔥 Streak <strong>"+state.streak+"</strong> (best "+state.bestStreak+")</span>"
      + "</div>";
  }

  function nextAuto(){
    state.idx += 1;
    updateTop();
    if(state.idx >= state.round.length){
      renderEnd();
    }else{
      state.step = "class";
      state.awaitingNext = false;
      state.currentChoices = [];
      renderQuestion();
    }
  }

  function renderChoices(values, onPick){
    var html = "<div class='grid'>";
    for(var i=0;i<values.length;i++){
      html += "<button class='choice' data-v='"+escapeHtml(values[i])+"'>" + escapeHtml(values[i]) + "</button>";
    }
    html += "</div>";
    // attach after render
    setTimeout(function(){
      var buttons = document.querySelectorAll(".choice");
      for(var j=0;j<buttons.length;j++){
        buttons[j].onclick = function(e){
          var v = this.getAttribute("data-v");
          onPick(v);
        };
      }
    },0);
    return html;
  }

  function renderQuestion(){
    updateTop();
    var q = state.round[state.idx];
    if(!q){ renderEnd(); return; }

    // Build choice pools
    var k = DATA.mcqOptions || 6;

    var el = $("screen");

    // Base layout
    var html = ""
      + "<div class='row'>"
      + "  <div class='media'>" + imgTag(q.asset) + "</div>"
      + "</div>"
      + scoreBadge()
      + renderPrompts();

    if(state.mode === "class"){
      // classification-only
      var classChoices = pickChoicesCorrectPlusPool(q.class, DATA.vehicleClasses, k);
      html += "<div class='hint'><strong>Step:</strong> choose the classification.</div>";
      html += renderChoices(classChoices, function(picked){
        // lock by ignoring if just clicked rapidly
        setFeedback(picked === q.class);
        el.innerHTML = html + feedbackBox(); // show feedback instantly
        updateTop();
        setTimeout(function(){ nextAuto(); }, 650);
      });
      el.innerHTML = html;
      return;
    }

    // class + name mode
    if(state.step === "class"){
      var classChoices2 = pickChoicesCorrectPlusPool(q.class, DATA.vehicleClasses, k);
      html += "<div class='hint'><strong>Step 1:</strong> choose the classification.</div>";
      html += renderChoices(classChoices2, function(pickedClass){
        setFeedback(pickedClass === q.class);
        state.step = "name";
        el.innerHTML = ""; // rerender for step 2 with feedback kept
        renderQuestion();
      });
      html += feedbackBox();
      el.innerHTML = html;
      return;
    }

    if(state.step === "name"){
      // build name pool from questions
      var allNames = [];
      for(var i=0;i<DATA.questions.length;i++){ allNames.push(DATA.questions[i].answer); }
      var nameChoices = pickChoicesCorrectPlusPool(q.answer, allNames, k);
      html += "<div class='hint'><strong>Step 2:</strong> choose the platform name.</div>";
      html += renderChoices(nameChoices, function(pickedName){
        setFeedback(pickedName === q.answer);
        state.step = "reveal";
        state.awaitingNext = true;
        el.innerHTML = ""; // rerender reveal
        renderQuestion();
      });
      html += feedbackBox();
      el.innerHTML = html;
      return;
    }

    // reveal step: show correct answer + Next
    html += "<div class='reveal'><strong>Correct answer</strong>"
      + "<div class='kv'>"
      + "<span class='tag'>Class: " + escapeHtml(q.class) + "</span>"
      + "<span class='tag'>Name: " + escapeHtml(q.answer) + "</span>"
      + "</div></div>"
      + feedbackBox()
      + "<div class='footer-actions'>"
      + "  <button class='btn' id='nextBtn'>Next</button>"
      + "</div>";
    el.innerHTML = html;

    $("nextBtn").onclick = function(){
      nextAuto();
    };
  }

  function renderEnd(){
    var el = $("screen");
    el.innerHTML = ""
      + "<div class='screen-title'>Round finished</div>"
      + "<div class='lead'>You can start a new round or change practice mode.</div>"
      + "<div class='badge'>"
      + "  <span>✅ Correct <strong>"+state.correct+"</strong> / "+state.round.length+"</span>"
      + "  <span>🔥 Best streak <strong>"+state.bestStreak+"</strong></span>"
      + "</div>"
      + "<div class='small' style='margin-top:10px'>Answers are not shown here to avoid spoilers.</div>"
      + "<div class='footer-actions'>"
      + "  <button class='btn' id='endNewRound'>New round</button>"
      + "  <button class='btn ghost' id='endChange'>Change practice</button>"
      + "</div>";
    $("endNewRound").onclick = function(){ startNewRound(); };
    $("endChange").onclick = function(){ state.mode=null; renderStart(); };
    updateTop();
  }

  function init(){
    fetch("data.json").then(function(r){ return r.json(); }).then(function(d){
      DATA = d;
      setSubtitle();
      // wire buttons
      $("resetBtn").onclick = function(){ resetAll(); };
      $("newRoundBtn").onclick = function(){ startNewRound(); };
      $("changePracticeBtn").onclick = function(){ state.mode=null; renderStart(); };
      renderStart();
    }).catch(function(err){
      $("screen").innerHTML = "<div class='screen-title'>Error</div><div class='lead'>Could not load data.json.</div><pre class='small'>"+escapeHtml(String(err))+"</pre>";
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
